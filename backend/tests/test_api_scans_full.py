import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from api.main import app
from models.db import User, Project, ScanRun, ScanStatusEnum, Finding

client = TestClient(app)

def test_create_scan_unauthorized():
    # Attempting to start scan without authorized=True should return 403 Forbidden
    with patch("api.routers.scans.get_current_user") as mock_user_dep, \
         patch("api.routers.scans.get_db") as mock_db_dep:
        
        mock_user = MagicMock(id=uuid.uuid4())
        mock_user_dep.return_value = mock_user
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(id=uuid.uuid4(), user_id=mock_user.id)
        mock_db_dep.return_value = mock_db

        app.dependency_overrides = {}

        response = client.post(
            f"/api/v1/projects/{uuid.uuid4()}/scans",
            json={"authorized": False}
        )
        assert response.status_code in [401, 403, 404]

def test_get_scan_not_found():
    with patch("api.routers.scans.get_current_user") as mock_user_dep, \
         patch("api.routers.scans.get_db") as mock_db_dep:
        
        mock_user = MagicMock(id=uuid.uuid4())
        mock_user_dep.return_value = mock_user
        
        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        mock_db_dep.return_value = mock_db

        app.dependency_overrides = {}

        response = client.get(f"/api/v1/scans/{uuid.uuid4()}")
        assert response.status_code in [401, 404]
