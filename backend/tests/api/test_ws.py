import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from jose import jwt

from api.routers.ws import ConnectionManager, websocket_scan_progress
from config.settings import settings
from models.db import ScanStatusEnum

@pytest.mark.asyncio
async def test_connection_manager_connect_disconnect():
    cm = ConnectionManager()
    mock_ws = AsyncMock()

    await cm.connect("scan-100", mock_ws)
    assert mock_ws.accept.called
    assert mock_ws in cm.active_connections["scan-100"]

    cm.disconnect("scan-100", mock_ws)
    assert mock_ws not in cm.active_connections["scan-100"]

    # Disconnect non-existent scan or non-existent ws does not raise error
    cm.disconnect("scan-999", mock_ws)

@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    cm = ConnectionManager()
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()
    mock_ws2.send_json.side_effect = Exception("Send failed")

    await cm.connect("scan-101", mock_ws1)
    await cm.connect("scan-101", mock_ws2)

    await cm.broadcast_progress("scan-101", {"status": "testing"})
    mock_ws1.send_json.assert_called_once_with({"status": "testing"})
    mock_ws2.send_json.assert_called_once()

    # Broadcast to empty scan_id does not raise error
    await cm.broadcast_progress("non-existent-scan", {"status": "done"})

@pytest.mark.asyncio
async def test_websocket_missing_token():
    mock_ws = AsyncMock()
    mock_db = MagicMock()

    await websocket_scan_progress(mock_ws, "scan-1", token=None, db=mock_db)
    mock_ws.close.assert_called_once_with(code=1008, reason="Missing authentication token")

@pytest.mark.asyncio
async def test_websocket_invalid_jwt_token():
    mock_ws = AsyncMock()
    mock_db = MagicMock()

    await websocket_scan_progress(mock_ws, "scan-1", token="invalid-token-string", db=mock_db)
    mock_ws.close.assert_called_once_with(code=1008, reason="Invalid authentication token signature")

@pytest.mark.asyncio
async def test_websocket_missing_sub_in_token():
    mock_ws = AsyncMock()
    mock_db = MagicMock()
    token = jwt.encode({"other": "field"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    await websocket_scan_progress(mock_ws, "scan-1", token=token, db=mock_db)
    mock_ws.close.assert_called_once_with(code=1008, reason="Invalid authentication token payload")

@pytest.mark.asyncio
@patch("api.routers.ws.asyncio.sleep", new_callable=AsyncMock)
async def test_websocket_valid_token_scan_done(mock_sleep):
    mock_ws = AsyncMock()
    mock_db = MagicMock()

    mock_scan_run = MagicMock(id="scan-200", status=ScanStatusEnum.done, site_graph={"pages": 5})
    mock_db.query.return_value.filter.return_value.first.return_value = mock_scan_run
    mock_db.query.return_value.filter.return_value.count.return_value = 12

    valid_token = jwt.encode({"sub": "user-123"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    await websocket_scan_progress(mock_ws, "scan-200", token=valid_token, db=mock_db)

    assert mock_ws.accept.called
    assert mock_ws.send_json.called
    sent_payload = mock_ws.send_json.call_args[0][0]
    assert sent_payload["scan_id"] == "scan-200"
    assert sent_payload["status"] == "done"
    assert sent_payload["findings_count"] == 12

@pytest.mark.asyncio
async def test_websocket_scan_not_found():
    mock_ws = AsyncMock()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    valid_token = jwt.encode({"sub": "user-123"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    await websocket_scan_progress(mock_ws, "invalid-scan-id", token=valid_token, db=mock_db)

    mock_ws.send_json.assert_called_once_with({"error": "Scan run not found"})
