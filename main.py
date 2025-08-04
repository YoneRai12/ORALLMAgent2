"""Main entry point for Manus-style autonomous AI agent system.

Provides CLI and REST API interfaces for sending natural language tasks to
local LLM servers.  This scaffold is designed to be extended with additional
planning, tool execution, and reflection logic.

Security Features:
- JWT auth with credentials from environment variables
- CORS, rate limiting, and CSRF protection for web clients
- API served only on localhost/LAN (do not expose publicly)
"""
from __future__ import annotations

import argparse
import os
import time
from typing import List

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi_csrf_protect import CsrfProtect

# Load environment variables from .env if present
load_dotenv()

app = FastAPI(title="Manus Agent", description="Autonomous AI agent scaffold")

# --- CORS ---
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address, default_limits=[os.getenv("RATE_LIMIT", "5/minute")])
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# --- CSRF Protection ---
class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET", "change_me")

@CsrfProtect.load_config
def get_csrf_config() -> CsrfSettings:  # pragma: no cover - configuration
    return CsrfSettings()

# --- Auth Helpers ---
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))
API_USER = os.getenv("API_USER", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "change_me")

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
        if username != API_USER:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return username
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed") from exc

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return verify_token(token)

# --- Models ---
class TaskRequest(BaseModel):
    """Schema for REST API task requests."""
    instruction: str

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

# --- API Endpoints ---
@app.post("/token")
@limiter.limit("5/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), csrf_protect: CsrfProtect = Depends()) -> Response:
    if form_data.username != API_USER or form_data.password != API_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token({"sub": API_USER}, ACCESS_TOKEN_EXPIRE_SECONDS)
    csrf_token = csrf_protect.generate_csrf()
    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    csrf_protect.set_csrf_cookie(response, csrf_token)
    response.headers["X-CSRF-Token"] = csrf_token
    return response

@app.get("/status")
async def status_endpoint() -> dict:
    return {"status": "ok", "version": "0.1"}

@app.post("/api/task")
@limiter.limit("5/minute")
async def run_task(request: Request, req: TaskRequest, csrf_protect: CsrfProtect = Depends(), user: str = Depends(get_current_user)) -> dict:
    csrf_protect.validate_csrf(request)
    plan = call_llm(f"Create a plan for the following task and return JSON steps: {req.instruction}")
    return {"plan": plan, "user": user}

# --- CLI Mode ---
def cli_mode(args: List[str]) -> None:
    """Run the agent in CLI mode."""
    instruction = " ".join(args) if args else input("Instruction: ")
    plan = call_llm(f"Create a plan for the following task and return JSON steps: {instruction}")
    print("Plan:\n", plan)
    # Placeholder: execute the plan step-by-step and provide reflections.
    print("Execution is not yet implemented in this scaffold.")

# --- Entrypoint ---
def main() -> None:
    """Parse command-line arguments and start CLI or REST API server."""
    parser = argparse.ArgumentParser(description="Manus-style autonomous agent")
    parser.add_argument("instruction", nargs=argparse.REMAINDER, help="Task instruction for CLI mode")
    parser.add_argument("--api", action="store_true", help="Run REST API server instead of CLI")
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
