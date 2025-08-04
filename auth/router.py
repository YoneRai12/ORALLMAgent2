"""JWT authentication routes and utilities."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from users.auth import UserManager
from .models import Token, UserCreate

SECRET_KEY = os.getenv("JWT_SECRET", "change_me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["Manus-Like"])
user_manager = UserManager(Path("data/users.json"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/signup")
def signup(payload: UserCreate) -> dict:
    """Register a new user account."""

    if user_manager.user_exists(payload.username):
        raise HTTPException(status_code=400, detail="user exists")
    user_manager.create_user(payload.username, payload.password)
    return {"msg": "created"}


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Authenticate a user and return an access token."""

    if not user_manager.authenticate(form_data.username, form_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token(
        {"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """FastAPI dependency to retrieve the current user from a JWT."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or not user_manager.user_exists(username):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    except JWTError as exc:  # pragma: no cover - simple error path
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    return username

