"""GitHub repository cloning service."""
import logging
import re
import uuid
from pathlib import Path
from typing import List, Tuple

from app.services.file_handler import ensure_temp_dir, read_file

logger = logging.getLogger(__name__)

GITHUB_URL_RE = re.compile(
    r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+(\.git)?(/.*)?$"
)


def validate_github_url(url: str) -> None:
    """Raise ValueError if the URL doesn't look like a public GitHub repo."""
    if not GITHUB_URL_RE.match(url.strip()):
        raise ValueError(f"Invalid GitHub URL: {url!r}")


def clone_repo(repo_url: str) -> Tuple[Path, List[Path]]:
    """
    Clone a public GitHub repository and return (clone_dir, py_files).

    Args:
        repo_url: HTTPS URL of the public GitHub repository.

    Returns:
        Tuple of (cloned directory, list of .py file paths).
    """
    try:
        import git  # type: ignore
    except ImportError:
        raise RuntimeError("GitPython is not installed. Add 'gitpython' to requirements.txt.")

    validate_github_url(repo_url)

    temp = ensure_temp_dir()
    clone_dir = temp / f"repo_{uuid.uuid4().hex}"

    logger.info(f"Cloning {repo_url} → {clone_dir}")
    try:
        git.Repo.clone_from(repo_url.strip(), clone_dir, depth=1)
    except git.exc.GitCommandError as e:
        logger.error(f"Git clone failed: {e}")
        raise ValueError(f"Failed to clone repository. Make sure the URL is correct and the repo is public. ({e})") from e

    py_files = sorted(p for p in clone_dir.rglob("*.py") if ".git" not in p.parts)
    logger.info(f"Found {len(py_files)} Python files in cloned repo")
    return clone_dir, py_files


def read_py_files(py_files: List[Path], base_dir: Path) -> List[Tuple[str, str]]:
    """Return (relative_name, code) pairs for each .py file."""
    results = []
    for path in py_files:
        rel = str(path.relative_to(base_dir))
        code = read_file(path)
        results.append((rel, code))
    return results
