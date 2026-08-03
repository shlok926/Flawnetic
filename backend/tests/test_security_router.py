import pytest
from fastapi.testclient import TestClient
from api.main import app
from config.settings import settings

client = TestClient(app)

def test_cors_origin_restriction():
    # Unauthorized origin should not receive Access-Control-Allow-Origin header
    response = client.options(
        "/api/v1/auth/register",
        headers={"Origin": "http://malicious-attacker.com", "Access-Control-Request-Method": "POST"}
    )
    assert response.headers.get("access-control-allow-origin") != "http://malicious-attacker.com"
    assert response.headers.get("access-control-allow-origin") != "*"

def test_cors_allowed_origin():
    # Configured frontend origin should be permitted
    allowed_origin = settings.frontend_url.split(",")[0].strip()
    response = client.options(
        "/api/v1/auth/register",
        headers={"Origin": allowed_origin, "Access-Control-Request-Method": "POST"}
    )
    assert response.headers.get("access-control-allow-origin") == allowed_origin

def test_websocket_missing_auth_token():
    # WebSocket connection without token parameter must be rejected
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/scans/test-scan-id") as websocket:
            pass

def test_websocket_invalid_auth_token():
    # WebSocket connection with invalid token must be rejected
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/scans/test-scan-id?token=invalid.jwt.token") as websocket:
            pass
