from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
from app.core.config import settings
from app.api.v1.router import api_router
import traceback
import uuid
import logging

app = FastAPI(title=settings.project_name)

# Configure a basic logger if not already configured
logger = logging.getLogger("uvicorn.error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.project_name}"}

# Optional: enable `python main.py` to run a dev server directly
if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    except Exception as e:
        # Avoid crashing if uvicorn not installed in some environments
        raise SystemExit(f"Failed to start uvicorn: {e}")
