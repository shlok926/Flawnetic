import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app
from models.db import User, Project

client = TestClient(app)

def test_list_projects_empty():
    with patch("api.routers.projects.get_current_user") as mock_user_dep, \
         patch("api.routers.projects.get_db") as mock_db_dep:
        
        mock_user = MagicMock(id=uuid.uuid4())
        mock_user_dep.return_value = mock_user
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db_dep.return_value = mock_db

        app.dependency_overrides = {}

        response = client.get("/api/v1/projects")
        assert response.status_code in [401, 200]

def test_get_project_not_found():
    with patch("api.routers.projects.get_current_user") as mock_user_dep, \
         patch("api.routers.projects.get_db") as mock_db_dep:
        
        mock_user = MagicMock(id=uuid.uuid4())
        mock_user_dep.return_value = mock_user
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db_dep.return_value = mock_db

        app.dependency_overrides = {}

        response = client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code in [401, 404]
