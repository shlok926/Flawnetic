import pytest
import time
import statistics
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

def test_api_root_latency_benchmark():
    # Statistical methodology: 5 warm-up, 30 measured runs
    for _ in range(5):
        client.get("/")

    latencies_ms = []
    for _ in range(30):
        start = time.perf_counter()
        resp = client.get("/")
        duration = (time.perf_counter() - start) * 1000.0
        assert resp.status_code == 200
        latencies_ms.append(duration)

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)]

    # Budget: P99 <= 200ms
    assert p99 <= 200.0, f"API Root P99 latency exceeded budget: {p99:.2f}ms > 200ms"

def test_api_health_latency_benchmark():
    for _ in range(5):
        client.get("/health")

    latencies_ms = []
    for _ in range(30):
        start = time.perf_counter()
        resp = client.get("/health")
        duration = (time.perf_counter() - start) * 1000.0
        assert resp.status_code == 200
        latencies_ms.append(duration)

    latencies_ms.sort()
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]

    # Budget: P95 <= 100ms
    assert p95 <= 100.0, f"API Health P95 latency exceeded budget: {p95:.2f}ms > 100ms"
