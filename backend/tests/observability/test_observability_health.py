from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_live_endpoint():
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"

def test_health_ready_endpoint():
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"

def test_health_dependencies_endpoint():
    resp = client.get("/health/dependencies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "postgresql" in data["dependencies"]
    assert "redis" in data["dependencies"]
    assert "minio_s3" in data["dependencies"]
    assert "celery" in data["dependencies"]
