import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from engines.crawler.models import SiteGraph, PageNode
from models.db import ScanRun, ScanStatusEnum, Project, Page, Finding, ModuleEnum, SeverityEnum, Report
from workers.tasks import run_scan, _run_module_safely, _get_ai_hint

def test_run_module_safely_success():
    def mock_fn(x):
        return [{"title": "Flaw 1"}]

    res = _run_module_safely("test_mod", mock_fn, 1)
    assert res == [{"title": "Flaw 1"}]

def test_run_module_safely_failure():
    def mock_fn():
        raise RuntimeError("Module crashed")

    res = _run_module_safely("failing_mod", mock_fn)
    assert res == []

def test_get_ai_hint_disabled_key():
    ai_analyzer = MagicMock()
    with patch("workers.tasks.settings") as mock_settings:
        mock_settings.anthropic_api_key = ""
        hint = _get_ai_hint(ai_analyzer, "Title", "Desc", {})
        assert hint is None

def test_get_ai_hint_none_analyzer():
    hint = _get_ai_hint(None, "Title", "Desc", {})
    assert hint is None

@patch("workers.tasks.asyncio.run")
def test_get_ai_hint_success(mock_async_run):
    ai_analyzer = MagicMock()
    mock_async_run.return_value = "Root Cause Analysis Hint"
    with patch("workers.tasks.settings") as mock_settings:
        mock_settings.anthropic_api_key = "valid-key-123"
        hint = _get_ai_hint(ai_analyzer, "Title", "Desc", {})
        assert hint == "Root Cause Analysis Hint"

@patch("workers.tasks.SessionLocal")
def test_run_scan_non_existent_scan_run(mock_session_factory):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_factory.return_value = mock_db

    run_scan("invalid-id")
    mock_db.close.assert_called_once()

@patch("workers.tasks.SessionLocal")
def test_run_scan_non_existent_project(mock_session_factory):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id="scan-1", project_id="proj-1", config={})
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scan_run, None]
    mock_session_factory.return_value = mock_db

    run_scan("scan-1")
    assert mock_scan_run.status == ScanStatusEnum.crawling

@patch("workers.tasks.PDFReportGenerator")
@patch("workers.tasks.AITriageEngine")
@patch("workers.tasks.FlawneticCrawler")
@patch("workers.tasks.FunctionalEngine")
@patch("workers.tasks.SecurityEngine")
@patch("workers.tasks.AccessibilityEngine")
@patch("workers.tasks.UsabilityEngine")
@patch("workers.tasks.VisualEngine")
@patch("workers.tasks.SessionLocal")
def test_run_scan_full_pipeline_success(
    mock_session_factory,
    mock_vis_eng,
    mock_usab_eng,
    mock_a11y_eng,
    mock_sec_eng,
    mock_func_eng,
    mock_crawler_cls,
    mock_triage_cls,
    mock_report_cls
):
    mock_db = MagicMock()
    mock_session_factory.return_value = mock_db

    mock_project = MagicMock(id="proj-1", base_url="https://example.com", name="Test Proj")
    mock_scan_run = MagicMock(id="scan-1", project_id="proj-1", config={"modules": ["functional", "security", "accessibility", "usability", "visual"]})
    mock_page = MagicMock(id="page-1", url="https://example.com/page1", title="Page 1", http_status=200, screenshot_url="/tmp/p1.png")

    def mock_first():
        return mock_scan_run

    def mock_query(model):
        query_mock = MagicMock()
        if model == ScanRun:
            query_mock.filter.return_value.first.return_value = mock_scan_run
        elif model == Project:
            query_mock.filter.return_value.first.return_value = mock_project
        elif model == Page:
            query_mock.filter.return_value.all.return_value = [mock_page]
            query_mock.filter.return_value.first.return_value = mock_page
            query_mock.filter.return_value.count.return_value = 1
        elif model == Finding:
            mock_finding = MagicMock(
                title="XSS Vulnerability", description="Reflected XSS", severity=SeverityEnum.high,
                module=ModuleEnum.functional, steps_to_reproduce={}, expected_result="Clean",
                actual_result="Alert", root_cause_hint="Fix HTML escape", page_id="page-1"
            )
            query_mock.filter.return_value.all.return_value = [mock_finding]
        return query_mock

    mock_db.query.side_effect = mock_query

    page_node = PageNode(
        url="https://example.com/page1",
        title="Page 1",
        http_status=200,
        depth=1,
        discovered_via="root",
        screenshot_path="/tmp/p1.png",
        elements=[]
    )
    site_graph = SiteGraph(
        base_url="https://example.com",
        pages=[page_node],
        total_pages=1,
        max_depth_reached=1,
        crawl_duration_seconds=0.5
    )
    
    mock_crawler = MagicMock()
    mock_crawler.crawl = AsyncMock(return_value=site_graph)
    mock_crawler_cls.return_value = mock_crawler

    # Mock engine results
    mock_func_eng.return_value.analyze_and_test = AsyncMock(return_value=[
        {"title": "XSS Vulnerability", "description": "Reflected XSS", "severity": "high", "priority": "high", "steps_to_reproduce": {}, "expected_result": "Clean", "actual_result": "Alert"}
    ])
    mock_sec_eng.return_value.run_zap_dast_scan = AsyncMock(return_value=[
        {"title": "Header Missing", "description": "Missing HSTS", "severity": "medium", "priority": "medium"}
    ])
    mock_a11y_eng.return_value.scan_page = AsyncMock(return_value=[
        {"title": "Contrast Low", "description": "Low Contrast", "severity": "low", "priority": "low"}
    ])
    mock_usab_eng.return_value.analyze_page = AsyncMock(return_value=[
        {"title": "Missing Alt", "description": "No alt text", "severity": "low", "priority": "low"}
    ])
    mock_vis_eng.return_value.audit_visual_rendering = AsyncMock(return_value=[
        {"title": "Visual Mismatch", "description": "Layout shifted", "severity": "medium", "priority": "medium"}
    ])

    mock_triage = MagicMock()
    mock_triage.triage.return_value = [{"title": "XSS Vulnerability", "severity": "HIGH"}]
    mock_triage_cls.return_value = mock_triage

    mock_report_gen = MagicMock()
    mock_report_gen.generate_and_upload.return_value = "http://minio:9000/reports/r1.pdf"
    mock_report_cls.return_value = mock_report_gen

    with patch("httpx.head") as mock_httpx_head:
        mock_httpx_resp = MagicMock(status_code=200)
        mock_httpx_head.return_value = mock_httpx_resp

        run_scan("scan-1")

    assert mock_scan_run.status == ScanStatusEnum.done
    assert mock_scan_run.summary["pdf_url"] == "http://minio:9000/reports/r1.pdf"
    assert mock_scan_run.summary["total_findings"] == 1

@patch("workers.tasks.SessionLocal")
def test_run_scan_unhandled_exception(mock_session_factory):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id="scan-1", project_id="proj-1", config={})
    mock_db.query.return_value.filter.return_value.first.side_effect = Exception("Database connection dead")
    mock_session_factory.return_value = mock_db

    run_scan("scan-1")
    assert mock_db.close.called
