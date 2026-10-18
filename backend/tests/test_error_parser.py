from app.compiler.error_parser import JavaErrorParser

parser = JavaErrorParser()


def test_parse_type_mismatch():
    sample_stderr = """Main.java:3: error: incompatible types: java.lang.String cannot be converted to int
        int age = "20";
                  ^
1 error
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 1
    err = errors[0]
    assert err.file == "Main.java"
    assert err.line == 3
    assert err.severity == "error"
    assert err.compiler_code == "INCOMPATIBLE_TYPES"
    assert "cannot be converted to int" in err.message
    assert err.is_primary is True
    assert err.column == 19


def test_parse_missing_semicolon():
    sample_stderr = """Main.java:4: error: ';' expected
        System.out.println(age)
                               ^
1 error
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 1
    err = errors[0]
    assert err.line == 4
    assert err.compiler_code == "SEMICOLON_EXPECTED"


def test_parse_multiple_errors():
    sample_stderr = """Main.java:3: error: incompatible types: java.lang.String cannot be converted to int
        int age = "20";
                  ^
Main.java:4: error: ';' expected
        System.out.println(age)
                               ^
2 errors
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 2
    assert errors[0].line == 3
    assert errors[0].compiler_code == "INCOMPATIBLE_TYPES"
    assert errors[0].is_primary is True

    assert errors[1].line == 4
    assert errors[1].compiler_code == "SEMICOLON_EXPECTED"
    assert errors[1].is_primary is False


def test_parse_cannot_find_symbol():
    sample_stderr = """Main.java:3: error: cannot find symbol
        System.out.println(value);
                           ^
  symbol:   variable value
  location: class Main
1 error
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 1
    err = errors[0]
    assert err.compiler_code == "CANNOT_FIND_SYMBOL"
    assert err.symbol == "variable value"
    assert err.location == "class Main"


def test_parse_division_by_zero():
    sample_stderr = """Main.java:3: warning: [divzero] division by zero
        int s = 10 / 0;
                     ^
1 warning
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 1
    err = errors[0]
    assert err.line == 3
    assert err.column == 22
    assert err.compiler_code == "DIVISION_BY_ZERO"
    assert err.severity == "error"
    assert "division by zero" in err.message.lower()


def test_parse_division_by_zero_suppresses_duplicate_not_a_statement():
    sample_stderr = """Main.java:3: warning: [divzero] division by zero
        int s = 10 / 0;
                     ^
Main.java:3: error: not a statement
        int s = 10 / 0;
           ^
1 error
1 warning
"""
    errors = parser.parse(sample_stderr)
    assert len(errors) == 1
    assert errors[0].compiler_code == "DIVISION_BY_ZERO"

