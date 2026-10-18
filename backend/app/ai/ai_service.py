import json
import re
from typing import Optional, List
import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ClassificationResult
from app.knowledge.error_kb import ErrorKnowledgeBase, KnowledgeBaseEntry
from app.compiler.fix_engine import JavaFixEngine, FixResult
from app.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.utils.logger import logger


class AIExplanationResponse(BaseModel):
    """Strict structured explanation response schema."""
    title: str
    what_happened: str
    why_it_happened: str
    problematic_code: str
    suggested_fix: str
    corrected_code: Optional[str] = None
    prevention_tip: str
    concept_to_learn: Optional[str] = "Java Fundamentals"
    difficulty: str = "beginner"
    ai_generated: bool = False
    fix_available: bool = False
    fix_confidence: float = 0.0
    original_code: Optional[str] = None
    changed_lines: List[int] = Field(default_factory=list)
    fix_explanation: Optional[str] = None
    validated: bool = False


class AIExplanationService:
    """Service providing intelligent educational explanations with KB fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        kb: Optional[ErrorKnowledgeBase] = None,
        fix_engine: Optional[JavaFixEngine] = None
    ):
        self.api_key = api_key or settings.effective_ai_key
        self.model = model or settings.ai_model
        self.kb = kb or ErrorKnowledgeBase()
        self.fix_engine = fix_engine or JavaFixEngine()

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code fences and extraneous text from LLM response."""
        text = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if fence_match:
            return fence_match.group(1).strip()
        # Look for first { and last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            return text[first_brace:last_brace + 1].strip()
        return text

    def _fallback_to_kb(
        self,
        error: ParsedCompilerError,
        classification: ClassificationResult,
        source_code: str
    ) -> AIExplanationResponse:
        """Construct a high-quality explanation from the deterministic knowledge base and validated fix engine."""
        entry: KnowledgeBaseEntry = self.kb.lookup(error, classification)

        # Extract problematic line if available
        lines = source_code.splitlines()
        prob_code = lines[error.line - 1].strip() if 0 < error.line <= len(lines) else error.message

        # Deterministically generate and validate fix from the actual user code
        fix_res: FixResult = self.fix_engine.fix_and_validate(source_code, [error])

        return AIExplanationResponse(
            title=entry.title,
            what_happened=entry.beginner_explanation,
            why_it_happened=entry.why_it_happened,
            problematic_code=prob_code,
            suggested_fix=entry.suggested_fix,
            corrected_code=fix_res.corrected_code if fix_res.fix_available and fix_res.validated else None,
            prevention_tip=entry.prevention_advice,
            concept_to_learn=entry.related_concepts[0] if entry.related_concepts else "Java Syntax",
            difficulty="beginner",
            ai_generated=False,
            fix_available=fix_res.fix_available and fix_res.validated,
            fix_confidence=fix_res.fix_confidence,
            original_code=source_code,
            changed_lines=fix_res.changed_lines,
            fix_explanation=fix_res.fix_explanation,
            validated=fix_res.validated
        )

    def explain(
        self,
        source_code: str,
        error: ParsedCompilerError,
        classification: ClassificationResult,
        language: str = "Java"
    ) -> AIExplanationResponse:
        """
        Generate educational explanation for a compiler error.
        Uses LLM when API key is set; automatically falls back to Knowledge Base.
        """
        if not self.api_key:
            logger.info("No AI API key configured; using deterministic Knowledge Base.")
            return self._fallback_to_kb(error, classification, source_code)

        lines = source_code.splitlines()
        code_snippet = error.code_snippet or (
            lines[error.line - 1] if 0 < error.line <= len(lines) else error.message
        )

        user_content = USER_PROMPT_TEMPLATE.format(
            language=language,
            file=error.file,
            line=error.line,
            message=error.message,
            category=classification.category,
            subcategory=classification.subcategory,
            code_snippet=code_snippet,
            source_code=source_code
        )

        try:
            logger.info(f"Invoking AI explanation engine for line {error.line}: {error.compiler_code}")

            # Check if Gemini model or OpenAI model
            if "gemini" in self.model.lower():
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_content}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                # OpenAI-compatible Chat Completions format
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    raw_text = data["choices"][0]["message"]["content"]

            cleaned_json = self._clean_json_text(raw_text)
            parsed_data = json.loads(cleaned_json)
            parsed_data["ai_generated"] = True

            # MANDATORY COMPILER VALIDATION: Test proposed fix against javac
            proposed_fix = parsed_data.get("corrected_code")
            is_valid_compile = False
            if proposed_fix and proposed_fix.strip():
                comp_check = self.fix_engine.compiler.compile(proposed_fix)
                if comp_check.success and not self.fix_engine.parser.parse(comp_check.stderr):
                    is_valid_compile = True

            if is_valid_compile:
                parsed_data["fix_available"] = True
                parsed_data["validated"] = True
                parsed_data["fix_confidence"] = 0.95
                parsed_data["original_code"] = source_code
                parsed_data["fix_explanation"] = parsed_data.get("suggested_fix") or "AI correction validated by compiler."
            else:
                # LLM fix did not compile cleanly; fallback to deterministic fix engine
                det_fix = self.fix_engine.fix_and_validate(source_code, [error])
                parsed_data["corrected_code"] = det_fix.corrected_code if det_fix.fix_available and det_fix.validated else None
                parsed_data["fix_available"] = det_fix.fix_available and det_fix.validated
                parsed_data["fix_confidence"] = det_fix.fix_confidence
                parsed_data["original_code"] = source_code
                parsed_data["changed_lines"] = det_fix.changed_lines
                parsed_data["fix_explanation"] = det_fix.fix_explanation
                parsed_data["validated"] = det_fix.validated

            validated = AIExplanationResponse(**parsed_data)
            logger.info("AI explanation successfully generated and validated.")
            return validated

        except Exception as e:
            logger.warning(f"AI explanation call failed or timed out ({e}). Falling back to Knowledge Base.")
            return self._fallback_to_kb(error, classification, source_code)
