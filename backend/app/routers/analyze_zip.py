"""Router for POST /analyze/zip endpoint."""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.analysis_result import AnalysisResult
from app.services.file_handler import ensure_temp_dir, cleanup
from app.services.zip_handler import extract_zip, read_py_files
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Maksimal ZIP hajmi — 20MB
MAX_ZIP_SIZE = 20 * 1024 * 1024

# ZIP ichida maksimal Python fayl soni
MAX_PY_FILES = 100


@router.post("/zip", response_model=AnalysisResult)
@limiter.limit("10/minute")
async def analyze_zip(request: Request, file: UploadFile = File(...)) -> AnalysisResult:
    """
    Analyze all Python files inside an uploaded ZIP archive.

    Cheklovlar:
    - Daqiqada max 10 ta so'rov (bir IP dan)
    - ZIP hajmi max 20MB
    - ZIP ichida max 100 ta .py fayl
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Faqat .zip kengaytmali fayllar qabul qilinadi."
        )

    temp = ensure_temp_dir()
    zip_path = temp / f"{uuid.uuid4().hex}.zip"
    extract_dir: Path | None = None

    try:
        content = await file.read()

        # ZIP hajmini tekshirish
        if len(content) > MAX_ZIP_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP hajmi {MAX_ZIP_SIZE // (1024*1024)}MB dan oshmasligi kerak."
            )

        zip_path.write_bytes(content)
        logger.info(f"ZIP tahlil qilinmoqda: {file.filename} ({len(content)} bayt)")

        extract_dir, py_files = extract_zip(zip_path)

        # Python fayllar sonini tekshirish
        if len(py_files) > MAX_PY_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP ichida maksimal {MAX_PY_FILES} ta .py fayl bo'lishi mumkin. "
                       f"Topildi: {len(py_files)} ta."
            )

        if not py_files:
            return AnalysisResult(
                status="success",
                filename=file.filename,
                syntax_errors=[],
                security_warnings=[],
                total_files_analyzed=0,
            )

        pairs = read_py_files(py_files, extract_dir)

        from app.main import analysis_semaphore
        async with analysis_semaphore:
            result = build_result(pairs)

        result.filename = file.filename
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ZIP tahlil xatosi: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup(zip_path)
        if extract_dir:
            cleanup(extract_dir)