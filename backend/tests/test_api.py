from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_type_mismatch():
    code = """public class Main {
    public static void main(String[] args) {
        int age = "20";
        System.out.println(age);
    }
}"""
    response = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert len(data["errors"]) >= 1
    err0 = data["errors"][0]
    assert err0["error"]["line"] == 3
    assert err0["classification"]["category"] == "TYPE_ERROR"
    assert "explanation" in err0
    assert err0["explanation"]["title"] == "Type Mismatch"
    assert "submission_id" in data


def test_analyze_clean_code():
    code = """public class Main {
    public static void main(String[] args) {
        int x = 10;
        int y = 20;
        System.out.println(x + y);
    }
}"""
    response = client.post("/api/analyze", json={"language": "java", "source_code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["errors"]) == 0


def test_history_and_insights_pipeline():
    # Fetch history
    h_res = client.get("/api/history")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["total"] >= 2

    # Fetch detail for first submission
    sub_id = h_data["submissions"][0]["id"]
    det_res = client.get(f"/api/history/{sub_id}")
    assert det_res.status_code == 200

    # Fetch insights
    i_res = client.get("/api/insights")
    assert i_res.status_code == 200
    i_data = i_res.json()
    assert i_data["total_submissions"] >= 2
    assert i_data["total_errors"] >= 1
    assert len(i_data["category_distribution"]) > 0
    assert len(i_data["recommendations"]) > 0
