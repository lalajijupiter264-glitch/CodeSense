import json
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ClassificationResult
from app.utils.logger import logger


class KnowledgeBaseEntry(BaseModel):
    """Knowledge base article for a compiler error."""
    code: str
    category: str
    title: str
    beginner_explanation: str
    why_it_happened: str
    common_causes: list[str] = Field(default_factory=list)
    example_broken: Optional[str] = None
    example_fixed: Optional[str] = None
    suggested_fix: str
    prevention_advice: str
    related_concepts: list[str] = Field(default_factory=list)


class ErrorKnowledgeBase:
    """Service for retrieving educational explanations and prevention guides."""

    def __init__(self, json_path: Optional[str] = None):
        if json_path is None:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(dir_path, "java_errors.json")
        self.json_path = json_path
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load error definitions from JSON."""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
                logger.info(f"Loaded {len(self._entries)} error definitions from {self.json_path}")
            else:
                logger.warning(f"Knowledge base file not found at {self.json_path}")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")

    def lookup(
        self,
        error: ParsedCompilerError,
        classification: Optional[ClassificationResult] = None
    ) -> KnowledgeBaseEntry:
        """Find the most accurate knowledge base entry for an error."""
        # 1. Check direct compiler code or subcategory
        candidates = [
            error.compiler_code,
        ]

        # If it's cannot find symbol, check variable or method
        if error.compiler_code == "CANNOT_FIND_SYMBOL":
            if error.symbol and "variable" in error.symbol.lower():
                candidates.insert(0, "CANNOT_FIND_SYMBOL_VARIABLE")
            elif error.symbol and "method" in error.symbol.lower():
                candidates.insert(0, "CANNOT_FIND_SYMBOL_METHOD")
            elif error.symbol and "class" in error.symbol.lower():
                candidates.insert(0, "CANNOT_FIND_SYMBOL_CLASS")

        if classification:
            candidates.append(classification.subcategory)
            candidates.append(classification.category)

        for candidate in candidates:
            if candidate and candidate in self._entries:
                data = self._entries[candidate]
                return KnowledgeBaseEntry(**data)

        # 2. Heuristic fallback based on category
        cat = classification.category if classification else "SYNTAX_ERROR"
        return KnowledgeBaseEntry(
            code=error.compiler_code,
            category=cat,
            title=f"Java Compiler Diagnostic ({error.compiler_code.replace('_', ' ').title()})",
            beginner_explanation=f"The Java compiler detected an issue on line {error.line}: {error.message}",
            why_it_happened=f"Java rejected this code because: {error.message}. Review syntax, types, and declarations around line {error.line}.",
            common_causes=["Typo or syntax error", "Type incompatibility", "Missing declaration or import"],
            example_broken=error.code_snippet,
            example_fixed=None,
            suggested_fix=f"Review and correct line {error.line} according to Java specifications.",
            prevention_advice="Compile frequently after writing small sections of code to catch mistakes early.",
            related_concepts=["Java Syntax", "Compiler Diagnostics"]
        )
