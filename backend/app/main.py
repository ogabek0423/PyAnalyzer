"""FastAPI application entry point."""
import asyncio
import logging
import logging.config
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routers import analyze_text, analyze_file, analyze_zip, analyze_github

# ── Logging ────────────────────────────────────────────────────────────────────
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "system_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "system.log"),
            "formatter": "default",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "errors.log"),
            "level": "ERROR",
            "formatter": "default",
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "system_file", "error_file"],
    },
})

logger = logging.getLogger(__name__)

# ── Rate Limiter ───────────────────────────────────────────────────────────────
# Har bir IP manzildan daqiqada max 20 ta so'rov
limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])

# ── Parallel so'rovlar cheklovi ────────────────────────────────────────────────
# Bir vaqtda max 5 ta tahlil operatsiyasi
analysis_semaphore = asyncio.Semaphore(5)

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Python Code Analysis System",
    description="Analyze Python code for syntax errors and security issues.",
    version="1.0.0",
)

# Rate limiter ni ilovaga ulash
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Faqat ruxsat etilgan manzillardan so'rovlar qabul qilinadi
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    # Frontend fayl to'g'ridan-to'g'ri brauzerda ochilsa:
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Routerlar ──────────────────────────────────────────────────────────────────
app.include_router(
    analyze_text.router, prefix="/analyze", tags=["analyze"],
)
app.include_router(
    analyze_file.router, prefix="/analyze", tags=["analyze"],
)
app.include_router(
    analyze_zip.router, prefix="/analyze", tags=["analyze"],
)
app.include_router(
    analyze_github.router, prefix="/analyze", tags=["analyze"],
)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


logger.info("Python Code Analysis API started")