import pytest
from unittest.mock import MagicMock, patch

from workers.tasks import _run_module_safely, _get_ai_hint, run_scan
from models.db import ScanStatusEnum

def test_failure_injection_engine_module_crash():
    def failing_module():
        raise RuntimeError("Fatal engine crashed due to network timeout")

    res = _run_module_safely("failing_security_engine", failing_module)
    assert res == []

def test_failure_injection_claude_api_timeout():
    mock_ai_analyzer = MagicMock()
    mock_ai_analyzer.analyze_finding.side_effect = TimeoutError("Claude API timeout")

    with patch("workers.tasks.settings") as mock_settings:
        mock_settings.anthropic_api_key = "valid-key-123"
        hint = _get_ai_hint(mock_ai_analyzer, "SQLi", "Description", {})
        assert hint is None

def test_failure_injection_db_connection_down():
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("PostgreSQL connection refused")

    with patch("workers.tasks.SessionLocal", return_value=mock_db):
        run_scan("scan-db-failed")
        assert mock_db.close.called
