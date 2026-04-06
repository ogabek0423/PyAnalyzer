"""Utility helpers for reading and cleaning up temporary files."""
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

TEMP_DIR = Path(__file__).resolve().parents[2] / "temp"


def ensure_temp_dir() -> Path:
    """Create the temp directory if it doesn't exist."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_DIR


def read_file(path: Path) -> str:
    """Read a file and return its content as a string."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return ""


def cleanup(path: Path) -> None:
    """Remove a file or directory silently."""
    try:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    except Exception as e:
        logger.warning(f"Cleanup failed for {path}: {e}")
