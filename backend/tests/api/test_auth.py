import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from jose import jwt

from api.main import app
from api.dependencies import get_db
from api.routers.auth import get_password_hash, verify_password, create_access_token
from config.settings import settings
from models.db import User

client = TestClient(app)

def test_password_hash_and_verification():
    plain = "SuperSecretPassword123!"
    hashed = get_password_hash(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_create_access_token():
    payload = {"sub": "user-uuid-123"}
    token = create_access_token(payload)
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    assert decoded["sub"] == "user-uuid-123"
    assert "exp" in decoded

def test_register_duplicate_email():
    mock_db = MagicMock()
    existing_user = User(id=uuid.uuid4(), email="dup@example.com", name="Existing User")
    mock_db.query.return_value.filter.return_value.first.return_value = existing_user

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123", "name": "Dup User"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"
    finally:
        app.dependency_overrides.clear()

def test_register_success():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/register", json={"email": "newuser@example.com", "password": "password123", "name": "New User"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert mock_db.add.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()

def test_login_user_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/login", data={"username": "notfound@example.com", "password": "password123"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"
    finally:
        app.dependency_overrides.clear()

def test_login_invalid_password():
    mock_db = MagicMock()
    user = User(id=uuid.uuid4(), email="user@example.com", password_hash=get_password_hash("correctpass"))
    mock_db.query.return_value.filter.return_value.first.return_value = user

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/login", data={"username": "user@example.com", "password": "wrongpassword"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"
    finally:
        app.dependency_overrides.clear()

def test_login_success():
    mock_db = MagicMock()
    user_id = uuid.uuid4()
    user = User(id=user_id, email="user@example.com", password_hash=get_password_hash("correctpass"))
    mock_db.query.return_value.filter.return_value.first.return_value = user

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/login", data={"username": "user@example.com", "password": "correctpass"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        decoded = jwt.decode(data["access_token"], settings.jwt_secret_key, algorithms=["HS256"])
        assert decoded["sub"] == str(user_id)
    finally:
        app.dependency_overrides.clear()
