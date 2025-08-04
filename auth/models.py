"""Pydantic models used for authentication requests and responses."""
from __future__ import annotations

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Payload for creating a new user account."""

    username: str
    password: str


class UserLogin(BaseModel):
    """Payload for user login."""

    username: str
    password: str


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"

