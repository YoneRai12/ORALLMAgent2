import importlib
import os
from fastapi.testclient import TestClient
from fastapi import Request

from users.deps import get_user_manager


def load_app(**env):
    os.environ.setdefault("CSRF_SECRET_SALT", "test_salt")
    for k, v in env.items():
        os.environ[k] = v
    import main

    importlib.reload(main)
    return main


def test_path_traversal_blocked():
    main = load_app(CSRF_DISABLE="true")
    client = TestClient(main.app, base_url="http://localhost")
    client.post("/auth/signup", json={"username": "u", "password": "p"})
    res = client.post("/auth/token", data={"username": "u", "password": "p"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/download/%2e%2e/%2e%2e/.env", headers=headers)
    assert resp.status_code == 403


def test_csrf_env_match():
    main = load_app(CSRF_DISABLE="true")
    assert main.CsrfSettings().secret_key == os.environ["CSRF_SECRET_SALT"]
    request = Request({"type": "http", "app": main.app})
    um = get_user_manager(request)
    assert id(um) == id(main.app.state.user_manager)


def test_csrf_validation():
    main = load_app(CSRF_DISABLE="false")
    client = TestClient(
        main.app, base_url="http://localhost", raise_server_exceptions=False
    )
    res = client.post("/users/signup", json={"username": "a", "password": "b"})
    assert res.status_code == 403


def test_allowed_hosts():
    main = load_app(
        CSRF_DISABLE="true",
        ALLOWED_HOSTS="127.0.0.1,localhost,127.0.0.1:8001,localhost:8001",
    )
    client = TestClient(main.app, base_url="http://127.0.0.1:8001")
    resp = client.get("/docs")
    assert resp.status_code == 200
