import pytest
from unittest.mock import MagicMock, patch
from workers.tasks import _run_module_safely

def test_run_module_safely_success():
    def mock_fn(val):
        return [{"module": "test", "title": "Test Finding"}]

    res = _run_module_safely("test_module", mock_fn, val="hello")
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["title"] == "Test Finding"

def test_run_module_safely_exception_isolation():
    def failing_fn():
        raise RuntimeError("Module engine crashed unexpectedly")

    # Module failure should be caught safely, returning empty list without breaking worker
    res = _run_module_safely("failing_module", failing_fn)
    assert isinstance(res, list)
    assert len(res) == 0

@patch("workers.tasks.SessionLocal")
def test_run_scan_task_not_found(mock_session_local):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    from workers.tasks import run_scan
    # Non-existent scan run id should return None without crashing worker
    res = run_scan("non-existent-id")
    assert res is None
