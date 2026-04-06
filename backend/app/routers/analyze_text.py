"""Router for POST /analyze/text endpoint."""
import logging

from fastapi import APIRouter, HTTPException

from app.models.analysis_result import AnalysisResult, TextRequest
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/text", response_model=AnalysisResult)
async def analyze_text(request: TextRequest) -> AnalysisResult:
    """
    Analyze Python code submitted as plain text.

    Args:
        request: JSON body containing the Python code string.

    Returns:
        AnalysisResult with syntax errors and security warnings.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    logger.info("Analyzing text code submission")
    result = build_result([("code.py", request.code)])
    result.filename = "code.py"
    return result
