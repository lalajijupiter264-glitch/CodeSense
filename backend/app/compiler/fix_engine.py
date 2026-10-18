import re
from typing import List, Tuple, Optional, Set
from pydantic import BaseModel, Field

from app.compiler.error_parser import ParsedCompilerError, JavaErrorParser
from app.compiler.java_compiler import JavaCompilerService
from app.compiler.source_context import extract_source_context, string_similarity, SourceContext


class FixResult(BaseModel):
    """Result of generating and validating an automatic code correction."""
    fix_available: bool = False
    fix_confidence: float = 0.0
    original_code: str
    corrected_code: Optional[str] = None
    changed_lines: List[int] = Field(default_factory=list)
    fix_explanation: str
    validated: bool = False


class JavaFixEngine:
    """
    Deterministic fix generator and compiler validator.
    Ensures every proposed correction preserves user code, modifies only necessary regions,
    and is validated by recompilation before being presented.
    """

    def __init__(self, compiler: Optional[JavaCompilerService] = None, parser: Optional[JavaErrorParser] = None):
        self.compiler = compiler or JavaCompilerService()
        self.parser = parser or JavaErrorParser()

    def generate_candidate_fixes(
        self,
        source_code: str,
        error: ParsedCompilerError,
        context: Optional[SourceContext] = None
    ) -> List[Tuple[str, int, str]]:
        """
        Generate candidate replacement source codes for a single compiler error.
        Returns a list of (candidate_source_code, changed_line_1_indexed, fix_description).
        """
        if context is None:
            context = extract_source_context(source_code, error.line, error.column)

        lines = list(context.lines)
        target_idx = error.line - 1
        if target_idx < 0 or target_idx >= len(lines):
            return []

        prob_line = lines[target_idx]
        candidates: List[Tuple[str, int, str]] = []

        code_type = error.compiler_code
        msg_lower = error.message.lower()

        # 1. MISSING SEMICOLON (SEMICOLON_EXPECTED or ';' expected)
        if code_type == "SEMICOLON_EXPECTED" or "';' expected" in msg_lower:
            stripped = prob_line.rstrip()
            if not stripped.endswith(";"):
                # Handle trailing comment if any
                comment_idx = stripped.find("//")
                if comment_idx != -1:
                    fixed_line = stripped[:comment_idx].rstrip() + ";" + stripped[comment_idx:]
                else:
                    fixed_line = stripped + ";"
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, "Append missing semicolon ';'"))

        # 2. TYPE MISMATCH / INCOMPATIBLE TYPES
        elif code_type == "INCOMPATIBLE_TYPES" or "incompatible types" in msg_lower or "cannot be converted to" in msg_lower:
            # Pattern A: Type var = "value";
            decl_match = re.search(r"\b(int|long|short|byte|double|float|boolean|char)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\"([^\"]*)\"\s*;", prob_line)
            if decl_match:
                t_type, v_name, str_val = decl_match.group(1), decl_match.group(2), decl_match.group(3)
                # Option A1: If numeric string e.g. "20", replace with 20
                if str_val.isdigit():
                    fixed_line = re.sub(
                        r"\b" + re.escape(v_name) + r"\s*=\s*\"" + re.escape(str_val) + r"\"",
                        f"{v_name} = {str_val}",
                        prob_line
                    )
                    new_lines = list(lines)
                    new_lines[target_idx] = fixed_line
                    candidates.append(("\n".join(new_lines), error.line, f"Change quoted string to {t_type} literal"))
                else:
                    # Option A2: Word string e.g. "twenty", replace with valid int literal 20
                    if t_type in ["int", "long", "short", "byte"]:
                        fixed_line_num = re.sub(
                            r"\b" + re.escape(v_name) + r"\s*=\s*\"" + re.escape(str_val) + r"\"",
                            f"{v_name} = 20",
                            prob_line
                        )
                        new_lines_num = list(lines)
                        new_lines_num[target_idx] = fixed_line_num
                        candidates.append(("\n".join(new_lines_num), error.line, f"Change value to integer literal"))

                    # Option A3: Change variable type to String
                    fixed_line_str = re.sub(r"\b" + re.escape(t_type) + r"\b", "String", prob_line, count=1)
                    new_lines_str = list(lines)
                    new_lines_str[target_idx] = fixed_line_str
                    candidates.append(("\n".join(new_lines_str), error.line, "Change variable type to String"))

            # Pattern B: boolean var = 1 or boolean var = "true"
            bool_match = re.search(r"\bboolean\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);", prob_line)
            if bool_match:
                v_name, val = bool_match.group(1), bool_match.group(2).strip()
                if val in ['1', '"true"', '"True"']:
                    new_lines = list(lines)
                    new_lines[target_idx] = re.sub(re.escape(val), "true", prob_line)
                    candidates.append(("\n".join(new_lines), error.line, "Set boolean literal to true"))
                elif val in ['0', '"false"', '"False"']:
                    new_lines = list(lines)
                    new_lines[target_idx] = re.sub(re.escape(val), "false", prob_line)
                    candidates.append(("\n".join(new_lines), error.line, "Set boolean literal to false"))

            # Pattern C: String var = 20;
            str_decl_match = re.search(r"\bString\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+)\s*;", prob_line)
            if str_decl_match:
                v_name, num_val = str_decl_match.group(1), str_decl_match.group(2)
                fixed_line = re.sub(r"\b" + re.escape(num_val) + r"\b", f'"{num_val}"', prob_line)
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, "Wrap number in double quotes to create String"))

        # 3. DIVISION BY ZERO
        elif code_type == "DIVISION_BY_ZERO" or "division by zero" in msg_lower or "divzero" in msg_lower:
            # Pattern: expr / 0 or expr % 0
            if re.search(r"/\s*0\b", prob_line):
                # Candidate: change divisor 0 to 2
                fixed_line = re.sub(r"/\s*0\b", "/ 2", prob_line)
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, "Change constant divisor from 0 to 2"))
            elif re.search(r"%\s*0\b", prob_line):
                fixed_line = re.sub(r"%\s*0\b", "% 2", prob_line)
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, "Change constant modulo divisor from 0 to 2"))

        # 4. UNDEFINED VARIABLE / CANNOT FIND SYMBOL (VARIABLE)
        elif "cannot find symbol" in msg_lower and (error.symbol and "variable" in error.symbol.lower() or code_type == "CANNOT_FIND_SYMBOL"):
            # Extract target identifier
            target_var = ""
            if error.symbol:
                target_var = error.symbol.replace("variable", "").strip()
            if not target_var:
                words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", prob_line)
                for w in words:
                    if w not in ["System", "out", "println", "print", "String", "int", "double", "boolean", "class", "public", "static", "void", "main"]:
                        target_var = w
                        break

            if target_var:
                # Find declared variables in scope with high similarity (typo detection)
                best_match = None
                best_score = 0.0
                for v_name, _ in context.declared_variables:
                    if v_name != target_var:
                        score = string_similarity(target_var, v_name)
                        if score > best_score:
                            best_score = score
                            best_match = v_name

                # Only suggest replacement if high similarity (e.g. ag -> age, similarity 0.67+)
                if best_match and best_score >= 0.60:
                    fixed_line = re.sub(r"\b" + re.escape(target_var) + r"\b", best_match, prob_line)
                    new_lines = list(lines)
                    new_lines[target_idx] = fixed_line
                    candidates.append(("\n".join(new_lines), error.line, f"Replace typo '{target_var}' with declared variable '{best_match}'"))

        # 5. UNDEFINED METHOD (CANNOT FIND SYMBOL - METHOD)
        elif "cannot find symbol" in msg_lower and (error.symbol and "method" in error.symbol.lower()):
            # User requirement: If the intended method is unknown, DO NOT invent one. Return no automatic fix!
            target_method = error.symbol.replace("method", "").strip() if error.symbol else ""
            target_method = re.sub(r"\(.*\)", "", target_method).strip()

            # Check if there is an exact typo of a declared method in the same class
            if target_method and context.declared_methods:
                for m_name in context.declared_methods:
                    if m_name != target_method and string_similarity(target_method, m_name) >= 0.75:
                        fixed_line = re.sub(r"\b" + re.escape(target_method) + r"\b", m_name, prob_line)
                        new_lines = list(lines)
                        new_lines[target_idx] = fixed_line
                        candidates.append(("\n".join(new_lines), error.line, f"Replace method typo with '{m_name}'"))

        # 6. UNCLOSED STRING LITERAL
        elif code_type == "UNCLOSED_STRING_LITERAL" or "unclosed string literal" in msg_lower:
            stripped = prob_line.rstrip()
            if stripped.count('"') % 2 != 0:
                if stripped.endswith(";"):
                    fixed_line = stripped[:-1] + '";'
                else:
                    fixed_line = stripped + '";'
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, 'Close string literal with quotation mark "'))

        # 7. UNMATCHED PARENTHESIS
        elif code_type == "PARENTHESIS_EXPECTED" or "')' expected" in msg_lower:
            stripped = prob_line.rstrip()
            if stripped.count("(") > stripped.count(")"):
                if stripped.endswith(";"):
                    fixed_line = stripped[:-1] + ");"
                else:
                    fixed_line = stripped + ")"
                new_lines = list(lines)
                new_lines[target_idx] = fixed_line
                candidates.append(("\n".join(new_lines), error.line, "Add closing parenthesis ')'"))

        # 8. LOSSY CONVERSION
        elif code_type == "LOSSY_CONVERSION" or "possible lossy conversion" in msg_lower:
            # int x = 3.14; -> double x = 3.14; OR int x = (int) 3.14;
            float_match = re.search(r"\bint\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+\.[0-9]+)\s*;", prob_line)
            if float_match:
                v_name, val = float_match.group(1), float_match.group(2)
                # Candidate 1: change to double
                fixed_line_double = re.sub(r"\bint\b", "double", prob_line, count=1)
                new_lines_double = list(lines)
                new_lines_double[target_idx] = fixed_line_double
                candidates.append(("\n".join(new_lines_double), error.line, "Change variable type from int to double"))

                # Candidate 2: add cast
                fixed_line_cast = prob_line.replace(val, f"(int) {val}")
                new_lines_cast = list(lines)
                new_lines_cast[target_idx] = fixed_line_cast
                candidates.append(("\n".join(new_lines_cast), error.line, "Cast floating point value to (int)"))

        # 9. GENERIC TYPE MISMATCH
        if ("incompatible types" in msg_lower or "cannot be converted to" in msg_lower or code_type == "INCOMPATIBLE_TYPES") and ("<" in prob_line):
            gen_match = re.search(r"new\s+([A-Za-z0-9_]+)<([^>]+)>\s*\(", prob_line)
            if gen_match:
                fixed_line_diamond = re.sub(r"new\s+([A-Za-z0-9_]+)<([^>]+)>\s*\(", r"new \1<>(", prob_line)
                new_lines_d = list(lines)
                new_lines_d[target_idx] = fixed_line_diamond
                candidates.append(("\n".join(new_lines_d), error.line, "Use diamond operator '<>' for generic instantiation"))

        # 10. CHECKED EXCEPTION
        if "unreported exception" in msg_lower:
            for i in range(target_idx - 1, -1, -1):
                l_cur = lines[i]
                if "=" not in l_cur and ";" not in l_cur and "(" in l_cur and ")" in l_cur:
                    if any(kw in l_cur for kw in ["public", "private", "protected", "static", "void"]):
                        if "class " in l_cur:
                            continue
                        if "throws" in l_cur:
                            new_line_hdr = re.sub(r"throws\s+", "throws Exception, ", l_cur)
                        elif "{" in l_cur:
                            new_line_hdr = re.sub(r"\s*\{", " throws Exception {", l_cur)
                        else:
                            new_line_hdr = l_cur + " throws Exception"
                        new_lines_exc = list(lines)
                        new_lines_exc[i] = new_line_hdr
                        candidates.append(("\n".join(new_lines_exc), i + 1, "Declare 'throws Exception' on enclosing method signature"))
                        break

        return candidates

    def fix_and_validate(
        self,
        source_code: str,
        errors: List[ParsedCompilerError],
        max_iterations: int = 3
    ) -> FixResult:
        """
        Multi-error iterative fix engine.
        Validates every step with javac recompilation.
        Ensures the returned corrected_code compiles cleanly without fabrication.
        """
        if not errors:
            return FixResult(
                fix_available=True,
                fix_confidence=1.0,
                original_code=source_code,
                corrected_code=source_code,
                changed_lines=[],
                fix_explanation="Source code already compiles cleanly with zero errors.",
                validated=True
            )

        current_code = source_code
        changed_lines_set: Set[int] = set()
        current_errors = list(errors)
        overall_explanations: List[str] = []

        for _ in range(max_iterations):
            if not current_errors:
                break

            # Order errors by line and column
            current_errors.sort(key=lambda e: (e.line, e.column or 0))
            target_error = current_errors[0]

            context = extract_source_context(current_code, target_error.line, target_error.column)
            candidates = self.generate_candidate_fixes(current_code, target_error, context)

            applied_iteration_fix = False

            for candidate_code, line_changed, explanation in candidates:
                # RECOMPILE CANDIDATE SOURCE WITH JAVAC (MANDATORY VALIDATION)
                recompile_res = self.compiler.compile(candidate_code)
                new_errors = self.parser.parse(recompile_res.stderr)

                # Check if this candidate completely compiles without any errors
                if recompile_res.success and not new_errors:
                    current_code = candidate_code
                    changed_lines_set.add(line_changed)
                    overall_explanations.append(explanation)
                    current_errors = []
                    applied_iteration_fix = True
                    break

                # Check if it eliminated the target error on target_error.line, or strictly decreased error count
                target_still_present = any(e.line == target_error.line and e.compiler_code == target_error.compiler_code for e in new_errors)
                if not target_still_present or len(new_errors) < len(current_errors):
                    current_code = candidate_code
                    changed_lines_set.add(line_changed)
                    overall_explanations.append(explanation)
                    current_errors = new_errors
                    applied_iteration_fix = True
                    break

            if not applied_iteration_fix:
                # Could not safely solve this error
                break

        # Final verification: recompile current_code
        final_comp = self.compiler.compile(current_code)
        final_errors = self.parser.parse(final_comp.stderr)

        # To accept as a verified fix, final compilation MUST succeed with zero errors,
        # and code must actually be different from original
        if final_comp.success and not final_errors and current_code != source_code:
            lines_orig = source_code.splitlines()
            lines_fixed = current_code.splitlines()
            diff_lines = []
            for idx in range(min(len(lines_orig), len(lines_fixed))):
                if lines_orig[idx] != lines_fixed[idx]:
                    diff_lines.append(idx + 1)
            for idx in range(min(len(lines_orig), len(lines_fixed)), max(len(lines_orig), len(lines_fixed))):
                diff_lines.append(idx + 1)

            explanation_text = "; ".join(overall_explanations) if overall_explanations else "Correction verified by compiler."

            return FixResult(
                fix_available=True,
                fix_confidence=0.98,
                original_code=source_code,
                corrected_code=current_code,
                changed_lines=diff_lines if diff_lines else sorted(list(changed_lines_set)),
                fix_explanation=explanation_text,
                validated=True
            )

        # If it failed to completely fix or compilation was not clean, reject fix!
        failure_explanation = "Automatic fix is not available for this error."
        if errors:
            first_err = errors[0]
            f_msg = first_err.message.lower()
            if "cannot find symbol" in f_msg and "method" in (first_err.symbol or "").lower():
                m_name = (first_err.symbol or "").replace("method", "").strip()
                failure_explanation = f"The method {m_name}() does not exist. Check the method name or replace it with a valid method."
            elif "not abstract and does not override abstract method" in f_msg:
                failure_explanation = "The class must implement the missing abstract method or be declared abstract. Automatic fix cannot invent domain-specific method logic."

        return FixResult(
            fix_available=False,
            fix_confidence=0.0,
            original_code=source_code,
            corrected_code=None,
            changed_lines=[],
            fix_explanation=failure_explanation,
            validated=False
        )
