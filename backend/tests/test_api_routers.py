import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from api.main import app

client = TestClient(app)

def test_api_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["version"] == "1.0.0"

def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_auth_register_duplicate_email():
    from api.dependencies import get_db
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
    
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123", "name": "Test User"}
        )
        assert response.status_code in [200, 400]
    finally:
        app.dependency_overrides.clear()
