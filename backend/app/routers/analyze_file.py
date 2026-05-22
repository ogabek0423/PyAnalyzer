"""Router for POST /analyze/file endpoint."""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.analysis_result import AnalysisResult
from app.services.file_handler import ensure_temp_dir, cleanup
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Maksimal fayl hajmi — 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/file", response_model=AnalysisResult)
@limiter.limit("15/minute")
async def analyze_file(request: Request, file: UploadFile = File(...)) -> AnalysisResult:
    """
    Analyze a single uploaded .py file.

    Cheklovlar:
    - Daqiqada max 15 ta so'rov (bir IP dan)
    - Fayl hajmi max 5MB
    - Faqat .py kengaytmali fayllar
    """
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400,
            detail="Faqat .py kengaytmali fayllar qabul qilinadi."
        )

    temp = ensure_temp_dir()
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest = temp / safe_name

    try:
        content = await file.read()

        # Fayl hajmini tekshirish
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Fayl hajmi {MAX_FILE_SIZE // (1024*1024)}MB dan oshmasligi kerak."
            )

        dest.write_bytes(content)
        code = content.decode("utf-8", errors="replace")

        logger.info(f"Fayl tahlil qilinmoqda: {file.filename} ({len(content)} bayt)")

        from app.main import analysis_semaphore
        async with analysis_semaphore:
            result = build_result([(file.filename, code)])

        result.filename = file.filename
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fayl tahlil xatosi: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup(dest)