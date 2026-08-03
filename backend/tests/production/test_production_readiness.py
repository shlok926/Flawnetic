from fastapi.testclient import TestClient
from api.main import app
from scripts.disaster_recovery import dr_manager

client = TestClient(app)

def test_production_security_headers():
    resp = client.get("/health/live")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
    assert headers.get("Content-Security-Policy") == "default-src 'self'"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_production_telemetry_headers():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "X-Correlation-ID" in resp.headers
    assert "X-Request-ID" in resp.headers
    assert "X-Trace-ID" in resp.headers

def test_disaster_recovery_snapshot_creation_and_restore_verification():
    res = dr_manager.create_backup_snapshot()
    assert res["status"] == "SUCCESS"
    backup_filepath = res["backup_file"]

    is_valid = dr_manager.verify_restore_procedure(backup_filepath)
    assert is_valid is True
