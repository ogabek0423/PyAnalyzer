"""Router for POST /analyze/github endpoint."""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.analysis_result import AnalysisResult, GithubRequest
from app.services.file_handler import cleanup
from app.services.github_cloner import clone_repo, read_py_files
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/github", response_model=AnalysisResult)
async def analyze_github(request: GithubRequest) -> AnalysisResult:
    """
    Clone a public GitHub repository and analyze all Python files.

    Args:
        request: JSON body with 'repo_url' field.

    Returns:
        Aggregated AnalysisResult for all .py files in the repo.
    """
    clone_dir: Path | None = None
    try:
        clone_dir, py_files = clone_repo(request.repo_url)

        if not py_files:
            return AnalysisResult(
                status="success",
                filename=request.repo_url,
                syntax_errors=[],
                security_warnings=[],
                total_files_analyzed=0,
            )

        pairs = read_py_files(py_files, clone_dir)
        result = build_result(pairs)
        result.filename = request.repo_url
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"GitHub analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if clone_dir:
            cleanup(clone_dir)
