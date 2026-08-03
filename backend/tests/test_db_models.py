import pytest
import uuid
from models.db import User, Project, ScanRun, Finding, RoleEnum, ScanStatusEnum
from api.schemas import UserRegisterRequest, UserLoginRequest, ScanCreateRequest

def test_db_user_model():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="testuser@example.com",
        password_hash="hashed_pw_123",
        name="Test User",
        role=RoleEnum.member
    )
    assert user.id == user_id
    assert user.email == "testuser@example.com"
    assert user.role == RoleEnum.member

def test_db_project_model():
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    project = Project(
        id=project_id,
        user_id=user_id,
        name="E-Commerce Audit Project",
        base_url="https://demo.example.com"
    )
    assert project.id == project_id
    assert project.name == "E-Commerce Audit Project"
    assert project.base_url == "https://demo.example.com"

def test_db_scan_run_model():
    scan_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scan_run = ScanRun(
        id=scan_id,
        project_id=project_id,
        status=ScanStatusEnum.crawling
    )
    assert scan_run.id == scan_id
    assert scan_run.status == ScanStatusEnum.crawling

def test_pydantic_schemas_validation():
    reg_req = UserRegisterRequest(email="newuser@example.com", password="securepassword", name="New User")
    assert reg_req.email == "newuser@example.com"
    
    login_req = UserLoginRequest(email="newuser@example.com", password="securepassword")
    assert login_req.email == "newuser@example.com"

    scan_req = ScanCreateRequest(max_pages=25)
    assert scan_req.max_pages == 25
