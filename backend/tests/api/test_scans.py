import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_db, get_current_user
from models.db import User, Project, ScanRun, ScanStatusEnum, Finding, Report

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(id=uuid.uuid4(), email="user@example.com", name="Test User")

def test_create_scan_project_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        project_id = uuid.uuid4()
        resp = client.post(f"/api/v1/projects/{project_id}/scans", json={"authorized": True})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"
    finally:
        app.dependency_overrides.clear()

def test_create_scan_unauthorized_flag(mock_user):
    mock_db = MagicMock()
    mock_project = Project(id=uuid.uuid4(), user_id=mock_user.id, name="Proj", base_url="https://example.com")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.post(f"/api/v1/projects/{mock_project.id}/scans", json={"authorized": False})
        assert resp.status_code == 403
        assert resp.json()["detail"] == "You must authorize the scan"
    finally:
        app.dependency_overrides.clear()

@patch("api.routers.scans.run_scan.delay")
def test_create_scan_success(mock_run_scan_delay, mock_user):
    mock_db = MagicMock()
    mock_project = Project(id=uuid.uuid4(), user_id=mock_user.id, name="Proj", base_url="https://example.com")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.post(f"/api/v1/projects/{mock_project.id}/scans", json={"authorized": True, "modules": ["functional"]})
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
        assert mock_run_scan_delay.called
    finally:
        app.dependency_overrides.clear()

def test_get_scan_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        run_id = uuid.uuid4()
        resp = client.get(f"/api/v1/scans/{run_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scan run not found"
    finally:
        app.dependency_overrides.clear()

def test_get_scan_success(mock_user):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id=uuid.uuid4(), project_id=uuid.uuid4(), status="done", config={})
    mock_scan_run.created_at = "2026-08-03T12:00:00"
    mock_scan_run.summary = {"total_findings": 0}
    mock_scan_run.site_graph = None

    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_scan_run

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get(f"/api/v1/scans/{mock_scan_run.id}")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()

def test_get_findings_scan_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        run_id = uuid.uuid4()
        resp = client.get(f"/api/v1/scans/{run_id}/findings")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()

def test_get_findings_success_filtered(mock_user):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id=uuid.uuid4())
    mock_finding = MagicMock(
        id=uuid.uuid4(), scan_run_id=mock_scan_run.id, page_id=uuid.uuid4(),
        module="functional", title="XSS", description="Found XSS",
        severity="high", priority="high", steps_to_reproduce={},
        expected_result=None, actual_result=None, root_cause_hint=None,
        created_at="2026-08-03T12:00:00"
    )

    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_scan_run
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_finding]

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get(f"/api/v1/scans/{mock_scan_run.id}/findings?severity=high&module=functional")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()

def test_get_report_not_ready(mock_user):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id=uuid.uuid4())
    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_scan_run
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get(f"/api/v1/scans/{mock_scan_run.id}/report")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Report not ready or failed to generate"
    finally:
        app.dependency_overrides.clear()

def test_get_report_success(mock_user):
    mock_db = MagicMock()
    mock_scan_run = MagicMock(id=uuid.uuid4())
    mock_report = Report(id=uuid.uuid4(), scan_run_id=mock_scan_run.id, pdf_url="http://minio:9000/r1.pdf")

    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_scan_run
    mock_db.query.return_value.filter.return_value.first.return_value = mock_report

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get(f"/api/v1/scans/{mock_scan_run.id}/report")
        assert resp.status_code == 200
        assert resp.json() == {"pdf_url": "http://minio:9000/r1.pdf"}
    finally:
        app.dependency_overrides.clear()
