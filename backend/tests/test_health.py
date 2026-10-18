from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "CodeSense" in data["message"]
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["app"] == "CodeSense"
    assert "compiler" in data
    assert "available" in data["compiler"]
    # Verify javac is found on this environment
    assert data["compiler"]["available"] is True
    assert "javac" in data["compiler"]["version"]
