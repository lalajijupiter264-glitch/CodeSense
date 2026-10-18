from app.compiler.java_compiler import JavaCompilerService

compiler = JavaCompilerService()


def test_compiler_availability():
    assert compiler.is_available() is True
    assert compiler.language == "java"


def test_compiler_success():
    code = """
public class Main {
    public static void main(String[] args) {
        int x = 10;
        int y = 20;
        System.out.println(x + y);
    }
}
"""
    result = compiler.compile(code)
    assert result.success is True
    assert result.exit_code == 0
    assert result.compilation_time_ms > 0


def test_compiler_syntax_error():
    code = """
public class Main {
    public static void main(String[] args) {
        int x = 10
        System.out.println(x);
    }
}
"""
    result = compiler.compile(code)
    assert result.success is False
    assert result.exit_code != 0
    assert "error: ';' expected" in result.stderr or "';' expected" in result.stderr
    # Server temp directories must NOT be exposed in stderr
    assert "codesense_java_" not in result.stderr
