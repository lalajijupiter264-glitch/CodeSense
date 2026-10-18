from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ClassificationResult
from app.ai.ai_service import AIExplanationResponse
from app.analyzers.static_analyzer import StaticWarning


class AnalyzeRequest(BaseModel):
    """Source code submission for full compilation and educational diagnostic analysis."""
    language: str = Field(default="java", description="Target programming language (currently: java)")
    source_code: str = Field(..., description="Java source code to compile and analyze", min_length=1)
    user_id: Optional[str] = Field(default="guest", description="Unique user or session identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "language": "java",
                    "source_code": "public class Main {\n    public static void main(String[] args) {\n        int age = \"twenty\";\n        System.out.println(age);\n    }\n}",
                    "user_id": "student-123"
                }
            ]
        }
    )


class CompileRequest(BaseModel):
    """Source code submission for raw compiler execution only without AI/KB explanations."""
    language: str = Field(default="java", description="Target programming language")
    source_code: str = Field(..., description="Java source code to compile", min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "language": "java",
                    "source_code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World\");\n    }\n}"
                }
            ]
        }
    )


class ErrorDetail(BaseModel):
    """Detailed error object linking raw compiler parser, taxonomy classifier, and validated fix."""
    error: ParsedCompilerError
    classification: ClassificationResult
    explanation: Optional[AIExplanationResponse] = None


class AnalysisResponse(BaseModel):
    """Complete response returned by POST /api/analyze."""
    submission_id: str = Field(..., description="Unique UUID for this analysis submission")
    language: str = Field(default="java", description="Programming language analyzed")
    success: bool = Field(..., description="True if program compiled cleanly with zero errors")
    exit_code: int = Field(..., description="Process exit code from javac (0 = success)")
    compilation_time_ms: float = Field(..., description="Time taken by javac compiler in milliseconds")
    raw_output: str = Field(..., description="Raw stderr or stdout stream from javac")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of parsed and classified compiler diagnostics")
    warnings: List[StaticWarning] = Field(default_factory=list, description="Code quality recommendations from static analyzer")
    primary_error: Optional[ErrorDetail] = Field(default=None, description="The primary blocking diagnostic requiring immediate attention")
    summary_message: str = Field(..., description="High-level human readable compilation status summary")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "submission_id": "7f13b2c1-d45e-4a67-b89c-0123456789ab",
                    "language": "java",
                    "success": False,
                    "exit_code": 1,
                    "compilation_time_ms": 412.5,
                    "raw_output": "Main.java:3: error: incompatible types: String cannot be converted to int\n        int age = \"twenty\";\n                  ^\n1 error\n",
                    "errors": [
                        {
                            "error": {
                                "id": "Main.java:3:19",
                                "file": "Main.java",
                                "line": 3,
                                "column": 19,
                                "severity": "error",
                                "message": "incompatible types: String cannot be converted to int",
                                "compiler_code": "INCOMPATIBLE_TYPES",
                                "code_snippet": "        int age = \"twenty\";",
                                "is_primary": True
                            },
                            "classification": {
                                "category": "TYPE_ERROR",
                                "subcategory": "INCOMPATIBLE_TYPES",
                                "severity": "HIGH",
                                "confidence": 0.98,
                                "description": "Type conversion error"
                            },
                            "explanation": {
                                "title": "Type Mismatch",
                                "what_happened": "You attempted to store text (a String) inside an integer variable.",
                                "why_it_happened": "Java is statically typed and prevents putting String values into int variables.",
                                "problematic_code": "int age = \"twenty\";",
                                "suggested_fix": "Change the value to an integer literal, e.g. 20, or change the variable type to String.",
                                "corrected_code": "public class Main {\n    public static void main(String[] args) {\n        int age = 20;\n        System.out.println(age);\n    }\n}",
                                "prevention_tip": "Remember that quotes define a String; omit quotes for numeric types.",
                                "concept_to_learn": "Primitive Types & Type System",
                                "difficulty": "beginner",
                                "ai_generated": False,
                                "fix_available": True,
                                "fix_confidence": 0.98,
                                "original_code": "public class Main {\n    public static void main(String[] args) {\n        int age = \"twenty\";\n        System.out.println(age);\n    }\n}",
                                "changed_lines": [3],
                                "fix_explanation": "Change value to integer literal",
                                "validated": True
                            }
                        }
                    ],
                    "warnings": [],
                    "primary_error": None,
                    "summary_message": "Compilation failed with 1 compiler error."
                }
            ]
        }
    )


class ExplainRequest(BaseModel):
    """Request to explain a specific error on demand."""
    language: str = Field(default="java", description="Target language")
    source_code: str = Field(..., description="Original source code context")
    error: ParsedCompilerError = Field(..., description="Parsed compiler diagnostic token")
    classification: Optional[ClassificationResult] = Field(default=None, description="Optional classification override")
