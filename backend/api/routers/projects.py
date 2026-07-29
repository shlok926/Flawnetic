from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from api.dependencies import get_db, get_current_user
from api.schemas import ProjectCreateRequest, ProjectResponse
from models.db import User, Project

router = APIRouter()

@router.post("", response_model=ProjectResponse)
def create_project(project: ProjectCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_project = Project(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=project.name,
        base_url=project.base_url
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
