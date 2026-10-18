from app.analyzers.static_analyzer import JavaStaticAnalyzer

analyzer = JavaStaticAnalyzer()


def test_unused_variable_detected():
    code = """public class Main {
    public static void main(String[] args) {
        int unusedValue = 42;
        System.out.println("Hello");
    }
}"""
    warnings = analyzer.analyze(code)
    rule_ids = [w.rule_id for w in warnings]
    assert "UNUSED_VARIABLE" in rule_ids
    var_warn = next(w for w in warnings if w.rule_id == "UNUSED_VARIABLE")
    assert "unusedValue" in var_warn.message
    assert var_warn.line == 3


def test_empty_catch_detected():
    code = """public class Main {
    public static void main(String[] args) {
        try {
            int x = 10 / 0;
        } catch (Exception e) {}
    }
}"""
    warnings = analyzer.analyze(code)
    rule_ids = [w.rule_id for w in warnings]
    assert "EMPTY_CATCH_BLOCK" in rule_ids


def test_string_equals_comparison():
    code = """public class Main {
    public static void main(String[] args) {
        String name = "Alice";
        if (name == "Alice") {
            System.out.println("Match");
        }
    }
}"""
    warnings = analyzer.analyze(code)
    rule_ids = [w.rule_id for w in warnings]
    assert "STRING_EQUALS_CHECK" in rule_ids


def test_infinite_loop_warning():
    code = """public class Main {
    public static void main(String[] args) {
        while (true) {
            System.out.println("Running");
        }
    }
}"""
    warnings = analyzer.analyze(code)
    rule_ids = [w.rule_id for w in warnings]
    assert "INFINITE_LOOP" in rule_ids
