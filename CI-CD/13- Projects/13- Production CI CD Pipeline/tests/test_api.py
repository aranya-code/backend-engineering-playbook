from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").status_code == 200

def test_version():
    assert client.get("/version").json()["version"] == "0.1.0"
