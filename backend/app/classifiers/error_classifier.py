import re
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.compiler.error_parser import ParsedCompilerError


class ClassificationResult(BaseModel):
    """Result of categorizing a compiler error."""
    category: str
    subcategory: str
    severity: str
    confidence: float
    description: str


class ErrorClassifier:
    """Deterministic taxonomy classifier for Java compiler errors."""

    # Category taxonomy constants
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TYPE_ERROR = "TYPE_ERROR"
    VARIABLE_ERROR = "VARIABLE_ERROR"
    METHOD_ERROR = "METHOD_ERROR"
    CLASS_ERROR = "CLASS_ERROR"
    ACCESS_ERROR = "ACCESS_ERROR"
    ARITHMETIC_ERROR = "ARITHMETIC_ERROR"
    CODE_QUALITY = "CODE_QUALITY"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    # Deterministic mapping based on compiler codes
    CODE_MAP: Dict[str, Dict[str, Any]] = {
        "DIVISION_BY_ZERO": {
            "category": ARITHMETIC_ERROR,
            "subcategory": "DIVISION_BY_ZERO",
            "confidence": 0.99,
            "description": "Attempted to divide by zero in an arithmetic expression."
        },
        "SEMICOLON_EXPECTED": {
            "category": SYNTAX_ERROR,
            "subcategory": "MISSING_SEMICOLON",
            "confidence": 0.99,
            "description": "A semicolon ';' was omitted at the end of a statement."
        },
        "PARENTHESIS_EXPECTED": {
            "category": SYNTAX_ERROR,
            "subcategory": "UNMATCHED_PARENTHESIS",
            "confidence": 0.98,
            "description": "A closing or opening parenthesis was expected."
        },
        "BRACE_EXPECTED": {
            "category": SYNTAX_ERROR,
            "subcategory": "UNMATCHED_BRACE",
            "confidence": 0.98,
            "description": "A closing or opening curly brace '{' or '}' was expected."
        },
        "NOT_A_STATEMENT": {
            "category": SYNTAX_ERROR,
            "subcategory": "INVALID_STATEMENT",
            "confidence": 0.95,
            "description": "The expression does not constitute a valid Java statement."
        },
        "ILLEGAL_START_OF_EXPRESSION": {
            "category": SYNTAX_ERROR,
            "subcategory": "MALFORMED_EXPRESSION",
            "confidence": 0.95,
            "description": "Java encountered an unexpected token at the beginning of an expression."
        },
        "UNCLOSED_STRING_LITERAL": {
            "category": SYNTAX_ERROR,
            "subcategory": "UNCLOSED_STRING",
            "confidence": 0.99,
            "description": "A string literal was opened with double quotes but never closed before the line ended."
        },
        "UNCLOSED_CHAR_LITERAL": {
            "category": SYNTAX_ERROR,
            "subcategory": "UNCLOSED_CHAR",
            "confidence": 0.99,
            "description": "A character literal was opened with single quotes but not properly closed."
        },
        "INCOMPATIBLE_TYPES": {
            "category": TYPE_ERROR,
            "subcategory": "TYPE_MISMATCH",
            "confidence": 0.98,
            "description": "Attempted to assign a value of one type to a variable of an incompatible type."
        },
        "LOSSY_CONVERSION": {
            "category": TYPE_ERROR,
            "subcategory": "LOSSY_CONVERSION",
            "confidence": 0.98,
            "description": "Conversion between types would result in potential loss of data."
        },
        "MISSING_RETURN_STATEMENT": {
            "category": METHOD_ERROR,
            "subcategory": "MISSING_RETURN",
            "confidence": 0.98,
            "description": "Method declares a non-void return type but is missing a return statement on one or more paths."
        },
        "MISSING_RETURN_VALUE": {
            "category": METHOD_ERROR,
            "subcategory": "RETURN_VALUE_REQUIRED",
            "confidence": 0.98,
            "description": "A return statement in a non-void method did not provide a return value."
        },
        "VOID_RETURN_VALUE": {
            "category": METHOD_ERROR,
            "subcategory": "CANNOT_RETURN_FROM_VOID",
            "confidence": 0.98,
            "description": "Attempted to return a value from a method declared with void return type."
        },
        "METHOD_SIGNATURE_MISMATCH": {
            "category": METHOD_ERROR,
            "subcategory": "WRONG_ARGUMENTS",
            "confidence": 0.96,
            "description": "Method arguments do not match any available method signature."
        },
        "VARIABLE_NOT_INITIALIZED": {
            "category": VARIABLE_ERROR,
            "subcategory": "UNINITIALIZED_VARIABLE",
            "confidence": 0.98,
            "description": "Variable is being read before having been assigned a guaranteed initial value."
        },
        "DUPLICATE_VARIABLE": {
            "category": VARIABLE_ERROR,
            "subcategory": "ALREADY_DEFINED_VARIABLE",
            "confidence": 0.98,
            "description": "A variable with this identifier has already been declared in the current scope."
        },
        "PRIVATE_ACCESS": {
            "category": ACCESS_ERROR,
            "subcategory": "PRIVATE_MEMBER_ACCESS",
            "confidence": 0.97,
            "description": "Attempted to access a private member from outside its declaring class."
        },
        "CLASS_EXPECTED": {
            "category": CLASS_ERROR,
            "subcategory": "CLASS_TOKEN_EXPECTED",
            "confidence": 0.95,
            "description": "Class, interface, or enum expected by compiler."
        },
        "UNREACHABLE_STATEMENT": {
            "category": CODE_QUALITY,
            "subcategory": "DEAD_CODE",
            "confidence": 0.98,
            "description": "Code statement can never be executed at runtime."
        },
        "STATIC_CONTEXT_ERROR": {
            "category": METHOD_ERROR,
            "subcategory": "STATIC_REFERENCE_ERROR",
            "confidence": 0.97,
            "description": "Attempted to reference an instance member directly from a static context."
        }
    }

    def classify(self, error: ParsedCompilerError) -> ClassificationResult:
        """Classify a parsed compiler error into category, subcategory, and confidence."""
        # 1. Direct code lookup
        if error.compiler_code in self.CODE_MAP:
            mapping = self.CODE_MAP[error.compiler_code]
            sev = "ERROR" if error.compiler_code == "DIVISION_BY_ZERO" else error.severity.upper()
            return ClassificationResult(
                category=mapping["category"],
                subcategory=mapping["subcategory"],
                severity=sev,
                confidence=mapping["confidence"],
                description=mapping["description"]
            )

        # 2. Cannot find symbol - check symbol type
        if error.compiler_code == "CANNOT_FIND_SYMBOL" or "cannot find symbol" in error.message.lower():
            if error.symbol:
                symbol_lower = error.symbol.lower()
                if "variable" in symbol_lower:
                    return ClassificationResult(
                        category=self.VARIABLE_ERROR,
                        subcategory="UNDEFINED_VARIABLE",
                        severity=error.severity.upper(),
                        confidence=0.97,
                        description=f"The variable '{error.symbol}' has not been declared or is out of scope."
                    )
                elif "method" in symbol_lower:
                    return ClassificationResult(
                        category=self.METHOD_ERROR,
                        subcategory="UNDEFINED_METHOD",
                        severity=error.severity.upper(),
                        confidence=0.97,
                        description=f"The method '{error.symbol}' does not exist on the target object/class."
                    )
                elif "class" in symbol_lower:
                    return ClassificationResult(
                        category=self.CLASS_ERROR,
                        subcategory="UNDEFINED_CLASS",
                        severity=error.severity.upper(),
                        confidence=0.97,
                        description=f"The class '{error.symbol}' could not be found or imported."
                    )

            # Fallback for cannot find symbol without explicit symbol header
            msg_lower = error.message.lower()
            if "variable" in msg_lower:
                sub = "UNDEFINED_VARIABLE"
                cat = self.VARIABLE_ERROR
            elif "method" in msg_lower:
                sub = "UNDEFINED_METHOD"
                cat = self.METHOD_ERROR
            elif "class" in msg_lower:
                sub = "UNDEFINED_CLASS"
                cat = self.CLASS_ERROR
            else:
                sub = "UNDECLARED_IDENTIFIER"
                cat = self.VARIABLE_ERROR

            return ClassificationResult(
                category=cat,
                subcategory=sub,
                severity=error.severity.upper(),
                confidence=0.92,
                description=f"Compiler could not resolve identifier: {error.message}"
            )

        # 3. Message heuristic matching
        msg = error.message.lower()
        if "division by zero" in msg or "divzero" in msg:
            return ClassificationResult(
                category=self.ARITHMETIC_ERROR,
                subcategory="DIVISION_BY_ZERO",
                severity="ERROR",
                confidence=0.99,
                description="Attempted to divide by zero in an arithmetic expression."
            )
        elif "type" in msg or "convert" in msg:
            return ClassificationResult(
                category=self.TYPE_ERROR,
                subcategory="TYPE_MISMATCH",
                severity=error.severity.upper(),
                confidence=0.88,
                description=error.message
            )
        elif "expected" in msg or "syntax" in msg:
            return ClassificationResult(
                category=self.SYNTAX_ERROR,
                subcategory="MALFORMED_SYNTAX",
                severity=error.severity.upper(),
                confidence=0.85,
                description=error.message
            )
        elif "method" in msg:
            return ClassificationResult(
                category=self.METHOD_ERROR,
                subcategory="METHOD_ERROR",
                severity=error.severity.upper(),
                confidence=0.85,
                description=error.message
            )

        # Default fallback
        return ClassificationResult(
            category=self.UNKNOWN_ERROR,
            subcategory="GENERAL_ERROR",
            severity=error.severity.upper(),
            confidence=0.60,
            description=error.message
        )
