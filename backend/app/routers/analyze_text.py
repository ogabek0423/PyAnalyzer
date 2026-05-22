"""Router for POST /analyze/text endpoint."""
import logging

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.analysis_result import AnalysisResult, TextRequest
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Maksimal kod uzunligi — 500KB
MAX_CODE_SIZE = 500 * 1024


@router.post("/text", response_model=AnalysisResult)
@limiter.limit("20/minute")
async def analyze_text(request: Request, body: TextRequest) -> AnalysisResult:
    """
    Analyze Python code submitted as plain text.

    Cheklovlar:
    - Daqiqada max 20 ta so'rov (bir IP dan)
    - Kod hajmi max 500KB
    """
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="Kod bo'sh bo'lmasligi kerak.")

    # Kod hajmini tekshirish
    if len(body.code.encode("utf-8")) > MAX_CODE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Kod hajmi {MAX_CODE_SIZE // 1024}KB dan oshmasligi kerak."
        )

    logger.info("Matn kodi tahlil qilinmoqda")

    from app.main import analysis_semaphore
    async with analysis_semaphore:
        result = build_result([("code.py", body.code)])

    result.filename = "code.py"
    return result