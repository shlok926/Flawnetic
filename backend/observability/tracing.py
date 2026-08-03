import uuid
from typing import Dict, Optional, Any
from contextlib import contextmanager

from observability.logging import trace_id_var, span_id_var, correlation_id_var

def generate_trace_id() -> str:
    """Generate 128-bit hex trace ID compatible with OpenTelemetry."""
    return uuid.uuid4().hex

def generate_span_id() -> str:
    """Generate 64-bit hex span ID compatible with OpenTelemetry."""
    return uuid.uuid4().hex[:16]

@contextmanager
def start_trace_span(span_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    OpenTelemetry-compatible trace span context manager.
    Updates trace_id_var and span_id_var context variables.
    """
    current_trace_id = trace_id_var.get() or generate_trace_id()
    parent_span_id = span_id_var.get()
    new_span_id = generate_span_id()

    token_trace = trace_id_var.set(current_trace_id)
    token_span = span_id_var.set(new_span_id)

    try:
        yield {
            "trace_id": current_trace_id,
            "span_id": new_span_id,
            "parent_span_id": parent_span_id,
            "span_name": span_name,
            "attributes": attributes or {}
        }
    finally:
        trace_id_var.reset(token_trace)
        span_id_var.reset(token_span)
