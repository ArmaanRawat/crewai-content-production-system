"""
api/calender_routes.py
─────────────────────────────────────────────────────────────────
FastAPI routes for the Content Calendar workflow.
─────────────────────────────────────────────────────────────────
"""

import time
from typing import Literal

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.helpers import generate_job_id, utc_now_iso, elapsed_seconds
from utils.job_store import job_store, JobBrief
from crews.calendar_crew import run_calendar_crew

logger = get_logger(__name__)
router = APIRouter()


class CalendarRequest(BaseModel):
    niche: str = Field(..., min_length=3, max_length=200)
    audience: str = Field(default="general readers", max_length=200)
    frequency: Literal["daily", "3x per week", "weekly", "biweekly"] = "weekly"
    weeks: int = Field(default=4, ge=1, le=12)


def run_calendar_background(
    job_id: str,
    niche: str,
    audience: str,
    frequency: str,
    weeks: int,
    start_time: float,
):
    """
    Background runner that executes the calendar crew pipeline,
    updates job_store, and logs progress.
    """
    try:
        calendar_text = run_calendar_crew(niche, audience, frequency, weeks)
        elapsed = elapsed_seconds(start_time)
        logger.info("Calendar job complete", job_id=job_id, elapsed=elapsed)

        job_store.update_job_success(
            job_id=job_id,
            article=calendar_text,
            word_count=len(calendar_text.split()),
            quality_score=100.0,
            quality_passed=True,
            quality_reasons=[],
        )
    except Exception as e:
        logger.error("Calendar job failed in background", job_id=job_id, error=str(e))
        job_store.update_job_failure(job_id, str(e))


@router.post("/generate")
async def generate_calendar(request: CalendarRequest, background_tasks: BackgroundTasks):
    """
    Kick off the content calendar pipeline.
    Registers job state before execution and updates it upon completion.
    """
    calendar_job_id = generate_job_id()
    created_at = utc_now_iso()
    start = time.time()

    topic = f"Content Calendar: {request.niche} ({request.weeks} weeks)"
    logger.info("Calendar job started", job_id=calendar_job_id, topic=topic)

    store_brief = JobBrief(
        topic=topic,
        tone="informational",
        word_count=0,
        audience=request.audience,
        seo_keywords=[],
        reference_docs=[],
    )
    job_store.add_job(calendar_job_id, "running", created_at, store_brief)

    background_tasks.add_task(
        run_calendar_background,
        calendar_job_id,
        request.niche,
        request.audience,
        request.frequency,
        request.weeks,
        start,
    )

    return {
        "calendar_job_id": calendar_job_id,
        "status": "running",
        "niche": request.niche,
        "weeks": request.weeks,
        "frequency": request.frequency,
        "created_at": created_at,
    }


@router.get("/jobs/{job_id}")
async def get_calendar_job(job_id: str):
    """
    Retrieve details of a specific calendar job by ID.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job
