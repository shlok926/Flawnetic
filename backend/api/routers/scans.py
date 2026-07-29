from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from api.dependencies import get_db, get_current_user
from api.schemas import ScanCreateRequest, ScanRunResponse, ScanRunStatusResponse, FindingResponse
from models.db import User, Project, ScanRun, ScanStatusEnum, Finding
from workers.tasks import run_scan

router = APIRouter()

@router.post("/projects/{project_id}/scans", response_model=ScanRunStatusResponse)
def create_scan(
    project_id: uuid.UUID, 
    scan: ScanCreateRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not scan.authorized:
        raise HTTPException(status_code=403, detail="You must authorize the scan")

    scan_run = ScanRun(
        id=uuid.uuid4(),
        project_id=project.id,
        status=ScanStatusEnum.queued,
        config=scan.model_dump()
    )
    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)
    
    # Enqueue celery task
    run_scan.delay(str(scan_run.id))
    
    return {"run_id": scan_run.id, "status": "queued"}

@router.get("/scans/{run_id}", response_model=ScanRunResponse)
def get_scan(run_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Need to verify project ownership via join
    scan_run = db.query(ScanRun).join(Project).filter(ScanRun.id == run_id, Project.user_id == current_user.id).first()
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan run not found")
    return scan_run

@router.get("/scans/{run_id}/findings", response_model=List[FindingResponse])
def get_findings(
    run_id: uuid.UUID, 
    severity: Optional[str] = None,
    module: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    scan_run = db.query(ScanRun).join(Project).filter(ScanRun.id == run_id, Project.user_id == current_user.id).first()
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan run not found")
        
    query = db.query(Finding).filter(Finding.scan_run_id == run_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    if module:
        query = query.filter(Finding.module == module)
        
    return query.all()

@router.get("/scans/{run_id}/report")
def get_report(run_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from models.db import Report
    scan_run = db.query(ScanRun).join(Project).filter(ScanRun.id == run_id, Project.user_id == current_user.id).first()
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan run not found")
        
    report = db.query(Report).filter(Report.scan_run_id == run_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready or failed to generate")
        
    return {"pdf_url": report.pdf_url}
