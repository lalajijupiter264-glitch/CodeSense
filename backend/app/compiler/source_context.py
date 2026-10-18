import re
from typing import List, Dict, Set, Tuple, Optional
from pydantic import BaseModel, Field


class SourceContext(BaseModel):
    """Context extracted from Java source code for intelligent error fixing."""
    lines: List[str]
    problematic_line_num: int
    problematic_line: str
    indentation: str
    surrounding_before: List[str] = Field(default_factory=list)
    surrounding_after: List[str] = Field(default_factory=list)
    declared_variables: List[Tuple[str, str]] = Field(default_factory=list)  # (name, type)
    declared_methods: List[str] = Field(default_factory=list)
    class_name: str = "Main"
    all_identifiers: Set[str] = Field(default_factory=set)


def extract_source_context(source_code: str, error_line: int, error_column: Optional[int] = None) -> SourceContext:
    """Extract syntactic context, scope symbols, and formatting from source code."""
    lines = source_code.splitlines()
    total_lines = len(lines)

    target_idx = max(0, min(error_line - 1, total_lines - 1)) if total_lines > 0 else 0
    prob_line = lines[target_idx] if total_lines > 0 else ""

    # Extract indentation
    indent_match = re.match(r"^(\s*)", prob_line)
    indentation = indent_match.group(1) if indent_match else ""

    # Surrounding lines (up to 3 before and 3 after)
    start_before = max(0, target_idx - 3)
    surrounding_before = lines[start_before:target_idx]

    end_after = min(total_lines, target_idx + 4)
    surrounding_after = lines[target_idx + 1:end_after]

    # Extract class name
    class_name = "Main"
    class_match = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", source_code)
    if class_match:
        class_name = class_match.group(1)

    # Extract declared variables (e.g. 'int age', 'String name', 'double total')
    declared_vars: List[Tuple[str, str]] = []
    var_pattern = re.compile(r"\b(int|long|short|byte|double|float|boolean|char|String|[A-Z][A-Za-z0-9_<>]*)\s+([a-z_][A-Za-z0-9_]*)\b")
    for l in lines:
        for match in var_pattern.finditer(l):
            var_type, var_name = match.group(1), match.group(2)
            if var_name not in ["main", "class", "void", "return", "if", "for", "while"]:
                declared_vars.append((var_name, var_type))

    # Extract declared methods (e.g. 'public static void main(...)', 'int compute(...)')
    declared_methods: List[str] = []
    method_pattern = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{")
    for l in lines:
        for match in method_pattern.finditer(l):
            m_name = match.group(1)
            if m_name not in ["if", "for", "while", "switch"]:
                declared_methods.append(m_name)

    # All word identifiers
    all_identifiers = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source_code))

    return SourceContext(
        lines=lines,
        problematic_line_num=error_line,
        problematic_line=prob_line,
        indentation=indentation,
        surrounding_before=surrounding_before,
        surrounding_after=surrounding_after,
        declared_variables=declared_vars,
        declared_methods=declared_methods,
        class_name=class_name,
        all_identifiers=all_identifiers
    )


def string_similarity(a: str, b: str) -> float:
    """Calculate normalized similarity ratio between two strings using Levenshtein distance."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    la, lb = len(a), len(b)
    # Levenshtein distance matrix
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j

    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost # substitution
            )

    dist = dp[la][lb]
    max_len = max(la, lb)
    return 1.0 - (dist / max_len)
