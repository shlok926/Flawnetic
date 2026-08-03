import json
import logging
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variables for request-level & task-level tracing
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
scan_id_var: ContextVar[Optional[str]] = ContextVar("scan_id", default=None)
project_id_var: ContextVar[Optional[str]] = ContextVar("project_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

SCHEMA_VERSION = "1.0"

class JSONLogFormatter(logging.Formatter):
    """
    Enterprise Structured JSON Log Formatter (Schema v1.0).
    OpenTelemetry-compatible with trace_id, span_id, and correlation_id context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get() or getattr(record, "correlation_id", None) or str(uuid.uuid4()),
            "trace_id": trace_id_var.get() or getattr(record, "trace_id", None),
            "span_id": span_id_var.get() or getattr(record, "span_id", None),
            "request_id": request_id_var.get() or getattr(record, "request_id", None),
            "scan_id": scan_id_var.get() or getattr(record, "scan_id", None),
            "project_id": project_id_var.get() or getattr(record, "project_id", None),
            "user_id": user_id_var.get() or getattr(record, "user_id", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Attach extra fields if present
        for key in ["duration_ms", "status", "engine_name", "error_code", "retry_count"]:
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        if record.exc_info:
            log_entry["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_entry["stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_structured_logging():
    """Setup root logger with JSONLogFormatter."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
