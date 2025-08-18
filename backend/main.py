from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from app.core.config import settings
from app.api.v1.router import api_router
import traceback
import uuid
import logging
import os
import socket
import subprocess
from typing import Optional

app = FastAPI(title=settings.project_name)

# Configure a basic logger if not already configured
logger = logging.getLogger("uvicorn.error")

# Compute allowed CORS origins from settings + local dev
_cors_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
try:
    _cors_origins.add(settings.frontend_base_url)
    _cors_origins.add(settings.training_frontend_base_url)
    _cors_origins.add(settings.production_frontend_base_url)
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global handler for unhandled exceptions to include stack trace in responses
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    # Log the error with stack trace and correlation id
    logger.error("Unhandled exception [%s] at %s %s\n%s", error_id, request.method, request.url.path, trace)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "trace": trace,
            "error_id": error_id,
            "path": str(request.url.path),
            "method": request.method,
        },
        headers={"X-Error-ID": error_id},
    )


# ---- Dev: Auto-start Vite on backend start (optional via env FRONTEND_AUTOSTART=true) ----
VITE_DEFAULT_PORT = int(os.getenv("VITE_PORT", "5173"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
# If project structure is backend/ and frontend/ at repo root, adjust path accordingly
if not os.path.isdir(FRONTEND_DIR):
    # Try repo-root/frontend from backend/main.py location
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))


# Path to built frontend assets
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "false").lower() in {"1", "true", "yes", "y"}


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        try:
            return s.connect_ex((host, port)) == 0
        except OSError:
            return False


@app.on_event("startup")
async def maybe_start_vite() -> None:
    # Opt-in via environment variable
    autostart = os.getenv("FRONTEND_AUTOSTART", "false").lower() in {"1", "true", "yes", "y"}
    if not autostart:
        logger.info("Vite autostart disabled. Set FRONTEND_AUTOSTART=true to enable.")
        return

    if _port_open("127.0.0.1", VITE_DEFAULT_PORT) or _port_open("localhost", VITE_DEFAULT_PORT):
        logger.info("Vite appears to be already running on port %s; skipping autostart.", VITE_DEFAULT_PORT)
        return

    if not os.path.isdir(FRONTEND_DIR):
        logger.warning("Cannot autostart Vite: frontend directory not found at %s", FRONTEND_DIR)
        return

    # Build command for Windows PowerShell/cmd
    vite_cmd = os.getenv("VITE_START_CMD") or f"npm run dev -- --port {VITE_DEFAULT_PORT}"
    try:
        logger.info("Starting Vite in %s with: %s", FRONTEND_DIR, vite_cmd)
        # shell=True to resolve npm on PATH on Windows; run detached but keep handle
        proc = subprocess.Popen(
            vite_cmd,
            cwd=FRONTEND_DIR,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        app.state.vite_process = proc
    except Exception as e:
        logger.exception("Failed to start Vite: %s", e)


@app.on_event("shutdown")
async def stop_vite() -> None:
    proc: Optional[subprocess.Popen] = getattr(app.state, "vite_process", None)
    if not proc:
        return
    try:
        logger.info("Stopping Vite (pid=%s)", proc.pid)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    except Exception as e:
        logger.warning("Error while stopping Vite: %s", e)


# API routes
app.include_router(api_router, prefix="/api/v1")

# Optionally serve built frontend
if SERVE_FRONTEND and os.path.isdir(FRONTEND_DIST):
    logger.info("Serving frontend from %s", FRONTEND_DIST)
    # Mount at root; html=True enables SPA fallback to index.html
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    # Fallback simple root endpoint when not serving the SPA
    @app.get("/")
    async def root():
        return {"message": f"Welcome to {settings.project_name}"}

# Optional: enable `python main.py` to run a server directly (dev by default)
if __name__ == "__main__":
    try:
        import uvicorn
        # Prefer LOOMA_HOST if provided; otherwise, if PORT is set (e.g., on Render), default to 0.0.0.0
        # Fall back to 127.0.0.1 for local development.
        port_env = os.getenv("LOOMA_PORT") or os.getenv("PORT") or "8000"
        try:
            port = int(port_env)
        except ValueError:
            logger.warning("Invalid port env (LOOMA_PORT/PORT)=%s; defaulting to 8000", port_env)
            port = 8000
        # If a platform PORT is provided and LOOMA_HOST not explicitly set, bind to all interfaces
        host = os.getenv("LOOMA_HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
        # Reload is useful in dev, but should be disabled in production by default
        reload_flag = (os.getenv("UVICORN_RELOAD") or os.getenv("RELOAD") or "").lower() in {"1", "true", "yes", "y"}
        if os.getenv("PORT") and not os.getenv("LOOMA_HOST") and not (os.getenv("UVICORN_RELOAD") or os.getenv("RELOAD")):
            reload_flag = False
        uvicorn.run("main:app", host=host, port=port, reload=reload_flag)
    except Exception as e:
        # Avoid crashing if uvicorn not installed in some environments
        raise SystemExit(f"Failed to start uvicorn: {e}")
