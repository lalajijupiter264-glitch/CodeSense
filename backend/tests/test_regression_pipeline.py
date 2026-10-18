import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.compiler.java_compiler import JavaCompilerService
from app.compiler.error_parser import JavaErrorParser

client = TestClient(app)


def test_regression_1_valid_java_code():
    """1. Valid Java code using 10 / 2 compiles cleanly with zero errors."""
    code = """public class Main {
    public static void main(String[] args) {
        int s = 10 / 2;
        System.out.println(s);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["exit_code"] == 0
    assert len(data["errors"]) == 0
    assert "success" in data["summary_message"].lower()


def test_regression_2_division_by_zero():
    """2. Constant division by zero (int s = 10 / 0;) produces a division-by-zero diagnostic."""
    code = """public class Main {
    public static void main(String[] args) {
        int s = 10 / 0;
        System.out.println(s);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    codes = [e["error"]["compiler_code"] for e in data["errors"]]
    assert "DIVISION_BY_ZERO" in codes


def test_regression_3_type_mismatch():
    """3. Type mismatch (int age = "twenty";) produces an incompatible-types diagnostic."""
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
    assert data["exit_code"] == 1
    assert len(data["errors"]) >= 1
    codes = [e["error"]["compiler_code"] for e in data["errors"]]
    assert "INCOMPATIBLE_TYPES" in codes
    assert data["errors"][0]["error"]["line"] == 3


def test_regression_4_undefined_variable():
    """4. Undefined variable produces a cannot-find-symbol diagnostic."""
    code = """public class Main {
    public static void main(String[] args) {
        System.out.println(unknownVariable);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["exit_code"] == 1
    assert len(data["errors"]) >= 1
    codes = [e["error"]["compiler_code"] for e in data["errors"]]
    assert "CANNOT_FIND_SYMBOL" in codes


def test_regression_5_missing_semicolon():
    """5. Missing semicolon produces a semicolon-expected diagnostic."""
    code = """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello")
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    codes = [e["error"]["compiler_code"] for e in data["errors"]]
    assert "SEMICOLON_EXPECTED" in codes


def test_regression_6_multiple_independent_compiler_errors():
    """6. Multiple independent compiler errors are each parsed and returned."""
    code = """public class Main {
    public static void main(String[] args) {
        int age = "twenty"
        System.out.println(unknownVar)
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 2


def test_regression_7_empty_source_code():
    """7. Empty source code is rejected cleanly with 422 Unprocessable Entity."""
    res = client.post("/api/analyze", json={"language": "java", "source_code": ""})
    assert res.status_code == 422
    assert "source_code" in str(res.json())


def test_regression_8_missing_java_compiler():
    """8. Missing Java compiler returns structured infrastructure failure."""
    fake_compiler = JavaCompilerService(compiler_path="nonexistent_javac_executable_12345")
    assert fake_compiler.is_available() is False
    result = fake_compiler.compile("public class Main {}")
    assert result.success is False
    assert result.exit_code == -1
    assert result.error_message == "COMPILER_UNAVAILABLE"


def test_regression_9_compiler_subprocess_timeout(monkeypatch):
    """9. Controlled subprocess timeout cleanly aborts and reports timeout."""
    import subprocess
    compiler = JavaCompilerService()
    monkeypatch.setattr(compiler, "is_available", lambda: True)

    def fake_subprocess_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["javac"], timeout=0.01)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)
    result = compiler.compile("public class Main {}")
    assert result.success is False
    assert result.exit_code == -2
    assert result.error_message == "COMPILATION_TIMEOUT"
    assert "timed out" in result.stderr.lower()


def test_regression_10_unsupported_language_rejection():
    """10. Unsupported language requests are rejected with 400 Bad Request."""
    res = client.post("/api/analyze", json={"language": "cpp", "source_code": "int main() {}"})
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"].lower()


def test_regression_11_success_immediately_following_failure():
    """11. A successful request immediately following a failed request leaves no stale state."""
    # Failed request
    fail_code = """public class Main {
    public static void main(String[] args) {
        int x = "bad";
    }
}"""
    res_fail = client.post("/api/analyze", json={"language": "java", "source_code": fail_code})
    assert res_fail.status_code == 200
    assert res_fail.json()["success"] is False
    assert len(res_fail.json()["errors"]) >= 1

    # Immediately subsequent success request
    success_code = """public class Main {
    public static void main(String[] args) {
        int s = 10 / 2;
        System.out.println(s);
    }
}"""
    res_success = client.post("/api/analyze", json={"language": "java", "source_code": success_code})
    assert res_success.status_code == 200
    data = res_success.json()
    assert data["success"] is True
    assert data["exit_code"] == 0
    assert len(data["errors"]) == 0
    assert data["submission_id"] != res_fail.json()["submission_id"]


def test_regression_12_different_sources_produce_different_results():
    """12. Different source inputs produce distinctly different compiler diagnostics."""
    type_code = """public class Main {
    public static void main(String[] args) {
        int x = "text";
    }
}"""
    symbol_code = """public class Main {
    public static void main(String[] args) {
        System.out.println(ghost);
    }
}"""
    res_type = client.post("/api/analyze", json={"language": "java", "source_code": type_code}).json()
    res_symbol = client.post("/api/analyze", json={"language": "java", "source_code": symbol_code}).json()

    assert res_type["errors"][0]["error"]["compiler_code"] == "INCOMPATIBLE_TYPES"
    assert res_symbol["errors"][0]["error"]["compiler_code"] == "CANNOT_FIND_SYMBOL"
    assert res_type["errors"][0]["error"]["message"] != res_symbol["errors"][0]["error"]["message"]
