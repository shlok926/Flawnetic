import pytest
from observability.tracing import generate_trace_id, generate_span_id, start_trace_span

def test_opentelemetry_tracing_generation():
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    assert len(trace_id) == 32  # 128-bit hex
    assert len(span_id) == 16   # 64-bit hex

def test_start_trace_span_context():
    with start_trace_span("test_scan_engine", {"engine": "security"}) as span:
        assert span["span_name"] == "test_scan_engine"
        assert span["attributes"]["engine"] == "security"
        assert len(span["trace_id"]) == 32
        assert len(span["span_id"]) == 16
