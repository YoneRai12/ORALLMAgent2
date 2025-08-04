"""Main entry point for Manus-style autonomous AI agent system.

Provides CLI and REST API interfaces for sending natural language tasks to
local LLM servers.  This scaffold is designed to be extended with additional
planning, tool execution, and reflection logic.

Security Features:
- JWT auth with credentials from environment variables
- CORS, rate limiting, and CSRF protection for web clients
- API served only on localhost/LAN (do not expose publicly)
"""

import argparse
import os
import time
import shutil
import shlex
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, JSONResponse
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from slowapi import _rate_limit_exceeded_handler
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from limiter import limiter
from agent import AgentManager
from dashboard import dashboard_router, set_state
from api import router as api_router, set_managers as set_api_managers
from sessions.manager import SessionManager
from plugins import load_plugins
from users import UserManager
from auth.router import router as auth_router
from agent.parsers import parse_kv_pairs

CSRF_DISABLE = os.getenv("CSRF_DISABLE", "false").lower() == "true"

# Load environment variables from .env if present
load_dotenv()

app = FastAPI(title="Manus Agent", description="Autonomous AI agent scaffold")

allowed_hosts = [
    h.strip()
    for h in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,127.0.0.1:8001,localhost:8001",
    ).split(",")
    if h.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(api_router)

# Directory for storing session artifacts
SESSION_DIR = Path(os.getenv("SESSION_DIR", "session_data"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)
API_USER = os.getenv("API_USER", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "change_me")
session_manager = SessionManager(SESSION_DIR)
agent_manager = AgentManager(max_agents=int(os.getenv("MAX_AGENTS", "5")))
user_db = UserManager(Path(os.getenv("USER_DB", "data/users.json")))
app.state.user_manager = user_db
# make managers available to API router
set_api_managers(agent_manager, session_manager)
# initialise default admin user if credentials provided
if not user_db.user_exists(API_USER):
    try:
        user_db.create_user(API_USER, API_PASSWORD)
    except ValueError:
        pass
set_state(agent_manager, session_manager)
loaded_plugins = load_plugins(app)
chat_rooms: Dict[str, set[WebSocket]] = {}
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploaded_files"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/stream", StaticFiles(directory=SESSION_DIR), name="stream")

origins = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate Limiting ---
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# --- CSRF Protection ---
CSRF_SALT = os.getenv("CSRF_SECRET_SALT")
if not CSRF_SALT and os.getenv("DEBUG", "false").lower() != "true":
    raise RuntimeError("CSRF_SECRET_SALT not set")


class CsrfSettings(BaseModel):
    secret_key: str = CSRF_SALT or "change_me"


@CsrfProtect.load_config
def get_csrf_config() -> CsrfSettings:  # pragma: no cover - configuration
    return CsrfSettings()


csrf_protect = CsrfProtect()


if CSRF_DISABLE:

    @app.middleware("http")
    async def csrf_disabled(request: Request, call_next):
        return await call_next(request)

else:

    @app.middleware("http")
    async def csrf_middleware(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            try:
                await csrf_protect.validate_csrf(request)
            except CsrfProtectError as exc:  # pragma: no cover - simple error path
                return JSONResponse(status_code=403, content={"detail": str(exc)})
        return await call_next(request)


# --- Auth Helpers ---
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def create_access_token(data: dict, expires_delta: int) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub", "")
        if not user_db.user_exists(username):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        return username
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed"
        ) from exc


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return verify_token(token)


# --- Models ---
class TaskRequest(BaseModel):
    """Schema for REST API task requests.

    Supports both free-form ``instruction`` and structured Amazon purchases via
    the ``amazon_buy`` task.
    """

    instruction: str | None = None
    task: str | None = None
    item: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, alias="pass")


class BrowserStartRequest(BaseModel):
    """Request body for starting a browser session."""

    url: str = "about:blank"


class BrowserCommand(BaseModel):
    """Control commands for an existing browser session."""

    action: str  # "pause", "resume", or "step"


class AgentCreateRequest(BaseModel):
    """Create a new sub-agent with optional profile."""

    profile: str = "default"


class SessionCreateRequest(BaseModel):
    """Request body for creating a new user session."""

    profile: str = "default"


class UserCreate(BaseModel):
    username: str
    password: str


