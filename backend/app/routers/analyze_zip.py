"""Router for POST /analyze/zip endpoint."""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.analysis_result import AnalysisResult
from app.services.file_handler import ensure_temp_dir, cleanup
from app.services.zip_handler import extract_zip, read_py_files
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/zip", response_model=AnalysisResult)
async def analyze_zip(file: UploadFile = File(...)) -> AnalysisResult:
    """
    Analyze all Python files inside an uploaded ZIP archive.

    Args:
        file: Multipart-uploaded .zip file.

    Returns:
        Aggregated AnalysisResult across all .py files found.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted.")

    temp = ensure_temp_dir()
    zip_path = temp / f"{uuid.uuid4().hex}.zip"
    extract_dir: Path | None = None

    try:
        content = await file.read()
        zip_path.write_bytes(content)

        extract_dir, py_files = extract_zip(zip_path)

        if not py_files:
            return AnalysisResult(
                status="success",
                filename=file.filename,
                syntax_errors=[],
                security_warnings=[],
                total_files_analyzed=0,
            )

        pairs = read_py_files(py_files, extract_dir)
        result = build_result(pairs)
        result.filename = file.filename
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ZIP analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup(zip_path)
        if extract_dir:
            cleanup(extract_dir)
