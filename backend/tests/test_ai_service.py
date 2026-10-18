from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ClassificationResult
from app.ai.ai_service import AIExplanationService

service = AIExplanationService(api_key=None)  # Explicitly test KB fallback


def test_ai_fallback_to_kb():
    code = """public class Main {
    public static void main(String[] args) {
        int age = "20";
    }
}"""
    err = ParsedCompilerError(
        file="Main.java",
        line=3,
        severity="error",
        message="incompatible types: java.lang.String cannot be converted to int",
        compiler_code="INCOMPATIBLE_TYPES"
    )
    classification = ClassificationResult(
        category="TYPE_ERROR",
        subcategory="TYPE_MISMATCH",
        severity="ERROR",
        confidence=0.98,
        description="Type mismatch"
    )

    explanation = service.explain(code, err, classification)
    assert explanation.title == "Type Mismatch"
    assert "int" in explanation.what_happened.lower()
    assert explanation.ai_generated is False
    assert explanation.problematic_code == 'int age = "20";'
    assert len(explanation.prevention_tip) > 0
