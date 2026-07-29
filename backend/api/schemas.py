from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from models.db import RoleEnum, ScanStatusEnum, ModuleEnum, SeverityEnum

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: RoleEnum
    
    class Config:
        from_attributes = True

# --- Project Schemas ---
class ProjectCreateRequest(BaseModel):
    name: str
    base_url: str

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    base_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Scan Schemas ---
class ScanCreateRequest(BaseModel):
    max_pages: int = 50
    max_depth: int = 4
    modules: List[str] = ["functional", "security", "visual", "accessibility"]
    browsers: List[str] = ["chromium"]
    authorized: bool = False

class ScanRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: ScanStatusEnum
    started_at: datetime
    finished_at: Optional[datetime]
    config: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ScanRunStatusResponse(BaseModel):
    run_id: UUID
    status: str

class FindingResponse(BaseModel):
    id: UUID
    scan_run_id: UUID
    module: ModuleEnum
    title: str
    description: str
    severity: SeverityEnum
    
    class Config:
        from_attributes = True
