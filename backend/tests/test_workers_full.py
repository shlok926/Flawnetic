import pytest
import uuid
import dataclasses
from unittest.mock import MagicMock, patch
from workers.tasks import _run_module_safely, _get_ai_hint, run_scan
from models.db import ScanRun, ScanStatusEnum, Project, Page, Finding

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

    res = _run_module_safely("failing_module", failing_fn)
    assert isinstance(res, list)
    assert len(res) == 0

def test_get_ai_hint_fallback():
    hint = _get_ai_hint(None, "SQLi Title", "SQLi Desc", {})
    assert hint is None

@patch("workers.tasks.SessionLocal")
def test_run_scan_task_not_found(mock_session_local):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_local.return_value = mock_db

    res = run_scan("non-existent-id")
    assert res is None

@patch("workers.tasks.PDFReportGenerator")
@patch("workers.tasks.AITriageEngine")
@patch("workers.tasks.FlawneticCrawler")
@patch("workers.tasks.SessionLocal")
def test_run_scan_full_execution(mock_session_local, mock_crawler_cls, mock_triage_cls, mock_report_cls):
    scan_id = uuid.uuid4()
    project_id = uuid.uuid4()
    
    mock_scan_run = MagicMock(
        id=scan_id, 
        project_id=project_id, 
        config={"modules": ["functional", "security", "accessibility", "usability", "visual"]}, 
        status=ScanStatusEnum.queued
    )
    mock_project = MagicMock(id=project_id, base_url="https://demo.example.com", name="Demo Project")
    mock_page = MagicMock(id=uuid.uuid4(), url="https://demo.example.com/", scan_run_id=scan_id, screenshot_url="/tmp/shot.png")
    mock_finding = MagicMock(
        title="Sanitization Flaw",
        description="Missing encoding",
        severity=MagicMock(name="HIGH"),
        module=MagicMock(name="functional"),
        steps_to_reproduce=None,
        expected_result=None,
        actual_result=None,
        root_cause_hint=None,
        page_id=mock_page.id
    )

    mock_db = MagicMock()
    
    # Query builder helper
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.side_effect = [mock_scan_run, mock_project, mock_page, None]
    mock_query.all.return_value = [mock_page]
    mock_query.count.return_value = 1

    mock_db.query.return_value = mock_query
    mock_session_local.return_value = mock_db

    # Mock Crawler site graph
    mock_page_node = MagicMock(url="https://demo.example.com/", title="Home", http_status=200, screenshot_path="/tmp/shot.png")
    mock_site_graph = MagicMock(total_pages=1, pages=[mock_page_node])
    
    mock_crawler = MagicMock()
    mock_crawler.crawl.return_value = mock_site_graph
    mock_crawler_cls.return_value = mock_crawler

    # Mock PDF report & triage engine
    mock_triage = MagicMock()
    mock_triage.triage.return_value = [{
        "title": "Sanitization Flaw",
        "severity": "HIGH",
        "module": "functional",
        "page_url": "https://demo.example.com/"
    }]
    mock_triage_cls.return_value = mock_triage

    mock_report = MagicMock()
    mock_report.generate_and_upload.return_value = "http://localhost:9000/reports/test.pdf"
    mock_report_cls.return_value = mock_report

    sample_res = [{"title": "Test Flaw", "description": "Test Desc", "severity": "high", "priority": "high"}]

    with patch("workers.tasks.asyncio.run") as mock_asyncio_run, \
         patch("workers.tasks.FunctionalEngine") as mock_func_engine_cls, \
         patch("workers.tasks.SecurityEngine") as mock_sec_engine_cls, \
         patch("workers.tasks.AccessibilityEngine") as mock_a11y_engine_cls, \
         patch("workers.tasks.UsabilityEngine") as mock_usab_engine_cls, \
         patch("workers.tasks.VisualEngine") as mock_vis_engine_cls, \
         patch("httpx.head") as mock_httpx_head:
        
        mock_asyncio_run.return_value = mock_site_graph
        mock_httpx_resp = MagicMock(status_code=404)
        mock_httpx_head.return_value = mock_httpx_resp

        mock_func_engine_cls.return_value.analyze_and_test.return_value = sample_res
        mock_sec_engine_cls.return_value.run_zap_dast_scan.return_value = sample_res
        mock_a11y_engine_cls.return_value.scan_page.return_value = sample_res
        mock_usab_engine_cls.return_value.analyze_page.return_value = sample_res
        mock_vis_engine_cls.return_value.audit_visual_rendering.return_value = sample_res

        run_scan(str(scan_id))
        
        assert mock_db.commit.called
