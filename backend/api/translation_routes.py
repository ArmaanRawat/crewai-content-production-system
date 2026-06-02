"""
api/translation_routes.py
─────────────────────────────────────────────────────────────────
FastAPI routes for the Multilingual Translation workflow.
─────────────────────────────────────────────────────────────────
"""

import time
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, validator

from utils.logger import get_logger
from utils.helpers import generate_job_id, utc_now_iso, elapsed_seconds
from utils.job_store import job_store, JobBrief
from crews.translation_crew import run_translation_crew

logger = get_logger(__name__)
router = APIRouter()

SUPPORTED_LANGUAGES: List[str] = [
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Chinese",
    "Japanese",
    "Korean",
    "Arabic",
    "Hindi",
    "Dutch",
    "Russian",
    "Turkish",
    "Polish",
    "Swedish",
]


class TranslationRequest(BaseModel):
    job_id: str
    target_language: str

    @validator("target_language")
    def validate_target_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{v}'. Supported languages: {SUPPORTED_LANGUAGES}"
            )
        return v


def run_translation_background(
    translation_job_id: str,
    article: str,
    target_language: str,
    start_time: float,
):
    """
    Background runner that executes the blocking translation crew,
    updates job_store, and logs progress.
    """
    try:
        translated_article = run_translation_crew(article, target_language)
        elapsed = elapsed_seconds(start_time)
        logger.info(
            "Translation job complete",
            job_id=translation_job_id,
            target_language=target_language,
            elapsed=elapsed,
        )

        word_count = len(translated_article.split())
        job_store.update_job_success(
            job_id=translation_job_id,
            article=translated_article,
            word_count=word_count,
            quality_score=100.0,
            quality_passed=True,
            quality_reasons=[],
        )
    except Exception as e:
        logger.error(
            "Translation job failed in background",
            job_id=translation_job_id,
            error=str(e),
        )
        job_store.update_job_failure(translation_job_id, str(e))


@router.post("/submit")
async def submit_translation(request: TranslationRequest, background_tasks: BackgroundTasks):
    """
    Submit a translation job for an existing content job.
    Looks up the original job, creates a new translation job, and runs it in the background.
    """
    original_job = job_store.get_job(request.job_id)
    if not original_job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {request.job_id} not found",
        )

    article = original_job.get("article") if isinstance(original_job, dict) else getattr(original_job, "article", None)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job {request.job_id} has no article content available. The job may still be running or may have failed.",
        )

    original_topic = ""
    if isinstance(original_job, dict):
        brief = original_job.get("brief")
        if isinstance(brief, dict):
            original_topic = brief.get("topic", "")
        elif brief is not None:
            original_topic = getattr(brief, "topic", "")
    else:
        brief = getattr(original_job, "brief", None)
        if brief is not None:
            original_topic = getattr(brief, "topic", "") if not isinstance(brief, dict) else brief.get("topic", "")

    translation_job_id = generate_job_id()
    created_at = utc_now_iso()
    start = time.time()

    translation_topic = f"Translation [{request.target_language}]: {original_topic}"

    logger.info(
        "Translation job started",
        job_id=translation_job_id,
        original_job_id=request.job_id,
        target_language=request.target_language,
    )

    store_brief = JobBrief(
        topic=translation_topic,
        tone="neutral",
        word_count=0,
        audience="general",
        seo_keywords=[],
        reference_docs=[],
    )
    job_store.add_job(translation_job_id, "running", created_at, store_brief)

    background_tasks.add_task(
        run_translation_background,
        translation_job_id,
        article,
        request.target_language,
        start,
    )

    return {
        "translation_job_id": translation_job_id,
        "status": "running",
        "original_job_id": request.job_id,
        "target_language": request.target_language,
        "created_at": created_at,
    }


@router.get("/jobs/{job_id}")
async def get_translation_job(job_id: str):
    """
    Retrieve details of a specific translation job by ID.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/languages")
async def get_supported_languages():
    """
    Return the list of supported target languages for translation.
    """
    return {"supported_languages": SUPPORTED_LANGUAGES}
