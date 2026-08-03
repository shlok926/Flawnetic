import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_db, get_current_user
from models.db import User, Project

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(id=uuid.uuid4(), email="user@example.com", name="Test User")

def test_create_project_success(mock_user):
    mock_db = MagicMock()
    mock_proj = Project(id=uuid.uuid4(), user_id=mock_user.id, name="New Proj", base_url="https://example.com", created_at=datetime.utcnow())
    mock_db.refresh.side_effect = lambda obj: setattr(obj, 'created_at', datetime.utcnow())

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.post("/api/v1/projects", json={"name": "New Proj", "base_url": "https://example.com"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Proj"
        assert resp.json()["base_url"] == "https://example.com"
        assert mock_db.add.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()

def test_list_projects_success(mock_user):
    mock_db = MagicMock()
    mock_proj = Project(id=uuid.uuid4(), user_id=mock_user.id, name="P1", base_url="https://example.com", created_at=datetime.utcnow())
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_proj]

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "P1"
    finally:
        app.dependency_overrides.clear()

def test_get_project_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        proj_id = uuid.uuid4()
        resp = client.get(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"
    finally:
        app.dependency_overrides.clear()

def test_get_project_success(mock_user):
    mock_db = MagicMock()
    proj_id = uuid.uuid4()
    mock_proj = Project(id=proj_id, user_id=mock_user.id, name="Target Proj", base_url="https://target.com", created_at=datetime.utcnow())
    mock_db.query.return_value.filter.return_value.first.return_value = mock_proj

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        resp = client.get(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Target Proj"
    finally:
        app.dependency_overrides.clear()
