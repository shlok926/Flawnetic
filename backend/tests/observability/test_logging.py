import json
import logging
from observability.logging import JSONLogFormatter, SCHEMA_VERSION

def test_json_log_formatter_schema_v1():
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["schema_version"] == SCHEMA_VERSION
    assert data["level"] == "INFO"
    assert data["message"] == "Test log message"
    assert "correlation_id" in data
    assert "timestamp" in data
