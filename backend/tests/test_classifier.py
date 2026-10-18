from app.compiler.error_parser import ParsedCompilerError
from app.classifiers.error_classifier import ErrorClassifier

classifier = ErrorClassifier()


def test_classify_semicolon():
    err = ParsedCompilerError(
        file="Main.java",
        line=4,
        severity="error",
        message="';' expected",
        compiler_code="SEMICOLON_EXPECTED"
    )
    result = classifier.classify(err)
    assert result.category == "SYNTAX_ERROR"
    assert result.subcategory == "MISSING_SEMICOLON"
    assert result.confidence >= 0.95


def test_classify_incompatible_types():
    err = ParsedCompilerError(
        file="Main.java",
        line=3,
        severity="error",
        message="incompatible types: java.lang.String cannot be converted to int",
        compiler_code="INCOMPATIBLE_TYPES"
    )
    result = classifier.classify(err)
    assert result.category == "TYPE_ERROR"
    assert result.subcategory == "TYPE_MISMATCH"
    assert result.confidence >= 0.95


def test_classify_undefined_variable():
    err = ParsedCompilerError(
        file="Main.java",
        line=3,
        severity="error",
        message="cannot find symbol",
        compiler_code="CANNOT_FIND_SYMBOL",
        symbol="variable value",
        location="class Main"
    )
    result = classifier.classify(err)
    assert result.category == "VARIABLE_ERROR"
    assert result.subcategory == "UNDEFINED_VARIABLE"
    assert result.confidence >= 0.95


def test_classify_undefined_method():
    err = ParsedCompilerError(
        file="Main.java",
        line=5,
        severity="error",
        message="cannot find symbol",
        compiler_code="CANNOT_FIND_SYMBOL",
        symbol="method calculateTotal(int)",
        location="class Main"
    )
    result = classifier.classify(err)
    assert result.category == "METHOD_ERROR"
    assert result.subcategory == "UNDEFINED_METHOD"


def test_classify_division_by_zero():
    err = ParsedCompilerError(
        file="Main.java",
        line=3,
        severity="error",
        message="[divzero] division by zero",
        compiler_code="DIVISION_BY_ZERO"
    )
    result = classifier.classify(err)
    assert result.category == "ARITHMETIC_ERROR"
    assert result.subcategory == "DIVISION_BY_ZERO"
    assert result.severity == "ERROR"
    assert result.confidence >= 0.95

