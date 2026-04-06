"""FastAPI application entry point."""
import logging
import logging.config
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze_text, analyze_file, analyze_zip, analyze_github

# ── Logging setup ──────────────────────────────────────────────────────────────
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
        "system_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "system.log"),
            "formatter": "default",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "errors.log"),
            "level": "ERROR",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "system_file", "error_file"],
    },
})

logger = logging.getLogger(__name__)

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Python Code Analysis System",
    description="Analyze Python code for syntax errors and security issues.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_text.router, prefix="/analyze", tags=["analyze"])
app.include_router(analyze_file.router, prefix="/analyze", tags=["analyze"])
app.include_router(analyze_zip.router, prefix="/analyze", tags=["analyze"])
app.include_router(analyze_github.router, prefix="/analyze", tags=["analyze"])


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


logger.info("Python Code Analysis API started")
