from fastapi.testclient import TestClient
from api.main import app
from observability.metrics import metrics_registry

client = TestClient(app)

def test_metrics_taxonomy_endpoint():
    metrics_registry.inc_counter("scans_started_total")
    metrics_registry.observe_histogram("api_request_duration_ms", 12.5)

    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "system_metrics" in data
    assert "application_metrics" in data
    assert "business_metrics" in data
    assert "ai_metrics" in data
