from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import asyncio

from dependencies import get_db
from models.db import ScanRun, Finding

router = APIRouter(prefix="/ws", tags=["Real-time WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, scan_id: str, websocket: WebSocket):
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        self.active_connections[scan_id].append(websocket)

    def disconnect(self, scan_id: str, websocket: WebSocket):
        if scan_id in self.active_connections:
            if websocket in self.active_connections[scan_id]:
                self.active_connections[scan_id].remove(websocket)

    async def broadcast_progress(self, scan_id: str, data: dict):
        if scan_id in self.active_connections:
            for connection in self.active_connections[scan_id]:
                try:
                    await connection.send_json(data)
                except Exception:
                    pass

manager = ConnectionManager()

@router.websocket("/scans/{scan_id}")
async def websocket_scan_progress(websocket: WebSocket, scan_id: str, db: Session = Depends(get_db)):
    """
    Real-time WebSocket connection endpoint for monitoring live scan progress and findings stream.
    """
    await manager.connect(scan_id, websocket)
    try:
        while True:
            scan_run = db.query(ScanRun).filter(ScanRun.id == scan_id).first()
            if not scan_run:
                await websocket.send_json({"error": "Scan run not found"})
                break

            findings_count = db.query(Finding).filter(Finding.scan_run_id == scan_id).count()

            payload = {
                "scan_id": str(scan_run.id),
                "status": scan_run.status.value,
                "findings_count": findings_count,
                "site_graph": scan_run.site_graph
            }

            await websocket.send_json(payload)

            if scan_run.status.value in ["done", "failed"]:
                break

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(scan_id, websocket)
    except Exception:
        manager.disconnect(scan_id, websocket)
