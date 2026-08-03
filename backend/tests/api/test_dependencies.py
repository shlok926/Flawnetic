import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from jose import jwt

from api.dependencies import get_db, get_current_user
from config.settings import settings
from models.db import User

def test_get_db_generator():
    mock_db_session = MagicMock()
    with patch("api.dependencies.SessionLocal", return_value=mock_db_session):
        gen = get_db()
        db = next(gen)
        assert db == mock_db_session
        with pytest.raises(StopIteration):
            next(gen)
        assert mock_db_session.close.called

def test_get_current_user_invalid_token():
    mock_db = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid-token", db=mock_db)
    assert exc_info.value.status_code == 401

def test_get_current_user_missing_sub():
    mock_db = MagicMock()
    token = jwt.encode({"key": "val"}, settings.jwt_secret_key, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=mock_db)
    assert exc_info.value.status_code == 401

def test_get_current_user_not_found_in_db():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    token = jwt.encode({"sub": str(uuid.uuid4())}, settings.jwt_secret_key, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=token, db=mock_db)
    assert exc_info.value.status_code == 401

def test_get_current_user_success():
    user_id = uuid.uuid4()
    mock_user = User(id=user_id, email="auth@example.com", name="Auth User")
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    token = jwt.encode({"sub": str(user_id)}, settings.jwt_secret_key, algorithm="HS256")
    user = get_current_user(token=token, db=mock_db)
    assert user == mock_user
    assert user.id == user_id
