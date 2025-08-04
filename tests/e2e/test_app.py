import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CSRF_SECRET_SALT", "test_salt")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost")
os.environ.setdefault("CSRF_DISABLE", "true")
from main import app

client = TestClient(app, base_url="http://localhost")


@pytest.fixture(scope="session")
def token() -> str:
    client.post("/auth/signup", json={"username": "u", "password": "p"})
    res = client.post("/auth/token", data={"username": "u", "password": "p"})
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def session_id(token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/sessions", headers=headers)
    sid = res.json()["session_id"]
    start = client.post(
        f"/sessions/{sid}/browser/start",
        json={"url": "https://example.com"},
        headers=headers,
    )
    if start.status_code != 200:
        pytest.skip("Playwright browser not available")
    return sid


def test_login_start_stream(session_id: str) -> None:
    with client.websocket_connect(f"/ws/stream/{session_id}") as ws:
        frame = ws.receive_bytes()
        assert isinstance(frame, (bytes, bytearray)) and len(frame) > 0


def test_second_viewer(session_id: str) -> None:
    with client.websocket_connect(f"/ws/stream/{session_id}") as ws1:
        ws1.receive_bytes()
        with client.websocket_connect(f"/ws/stream/{session_id}") as ws2:
            frame = ws2.receive_bytes()
            assert frame


def test_file_upload_download(token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    content = b"hello"
    up = client.post(
        "/api/upload", headers=headers, files={"file": ("test.txt", content)}
    )
    assert up.status_code == 200
    down = client.get("/api/download/test.txt", headers=headers)
    assert down.content == content