# --- Utility ---
def call_llm(prompt: str) -> str:
    """Call the configured LLM server and return the generated text."""
    endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "default")

    response = requests.post(
        endpoint,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "512")),
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def parse_amazon_command(cmd: str) -> Dict[str, str | None]:
    """Parse ``!amazon buy`` commands with inline credentials."""

    kv, sanitized = parse_kv_pairs(cmd)
    tokens = shlex.split(sanitized)
    if len(tokens) < 3 or tokens[0] != "!amazon" or tokens[1] != "buy":
        raise ValueError("unsupported command")
    item = " ".join(tokens[2:])
    return {
        "task": "amazon_buy",
        "item": item,
        "email": kv.get("email"),
        "pass": kv.get("pass"),
    }


# --- API Endpoints ---
@app.post("/token")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    csrf_protect: CsrfProtect = Depends(),
) -> Response:
    if not user_db.authenticate(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        {"sub": form_data.username}, ACCESS_TOKEN_EXPIRE_SECONDS
    )
    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    if not CSRF_DISABLE:
        csrf_token, signed = csrf_protect.generate_csrf_tokens()
        csrf_protect.set_csrf_cookie(signed, response)
        response.headers["X-CSRF-Token"] = csrf_token
    return response


@app.post("/users/signup")
async def signup(user: UserCreate) -> dict:
    if user_db.user_exists(user.username):
        raise HTTPException(status_code=400, detail="user exists")
    user_db.create_user(user.username, user.password)
    return {"status": "created"}


@app.get("/status")
async def status_endpoint() -> dict:
    return {"status": "ok", "version": "0.9.0"}


@app.post("/api/task")
@limiter.limit("5/minute")
async def run_task(
    request: Request,
    req: TaskRequest,
    csrf_protect: CsrfProtect = Depends(),
    user: str = Depends(get_current_user),
) -> dict:
    if not CSRF_DISABLE:
        await csrf_protect.validate_csrf(request)
    if req.task == "amazon_buy":
        # Inline credentials are accepted but not returned in the response
        return {"task": req.task, "item": req.item, "user": user}
    instruction = req.instruction or ""
    plan = call_llm(
        f"Create a plan for the following task and return JSON steps: {instruction}"
    )
    return {"plan": plan, "user": user}


# --- Multi-agent management ---
@app.post("/agents")
async def create_agent_endpoint(
    req: AgentCreateRequest, user: str = Depends(get_current_user)
) -> dict:
    agent_id = agent_manager.create_agent(req.profile)
    return {"agent_id": agent_id}


@app.get("/agents")
async def list_agents_endpoint(user: str = Depends(get_current_user)) -> dict:
    return agent_manager.list_agents()


@app.post("/agents/{agent_id}/task")
async def agent_task_endpoint(
    agent_id: str, req: TaskRequest, user: str = Depends(get_current_user)
) -> dict:
    agent = agent_manager.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    plan = agent.plan(req.instruction)
    result = agent.execute(plan)
    return {"plan": plan, "result": result}


# --- Session Endpoints ---
@app.post("/sessions")
async def create_session_endpoint(
    req: SessionCreateRequest, user: str = Depends(get_current_user)
) -> dict:
    agent_id = agent_manager.create_agent(req.profile)
    session = session_manager.create(agent_id, owner=user)
    agent = agent_manager.get(agent_id)
    if agent and session.log:
        agent.logger = session.log
    return {"session_id": session.session_id, "agent_id": agent_id}


@app.get("/sessions")
async def list_sessions_endpoint(user: str = Depends(get_current_user)) -> dict:
    return session_manager.list(owner=user)


@app.post("/sessions/{session_id}/save")
async def save_session_endpoint(
    session_id: str, user: str = Depends(get_current_user)
) -> dict:
    session = session_manager.get(session_id)
    if session is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    session_manager.save(session_id)
    return {"status": "saved"}


@app.post("/sessions/{session_id}/load")
async def load_session_endpoint(
    session_id: str, user: str = Depends(get_current_user)
) -> dict:
    session = session_manager.load(session_id)
    if session.owner != user:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"status": "loaded"}


@app.get("/sessions/{session_id}/log")
async def download_log_endpoint(
    session_id: str, user: str = Depends(get_current_user)
) -> FileResponse:
    session = session_manager.get(session_id)
    if session is None or session.log is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    return FileResponse(session.log.path, filename="actions.log")


# --- File upload/download ---
@app.post("/sessions/{session_id}/files")
async def upload_file(
    session_id: str,
    uploaded: UploadFile = File(...),
    user: str = Depends(get_current_user),
) -> dict:
    session = session_manager.get(session_id)
    if session is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    dest_dir = UPLOAD_DIR / session_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / uploaded.filename
    with dest_path.open("wb") as f:
        f.write(await uploaded.read())
    return {"filename": uploaded.filename}


