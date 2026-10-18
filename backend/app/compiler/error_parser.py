import re
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class ParsedCompilerError(BaseModel):
    """Structured representation of a parsed compiler error or warning."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file: str = "Main.java"
    line: int = 1
    column: Optional[int] = None
    severity: str = "error"  # "error" | "warning"
    message: str
    compiler_code: str = "COMPILATION_ERROR"
    code_snippet: Optional[str] = None
    symbol: Optional[str] = None
    location: Optional[str] = None
    is_primary: bool = False


class JavaErrorParser:
    """Parser for OpenJDK javac compiler diagnostics."""

    # Matches lines like: Main.java:3: error: incompatible types: ...
    # or: Main.java:3: warning: [unchecked] ...
    ERROR_HEADER_REGEX = re.compile(
        r'^(?P<file>[^:\r\n]+):(?P<line>\d+):\s*(?P<severity>error|warning):\s*(?P<message>.+)$',
        re.MULTILINE
    )

    # Identifies specific compiler code tags from the message
    ERROR_CODE_PATTERNS = [
        (re.compile(r"division by zero|divzero", re.I), "DIVISION_BY_ZERO"),
        (re.compile(r"incompatible types|cannot be converted to", re.I), "INCOMPATIBLE_TYPES"),
        (re.compile(r"';' expected", re.I), "SEMICOLON_EXPECTED"),
        (re.compile(r"'\)' expected|'\(' expected", re.I), "PARENTHESIS_EXPECTED"),
        (re.compile(r"'\}' expected|'\{' expected", re.I), "BRACE_EXPECTED"),
        (re.compile(r"cannot find symbol", re.I), "CANNOT_FIND_SYMBOL"),
        (re.compile(r"variable .+ might not have been initialized", re.I), "VARIABLE_NOT_INITIALIZED"),
        (re.compile(r"variable .+ is already defined", re.I), "DUPLICATE_VARIABLE"),
        (re.compile(r"method .+ cannot be applied to given types", re.I), "METHOD_SIGNATURE_MISMATCH"),
        (re.compile(r"missing return statement", re.I), "MISSING_RETURN_STATEMENT"),
        (re.compile(r"missing return value", re.I), "MISSING_RETURN_VALUE"),
        (re.compile(r"cannot return a value from a method with void result type", re.I), "VOID_RETURN_VALUE"),
        (re.compile(r"unreachable statement", re.I), "UNREACHABLE_STATEMENT"),
        (re.compile(r"has private access in", re.I), "PRIVATE_ACCESS"),
        (re.compile(r"class, interface, or enum expected", re.I), "CLASS_EXPECTED"),
        (re.compile(r"not a statement", re.I), "NOT_A_STATEMENT"),
        (re.compile(r"illegal start of expression", re.I), "ILLEGAL_START_OF_EXPRESSION"),
        (re.compile(r"unclosed string literal", re.I), "UNCLOSED_STRING_LITERAL"),
        (re.compile(r"unclosed character literal", re.I), "UNCLOSED_CHAR_LITERAL"),
        (re.compile(r"non-static .+ cannot be referenced from a static context", re.I), "STATIC_CONTEXT_ERROR"),
        (re.compile(r"possible lossy conversion", re.I), "LOSSY_CONVERSION"),
    ]

    def _determine_compiler_code(self, message: str) -> str:
        """Infer standardized error code from javac error message."""
        for pattern, code in self.ERROR_CODE_PATTERNS:
            if pattern.search(message):
                return code
        return "GENERAL_COMPILER_ERROR"

    def parse(self, stderr: str) -> List[ParsedCompilerError]:
        """Parse javac stderr output into structured errors."""
        if not stderr or not stderr.strip():
            return []

        lines = stderr.splitlines()
        errors: List[ParsedCompilerError] = []
        current_error: Optional[ParsedCompilerError] = None
        current_snippet_lines: List[str] = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line is the start of a new error diagnostic
            match = self.ERROR_HEADER_REGEX.match(line)
            if match:
                # Save snippet to previous error if any
                if current_error and current_snippet_lines:
                    current_error.code_snippet = "\n".join(current_snippet_lines).rstrip()
                    current_snippet_lines = []

                file_path = match.group("file").strip()
                line_num = int(match.group("line"))
                severity = match.group("severity").lower()
                msg = match.group("message").strip()

                compiler_code = self._determine_compiler_code(msg)
                # Treat division by zero compiler diagnostic as an error
                if compiler_code == "DIVISION_BY_ZERO":
                    severity = "error"

                current_error = ParsedCompilerError(
                    file=file_path,
                    line=line_num,
                    severity=severity,
                    message=msg,
                    compiler_code=compiler_code,
                    is_primary=(len(errors) == 0)  # First error is marked primary
                )
                errors.append(current_error)
                i += 1
                continue

            # If inside an error block, parse supplementary details
            if current_error:
                stripped = line.strip()

                # Check for "symbol: variable x" or "symbol: method foo()"
                if stripped.startswith("symbol:"):
                    current_error.symbol = stripped.replace("symbol:", "").strip()
                elif stripped.startswith("location:"):
                    current_error.location = stripped.replace("location:", "").strip()
                elif "^" in line:
                    # Caret line indicates column position
                    caret_col = line.find("^") + 1
                    current_error.column = caret_col
                    current_snippet_lines.append(line)
                elif stripped.endswith("error") or stripped.endswith("errors") or stripped.endswith("warning"):
                    # e.g., "2 errors" or "1 warning" summary line
                    pass
                else:
                    # Snippet or continuation
                    current_snippet_lines.append(line)

            i += 1

        # Attach final snippet if exists
        if current_error and current_snippet_lines:
            current_error.code_snippet = "\n".join(current_snippet_lines).rstrip()

        # 1. Suppress redundant NOT_A_STATEMENT errors on lines that already have DIVISION_BY_ZERO
        div_zero_lines = {e.line for e in errors if e.compiler_code == "DIVISION_BY_ZERO"}
        if div_zero_lines:
            errors = [e for e in errors if not (e.compiler_code == "NOT_A_STATEMENT" and e.line in div_zero_lines)]

        # 2. Convert standalone NOT_A_STATEMENT to DIVISION_BY_ZERO if the snippet contains division by zero
        for err in errors:
            if err.compiler_code == "NOT_A_STATEMENT" and err.code_snippet:
                if re.search(r'/\s*0\b|%\s*0\b', err.code_snippet):
                    err.compiler_code = "DIVISION_BY_ZERO"
                    err.severity = "error"
                    err.message = "division by zero"

        # 3. Deduplicate multiple DIVISION_BY_ZERO errors on the same line
        seen_divzero = set()
        deduped = []
        for e in errors:
            if e.compiler_code == "DIVISION_BY_ZERO":
                if e.line in seen_divzero:
                    continue
                seen_divzero.add(e.line)
            deduped.append(e)
        errors = deduped

        # Sort errors by line number
        errors.sort(key=lambda e: (e.line, e.column or 0))

        # Re-tag the first one after sorting as primary if not already
        if errors:
            errors[0].is_primary = True

        return errors
