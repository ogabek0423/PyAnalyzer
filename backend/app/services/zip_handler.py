"""ZIP extraction and Python file discovery service."""
import logging
import uuid
import zipfile
from pathlib import Path
from typing import List, Tuple

from app.services.file_handler import ensure_temp_dir, read_file

logger = logging.getLogger(__name__)


def extract_zip(zip_path: Path) -> Tuple[Path, List[Path]]:
    """
    Extract a ZIP archive and return (extract_dir, list_of_py_files).

    Args:
        zip_path: Path to the uploaded .zip file.

    Returns:
        Tuple of (extraction directory, list of .py file paths).
    """
    temp = ensure_temp_dir()
    extract_dir = temp / f"zip_{uuid.uuid4().hex}"
    extract_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Security: skip absolute paths and path-traversal entries
            safe_members = [
                m for m in zf.infolist()
                if not m.filename.startswith("/") and ".." not in m.filename
            ]
            zf.extractall(extract_dir, members=safe_members)
    except zipfile.BadZipFile as e:
        logger.error(f"Bad ZIP file: {e}")
        raise ValueError("Uploaded file is not a valid ZIP archive.") from e
    except Exception as e:
        logger.error(f"ZIP extraction error: {e}")
        raise

    py_files = sorted(extract_dir.rglob("*.py"))
    logger.info(f"Extracted {len(py_files)} Python files from ZIP")
    return extract_dir, py_files


def read_py_files(py_files: List[Path], base_dir: Path) -> List[Tuple[str, str]]:
    """
    Read each .py file and return (relative_name, code) pairs.

    Args:
        py_files: Absolute paths to Python files.
        base_dir: Root extraction directory (for relative naming).

    Returns:
        List of (relative_filename, source_code) tuples.
    """
    results = []
    for path in py_files:
        rel = str(path.relative_to(base_dir))
        code = read_file(path)
        results.append((rel, code))
    return results
