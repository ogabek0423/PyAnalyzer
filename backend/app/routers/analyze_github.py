
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.analysis_result import AnalysisResult, GithubRequest
from app.services.file_handler import cleanup
from app.services.github_cloner import clone_repo, read_py_files
from app.services.report_generator import build_result

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Klonlash uchun maksimal vaqt — 60 soniya
CLONE_TIMEOUT = 60

# GitHub repodagi maksimal Python fayl soni
MAX_PY_FILES = 200

# Thread pool — git operatsiyalari uchun (bloklash muammosini hal qilish)
_executor = ThreadPoolExecutor(max_workers=3)


def _clone_and_find(repo_url: str):
    """Git klonlash va fayllarni topish (sinxron, thread da ishlaydi)."""
    return clone_repo(repo_url)


@router.post("/github", response_model=AnalysisResult)
@limiter.limit("5/minute")
async def analyze_github(request: Request, body: GithubRequest) -> AnalysisResult:
    """
    Clone a public GitHub repository and analyze all Python files.

    Cheklovlar:
    - Daqiqada max 5 ta so'rov (bir IP dan) — klonlash og'ir operatsiya
    - Klonlash vaqti max 60 soniya
    - Repoda max 200 ta .py fayl tahlil qilinadi
    """
    clone_dir: Path | None = None

    try:
        logger.info(f"GitHub repo tahlili boshlandi: {body.repo_url}")

        # Klonlashni thread pool da, timeout bilan bajarish
        loop = asyncio.get_event_loop()
        try:
            clone_dir, py_files = await asyncio.wait_for(
                loop.run_in_executor(_executor, _clone_and_find, body.repo_url),
                timeout=CLONE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"Klonlash vaqti tugadi: {body.repo_url}")
            raise HTTPException(
                status_code=408,
                detail=f"Klonlash {CLONE_TIMEOUT} soniyadan ko'p vaqt oldi. "
                       "Kichikroq repozitoriyani sinab ko'ring."
            )

        # Python fayllar sonini tekshirish
        if len(py_files) > MAX_PY_FILES:
            logger.warning(
                f"Repo da juda ko'p fayl: {len(py_files)} ta. "
                f"Faqat birinchi {MAX_PY_FILES} tasi tahlil qilinadi."
            )
            py_files = py_files[:MAX_PY_FILES]

        if not py_files:
            return AnalysisResult(
                status="success",
                filename=body.repo_url,
                syntax_errors=[],
                security_warnings=[],
                total_files_analyzed=0,
            )

        pairs = read_py_files(py_files, clone_dir)

        from app.main import analysis_semaphore
        async with analysis_semaphore:
            result = build_result(pairs)

        result.filename = body.repo_url
        logger.info(f"GitHub tahlil yakunlandi: {len(pairs)} fayl")
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"GitHub tahlil xatosi: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if clone_dir:
            cleanup(clone_dir)