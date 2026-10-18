"""
Regression tests for JavaFixEngine and validated corrected-code architecture.

Verifies:
1. Type mismatch (e.g. int age = "twenty"; -> int age = 20;)
2. Missing semicolon (e.g. System.out.println("Hello") -> System.out.println("Hello");)
3. Undefined variable typo (e.g. ag -> age)
4. Undefined method (intentionally disabled, never fabricate code)
5. Division by zero (constant expression fix validated by compiler)
6. Missing interface method (intentionally disabled, domain-specific)
7. Checked exception (declare throws Exception on method)
8. Generic type mismatch (diamond operator)
9. Multiple errors (iterative multi-step fix)
10. Valid program (preserves cleanly)
11. End-to-end POST /api/analyze integration
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.compiler.java_compiler import JavaCompilerService
from app.compiler.error_parser import JavaErrorParser
from app.compiler.fix_engine import JavaFixEngine, FixResult

client = TestClient(app)
compiler = JavaCompilerService()
parser = JavaErrorParser()
fix_engine = JavaFixEngine(compiler=compiler, parser=parser)


def test_case_1_type_mismatch():
    """1. Type mismatch: int age = 'twenty'; -> int age = 20;"""
    code = """public class Main {
    public static void main(String[] args) {
        int age = "twenty";
        System.out.println(age);
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    # Verify original source and unrelated code are preserved
    assert "public class Main" in result.corrected_code
    assert "System.out.println(age);" in result.corrected_code
    assert 'int age = 20;' in result.corrected_code
    assert result.changed_lines == [3]

    # Verify compilation succeeds
    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_2_missing_semicolon():
    """2. Missing semicolon: System.out.println("Hello") -> ;"""
    code = """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello")
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert 'System.out.println("Hello");' in result.corrected_code
    assert result.changed_lines == [3]

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_3_undefined_variable_typo():
    """3. Undefined variable typo: ag -> age"""
    code = """public class Main {
    public static void main(String[] args) {
        int age = 20;
        System.out.println(ag);
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert "System.out.println(age);" in result.corrected_code
    assert "int age = 20;" in result.corrected_code
    assert result.changed_lines == [4]

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_4_undefined_method_intentionally_disabled():
    """4. Undefined method: name.nonExistingMethod(); -> fix_available=False, never fabricate code."""
    code = """public class Main {
    public static void main(String[] args) {
        String name = "Madhav";
        name.nonExistingMethod();
        System.out.println(name);
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is False
    assert result.validated is False
    assert result.corrected_code is None
    assert "nonExistingMethod" in result.fix_explanation or "does not exist" in result.fix_explanation.lower()


def test_case_5_division_by_zero():
    """5. Division by zero: int result = 10 / 0; -> int result = 10 / 2;"""
    code = """public class Main {
    public static void main(String[] args) {
        int result = 10 / 0;
        System.out.println(result);
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert "int result = 10 / 2;" in result.corrected_code
    assert "System.out.println(result);" in result.corrected_code
    assert result.changed_lines == [3]

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_6_missing_interface_method_intentionally_disabled():
    """6. Missing interface method: domain-specific logic, automatic fixing intentionally disabled."""
    code = """public class Main implements Runnable {
    public static void main(String[] args) {
        System.out.println("Running");
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is False
    assert result.validated is False
    assert result.corrected_code is None
    assert "abstract" in result.fix_explanation.lower()


def test_case_7_checked_exception():
    """7. Checked exception: declare throws Exception on method."""
    code = """import java.io.FileReader;

public class Main {
    public static void main(String[] args) {
        FileReader reader = new FileReader("test.txt");
        System.out.println("Ready");
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert "throws Exception" in result.corrected_code
    assert "FileReader reader = new FileReader" in result.corrected_code

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_8_generic_type_mismatch():
    """8. Generic type mismatch: List<String> list = new ArrayList<Integer>(); -> diamond operator."""
    code = """import java.util.List;
import java.util.ArrayList;

public class Main {
    public static void main(String[] args) {
        List<String> list = new ArrayList<Integer>();
        System.out.println(list.size());
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert "new ArrayList<>()" in result.corrected_code
    assert "List<String> list" in result.corrected_code

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_9_multiple_errors_iterative():
    """9. Multiple errors: type mismatch + missing semicolon resolved iteratively."""
    code = """public class Main {
    public static void main(String[] args) {
        int age = "twenty";
        System.out.println("Hello")
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) >= 1

    result = fix_engine.fix_and_validate(code, errors, max_iterations=3)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code is not None

    assert "int age = 20;" in result.corrected_code
    assert 'System.out.println("Hello");' in result.corrected_code
    assert set(result.changed_lines) == {3, 4}

    final_comp = compiler.compile(result.corrected_code)
    assert final_comp.success is True
    assert parser.parse(final_comp.stderr) == []


def test_case_10_valid_program():
    """10. Valid program: already compiles cleanly, preserved without changes."""
    code = """public class Main {
    public static void main(String[] args) {
        int a = 10;
        int b = 20;
        System.out.println(a + b);
    }
}"""
    comp = compiler.compile(code)
    errors = parser.parse(comp.stderr)
    assert len(errors) == 0

    result = fix_engine.fix_and_validate(code, errors)
    assert result.fix_available is True
    assert result.validated is True
    assert result.corrected_code == code
    assert result.changed_lines == []


def test_api_e2e_validated_fix():
    """Verify POST /api/analyze returns structured fix metadata for type mismatch."""
    code = """public class Main {
    public static void main(String[] args) {
        int age = "twenty";
        System.out.println(age);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1

    exp = data["errors"][0]["explanation"]
    assert exp is not None
    assert exp["fix_available"] is True
    assert exp["validated"] is True
    assert exp["corrected_code"] is not None
    assert "int age = 20;" in exp["corrected_code"]
    assert exp["changed_lines"] == [3]


def test_api_e2e_intentionally_disabled_fix():
    """Verify POST /api/analyze does NOT invent code for ambiguous method calls."""
    code = """public class Main {
    public static void main(String[] args) {
        String name = "Madhav";
        name.nonExistingMethod();
        System.out.println(name);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1

    exp = data["errors"][0]["explanation"]
    assert exp is not None
    assert exp["fix_available"] is False
    assert exp["validated"] is False
    assert exp["corrected_code"] is None
    assert "Automatic fix is not available" in exp["fix_explanation"] or "does not exist" in exp["fix_explanation"]