@app.get("/sessions/{session_id}/files/{filename}")
async def download_file(
    session_id: str, filename: str, user: str = Depends(get_current_user)
) -> FileResponse:
    session = session_manager.get(session_id)
    if session is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    safe_name = Path(filename).name
    base = (UPLOAD_DIR / session_id).resolve()
    file_path = (base / safe_name).resolve()
    if not file_path.is_relative_to(base):
        raise HTTPException(status_code=403, detail="forbidden")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(file_path)


# --- Browser Session Endpoints ---
@app.post("/sessions/{session_id}/browser/start")
async def start_browser(
    session_id: str, req: BrowserStartRequest, user: str = Depends(get_current_user)
) -> dict:
    """Launch browser for an existing session and navigate to the given URL."""
    session = session_manager.get(session_id)
    if session is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    assert session.browser is not None
    await session.browser.start(req.url)
    return {"status": "started"}


@app.post("/sessions/{session_id}/browser/command")
async def control_browser(
    session_id: str, cmd: BrowserCommand, user: str = Depends(get_current_user)
) -> dict:
    """Control an existing browser session (pause/resume/step)."""
    session = session_manager.get(session_id)
    if session is None or session.browser is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    if cmd.action == "pause":
        session.browser.pause()
    elif cmd.action == "resume":
        session.browser.resume()
    elif cmd.action == "step":
        await session.browser.step()
    else:
        raise HTTPException(status_code=400, detail="unknown action")
    return {"status": "ok"}


@app.get("/sessions/{session_id}/browser/download")
async def download_session(
    session_id: str, user: str = Depends(get_current_user)
) -> FileResponse:
    """Download screenshots for a session as a ZIP archive."""
    session = session_manager.get(session_id)
    if session is None or session.browser is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    zip_path = shutil.make_archive(
        str(session.browser.save_dir), "zip", root_dir=session.browser.save_dir
    )
    return FileResponse(zip_path, filename=f"{session_id}.zip")


@app.get("/sessions/{session_id}/browser/video")
async def download_video(
    session_id: str, user: str = Depends(get_current_user)
) -> FileResponse:
    """Download recorded video for a browser session."""
    session = session_manager.get(session_id)
    if session is None or session.browser is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    video_path = session.browser.video_path
    if video_path is None or not video_path.exists():
        raise HTTPException(status_code=404, detail="video not available")
    return FileResponse(video_path, filename=f"{session_id}.webm")


@app.websocket("/ws/session/{session_id}")
async def session_stream(websocket: WebSocket, session_id: str, token: str) -> None:
    """Stream base64-encoded screenshots over WebSocket."""
    try:
        user = verify_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return
    session = session_manager.get(session_id)
    if session is None or session.browser is None or session.owner != user:
        await websocket.close(code=1008)
        return
    queue = session.browser.register()
    await websocket.accept()
    try:
        while True:
            img = await queue.get()
            await websocket.send_text(img)
    except WebSocketDisconnect:
        pass
    finally:
        session.browser.unregister(queue)


@app.websocket("/ws/chat/{room}")
async def chat_stream(websocket: WebSocket, room: str) -> None:
    """Simple multi-user chat channel for collaboration."""
    await websocket.accept()
    users = chat_rooms.setdefault(room, set())
    users.add(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            for ws in list(users):
                if ws is not websocket:
                    await ws.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        users.discard(websocket)


# --- CLI Mode ---
def cli_mode(args: List[str]) -> None:
    """Run the agent in CLI mode."""
    instruction = " ".join(args) if args else input("Instruction: ")
    if instruction.startswith("!amazon"):
        parsed = parse_amazon_command(instruction)
        print(parsed)
        return
    plan = call_llm(
        f"Create a plan for the following task and return JSON steps: {instruction}"
    )
    print("Plan:\n", plan)
    # Placeholder: execute the plan step-by-step and provide reflections.
    print("Execution is not yet implemented in this scaffold.")


# --- Entrypoint ---
def main() -> None:
    """Parse command-line arguments and start CLI or REST API server."""
    parser = argparse.ArgumentParser(description="Manus-style autonomous agent")
    parser.add_argument(
        "instruction", nargs=argparse.REMAINDER, help="Task instruction for CLI mode"
    )
    parser.add_argument(
        "--api", action="store_true", help="Run REST API server instead of CLI"
    )
    args = parser.parse_args()

    if args.api:
        import uvicorn

        port = int(os.getenv("PORT", "8001"))
        # Warning: ensure the server is not exposed to the public internet.
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
    else:
        cli_mode(args.instruction)


if __name__ == "__main__":
    main()
