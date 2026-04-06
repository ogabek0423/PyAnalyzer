"""Router for POST /analyze/file endpoint."""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.analysis_result import AnalysisResult
from app.services.file_handler import ensure_temp_dir, cleanup
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/file", response_model=AnalysisResult)
async def analyze_file(file: UploadFile = File(...)) -> AnalysisResult:
    """
    Analyze a single uploaded .py file.

    Args:
        file: Multipart-uploaded Python file.

    Returns:
        AnalysisResult with syntax errors and security warnings.
    """
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are accepted.")

    temp = ensure_temp_dir()
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest = temp / safe_name

    try:
        content = await file.read()
        dest.write_bytes(content)
        code = content.decode("utf-8", errors="replace")
        result = build_result([(file.filename, code)])
        result.filename = file.filename
        return result
    except Exception as e:
        logger.error(f"File analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup(dest)
