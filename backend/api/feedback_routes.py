"""
api/feedback_routes.py
─────────────────────────────────────────────────────────────────
FastAPI routes for the Client Feedback workflow.
Accepts feedback on a previously generated article, kicks off a
revision crew in the background, and exposes job status polling.
─────────────────────────────────────────────────────────────────
"""

import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.helpers import generate_job_id, utc_now_iso, elapsed_seconds
from utils.job_store import job_store, JobBrief
from crews.feedback_crew import run_feedback_crew

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    job_id: str = Field(..., description="The original content job ID whose article should be revised")
    feedback: str = Field(..., min_length=10, max_length=2000, description="Client feedback describing the desired revisions")


# ---------------------------------------------------------------------------
# Background runner
# ---------------------------------------------------------------------------

def run_feedback_pipeline_background(
    feedback_job_id: str,
    article: str,
    feedback: str,
    start_time: float,
):
    """
    Synchronous background runner that calls the feedback crew and updates
    the job store on completion or failure.
    """
    try:
        revised_article = run_feedback_crew(article, feedback)
        elapsed = elapsed_seconds(start_time)
        logger.info("Feedback job complete", job_id=feedback_job_id, elapsed=elapsed)

        word_count = len(revised_article.split())
        job_store.update_job_success(
            job_id=feedback_job_id,
            article=revised_article,
            word_count=word_count,
            quality_score=None,
            quality_passed=None,
            quality_reasons=[],
        )
    except Exception as e:
        logger.error("Feedback job failed in background", job_id=feedback_job_id, error=str(e))
        job_store.update_job_failure(feedback_job_id, str(e))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/submit")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Submit client feedback for an existing article and kick off a revision.

    Looks up the original job, extracts its article, creates a new feedback
    job, and runs the feedback crew in a background thread.
    """
    original_job = job_store.get_job(request.job_id)
    if not original_job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {request.job_id} not found",
        )

    if original_job.article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job {request.job_id} has no article to revise (status: {original_job.status})",
        )

    feedback_job_id = generate_job_id()
    created_at = utc_now_iso()
    start = time.time()

    logger.info(
        "Feedback job started",
        feedback_job_id=feedback_job_id,
        original_job_id=request.job_id,
        original_topic=original_job.brief.topic,
    )

    # Register the new feedback job in the store, reusing the original brief
    # fields but marking it as a revision.
    feedback_brief = JobBrief(
        topic=f"Feedback revision for: {original_job.brief.topic}",
        tone=original_job.brief.tone,
        word_count=original_job.brief.word_count,
        audience=original_job.brief.audience,
        seo_keywords=original_job.brief.seo_keywords,
        reference_docs=original_job.brief.reference_docs,
    )
    job_store.add_job(feedback_job_id, "running", created_at, feedback_brief)

    background_tasks.add_task(
        run_feedback_pipeline_background,
        feedback_job_id,
        original_job.article,
        request.feedback,
        start,
    )

    return {
        "feedback_job_id": feedback_job_id,
        "status": "running",
        "original_job_id": request.job_id,
        "created_at": created_at,
    }


@router.get("/jobs/{job_id}")
async def get_feedback_job(job_id: str):
    """
    Retrieve details of a specific feedback (or content) job by ID.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job
