from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mandatory_case_1_missing_semicolon():
    """Test 1 - Missing semicolon."""
    code = """public class Main {
    public static void main(String[] args) {
        int x = 10
        System.out.println(x);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    err = data["errors"][0]
    assert err["error"]["line"] == 3
    assert err["classification"]["category"] == "SYNTAX_ERROR"
    assert "semicolon" in err["explanation"]["title"].lower() or "semicolon" in err["error"]["message"].lower()


def test_mandatory_case_2_type_mismatch():
    """Test 2 - Type mismatch."""
    code = """public class Main {
    public static void main(String[] args) {
        int x = "hello";
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    err = data["errors"][0]
    assert err["error"]["line"] == 3
    assert err["classification"]["category"] == "TYPE_ERROR"
    assert err["explanation"]["title"] == "Type Mismatch"


def test_mandatory_case_3_undefined_variable():
    """Test 3 - Undefined variable."""
    code = """public class Main {
    public static void main(String[] args) {
        System.out.println(value);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    err = data["errors"][0]
    assert err["error"]["line"] == 3
    assert err["classification"]["category"] == "VARIABLE_ERROR"


def test_mandatory_case_4_wrong_method_arguments():
    """Test 4 - Wrong method arguments."""
    code = """public class Main {
    public static void main(String[] args) {
        int result = Math.max(10);
        System.out.println(result);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    err = data["errors"][0]
    assert err["classification"]["category"] == "METHOD_ERROR"


def test_mandatory_case_5_correct_program():
    """Test 5 - Correct program."""
    code = """public class Main {
    public static void main(String[] args) {
        int x = 10;
        int y = 20;
        System.out.println(x + y);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["errors"]) == 0
    assert "success" in data["summary_message"].lower() or "clean" in data["summary_message"].lower()


def test_mandatory_case_6_multiple_errors():
    """Test 6 - Multiple independent errors simultaneously reported by compiler."""
    code = """public class Main {
    public static void main(String[] args) {
        int age = "20";
        System.out.println(undefinedVar);
    }
}"""
    res = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 2

    # Verify both errors are detected
    categories = [e["classification"]["category"] for e in data["errors"]]
    lines = [e["error"]["line"] for e in data["errors"]]

    assert "TYPE_ERROR" in categories
    assert "VARIABLE_ERROR" in categories
    assert 3 in lines
    assert 4 in lines
    assert data["primary_error"] is not None


def test_mandatory_case_7_division_by_zero():
    """Test 7 - Division by zero diagnostic (int s = 10 / 0;)."""
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
    assert len(data["errors"]) == 1
    err = data["errors"][0]
    assert err["error"]["line"] == 3
    assert err["error"]["column"] == 22
    assert err["classification"]["category"] == "ARITHMETIC_ERROR"
    assert err["classification"]["subcategory"] == "DIVISION_BY_ZERO"
    assert "division by zero" in err["error"]["message"].lower()
    assert err["explanation"]["title"] == "Division by Zero"
    assert "divide an integer by zero" in err["explanation"]["what_happened"].lower()
    assert "constant expression" in err["explanation"]["why_it_happened"].lower()
    assert "int s = 10 / 2;" in err["explanation"]["corrected_code"]
    assert err["explanation"]["fix_available"] is True
    assert err["explanation"]["validated"] is True


