import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from api.main import app
from config.settings import settings

@pytest.fixture
def test_client():
    """FastAPI TestClient fixture."""
    return TestClient(app)

@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy Session fixture."""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.filter.return_value.count.return_value = 0
    return session

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic Claude API client."""
    client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"deduplicated_findings": [], "summary": "Test Summary"}')]
    client.messages.create.return_value = mock_message
    return client

@pytest.fixture
def sample_findings():
    """Sample finding dictionaries fixture."""
    return [
        {
            "id": "f-1",
            "module": "security",
            "title": "SQL Injection Vulnerability",
            "description": "DB syntax error on login payload",
            "severity": "CRITICAL",
            "page_url": "https://example.com/login",
            "expected_result": "Input sanitized",
            "actual_result": "Uncaught SQL Exception"
        },
        {
            "id": "f-2",
            "module": "accessibility",
            "title": "Missing Form Input Label",
            "description": "Search input lacks aria-label",
            "severity": "MEDIUM",
            "page_url": "https://example.com/",
            "expected_result": "Explicit label tag",
            "actual_result": "No associated label"
        }
    ]
