"""Simple user and API key management."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from passlib.context import CryptContext


class UserManager:
    """Persist and authenticate users with hashed passwords."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.users: Dict[str, str] = {}
        if self.db_path.exists():
            self.users = json.loads(self.db_path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.db_path.write_text(json.dumps(self.users, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_user(self, username: str, password: str) -> None:
        if username in self.users:
            raise ValueError("user exists")
        hashed = self.pwd_context.hash(password)
        self.users[username] = hashed
        self.save()

    def authenticate(self, username: str, password: str) -> bool:
        hashed = self.users.get(username)
        if not hashed:
            return False
        return self.pwd_context.verify(password, hashed)

    def user_exists(self, username: str) -> bool:
        return username in self.users
