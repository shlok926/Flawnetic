from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_correlation_id_propagation_middleware():
    custom_corr_id = "corr-test-unique-12345"
    resp = client.get("/", headers={"X-Correlation-ID": custom_corr_id})

    assert resp.status_code == 200
    assert resp.headers.get("X-Correlation-ID") == custom_corr_id
    assert "X-Request-ID" in resp.headers
    assert "X-Trace-ID" in resp.headers
    assert "X-Span-ID" in resp.headers
