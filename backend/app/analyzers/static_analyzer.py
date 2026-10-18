import re
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class StaticWarning(BaseModel):
    """Static analysis warning or code quality tip."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    severity: str = "warning"  # "warning" | "info"
    line: int
    column: Optional[int] = None
    title: str
    message: str
    why_it_matters: str
    suggestion: str
    is_potential: bool = True  # Labeled as potential issue per requirements


class JavaStaticAnalyzer:
    """Heuristic static code analyzer for Java."""

    # Regex to extract variable declarations
    VAR_DECL_REGEX = re.compile(
        r'\b(?:int|double|float|long|boolean|char|byte|short|String|[A-Z][A-Za-z0-9_<>]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*[^;]+)?\s*;',
    )

    # Keywords to avoid flagging as variables
    JAVA_KEYWORDS = {
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
        "class", "const", "continue", "default", "do", "double", "else", "enum",
        "extends", "final", "finally", "float", "for", "goto", "if", "implements",
        "import", "instanceof", "int", "interface", "long", "native", "new",
        "package", "private", "protected", "public", "return", "short", "static",
        "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while", "true", "false", "null"
    }

    def analyze(self, source_code: str) -> List[StaticWarning]:
        """Perform static analysis on Java code."""
        if not source_code or not source_code.strip():
            return []

        warnings: List[StaticWarning] = []
        lines = source_code.splitlines()

        # Check 1: Empty Catch Blocks
        for idx, line in enumerate(lines, start=1):
            if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', line):
                warnings.append(StaticWarning(
                    rule_id="EMPTY_CATCH_BLOCK",
                    severity="warning",
                    line=idx,
                    title="Empty Catch Block",
                    message="Empty catch block swallows exceptions silently without handling or logging.",
                    why_it_matters="Silently catching exceptions hides bugs, making errors impossible to trace when something fails at runtime.",
                    suggestion="Log the exception with `System.err.println(e.getMessage());` or rethrow/handle it appropriately."
                ))

        # Check 2: String Comparison with '=='
        for idx, line in enumerate(lines, start=1):
            # Check for "..." == var or var == "..." or str1 == str2 (rough heuristic)
            if re.search(r'"[^"]*"\s*==|==\s*"[^"]*"', line):
                warnings.append(StaticWarning(
                    rule_id="STRING_EQUALS_CHECK",
                    severity="warning",
                    line=idx,
                    title="String Identity Comparison",
                    message="Using '==' to compare Strings checks reference identity, not value equality.",
                    why_it_matters="Two distinct String objects containing identical text will evaluate to 'false' when compared with '=='.",
                    suggestion="Use `.equals()` for string content comparison: `str.equals(\"text\")`."
                ))

        # Check 3: Suspicious Condition Assignment (e.g. if (x = true))
        for idx, line in enumerate(lines, start=1):
            assign_match = re.search(r'\bif\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^=][^)]*)\)', line)
            if assign_match:
                var_name = assign_match.group(1)
                warnings.append(StaticWarning(
                    rule_id="ASSIGNMENT_IN_CONDITION",
                    severity="warning",
                    line=idx,
                    title="Assignment in Conditional",
                    message=f"Possible accidental assignment '=' instead of equality comparison '==' in `if ({var_name} = ...)`.",
                    why_it_matters="This assigns a value to the variable rather than testing whether it matches.",
                    suggestion=f"Replace '=' with '==' to test equality: `if ({var_name} == ...)`."
                ))

        # Check 4: Suspicious Infinite Loops (while(true) with no break/return)
        in_while_true = False
        while_start_line = 0
        loop_body_lines: List[str] = []
        brace_depth = 0

        for idx, line in enumerate(lines, start=1):
            if not in_while_true and re.search(r'\bwhile\s*\(\s*true\s*\)', line):
                in_while_true = True
                while_start_line = idx
                brace_depth += line.count('{') - line.count('}')
                loop_body_lines = [line]
                continue

            if in_while_true:
                brace_depth += line.count('{') - line.count('}')
                loop_body_lines.append(line)
                if brace_depth <= 0:
                    # Loop closed, examine body
                    body_text = "\n".join(loop_body_lines)
                    has_exit = any(kw in body_text for kw in ["break", "return", "System.exit", "throw"])
                    if not has_exit:
                        warnings.append(StaticWarning(
                            rule_id="INFINITE_LOOP",
                            severity="warning",
                            line=while_start_line,
                            title="Potential Infinite Loop",
                            message="`while(true)` loop does not appear to contain a `break`, `return`, or exit statement.",
                            why_it_matters="An infinite loop without an exit condition freezes program execution and consumes 100% CPU.",
                            suggestion="Add a termination condition with a `break;` statement or replace with a guarded `while (condition)`."
                        ))
                    in_while_true = False
                    loop_body_lines = []

        # Check 5: Unused Local Variables
        for idx, line in enumerate(lines, start=1):
            match = self.VAR_DECL_REGEX.search(line)
            if match:
                var_name = match.group(1)
                if var_name in self.JAVA_KEYWORDS or len(var_name) <= 1 and var_name in ['i', 'j', 'k']:
                    continue

                # Count occurrences of the word across the whole file
                pattern = rf'\b{re.escape(var_name)}\b'
                occurrences = [
                    line_no for line_no, l in enumerate(lines, start=1)
                    if re.search(pattern, l)
                ]

                # If it only appears once (on its declaration line), it is unused
                if len(occurrences) == 1 and occurrences[0] == idx:
                    warnings.append(StaticWarning(
                        rule_id="UNUSED_VARIABLE",
                        severity="warning",
                        line=idx,
                        title="Unused Local Variable",
                        message=f"Variable `{var_name}` is declared but never used elsewhere in the file.",
                        why_it_matters="Unused variables clutter code, consume stack space, and create confusion for readers.",
                        suggestion=f"Remove the unused variable `{var_name}` or utilize it in your logic."
                    ))

        # Check 6: Empty Methods
        method_pattern = re.compile(
            r'\b(?:public|protected|private|static|\s)+\s+(?:void|[A-Za-z0-9_<>]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{\s*\}'
        )
        for idx, line in enumerate(lines, start=1):
            match = method_pattern.search(line)
            if match:
                method_name = match.group(1)
                # Ignore main method if empty
                if method_name != "main":
                    warnings.append(StaticWarning(
                        rule_id="EMPTY_METHOD",
                        severity="info",
                        line=idx,
                        title="Empty Method Body",
                        message=f"Method `{method_name}` has an empty body without statements.",
                        why_it_matters="Empty methods do nothing when executed and may indicate incomplete implementation.",
                        suggestion=f"Implement `{method_name}` or remove it if not needed."
                    ))

        return warnings
