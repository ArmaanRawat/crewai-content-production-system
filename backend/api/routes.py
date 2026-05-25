"""
api/routes.py
"""

import time
import asyncio
from functools import partial
from fastapi import APIRouter, HTTPException
from schemas import ContentBriefRequest, ContentResponse
from crews import run_content_crew
from utils.logger import get_logger
from utils.helpers import generate_job_id, utc_now_iso, elapsed_seconds

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=ContentResponse)
async def generate_content(brief: ContentBriefRequest):
    """
    Kick off the content pipeline.
    Runs the crew in a thread executor to avoid event loop conflict.
    """
    job_id = generate_job_id()
    start  = time.time()

    logger.info("Job started", job_id=job_id, topic=brief.topic)

    try:
        # ── Run blocking CrewAI code in a separate thread ─────────────────
        # WHY: FastAPI is async, CrewAI kickoff() is blocking/sync.
        # Running it in an executor prevents blocking the event loop.
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                run_content_crew,
                topic=brief.topic,
                tone=brief.tone,
                word_count=brief.word_count,
                audience=brief.audience,
            )
        )

        elapsed = elapsed_seconds(start)
        logger.info("Job complete", job_id=job_id, elapsed=elapsed)

        return ContentResponse(
            job_id=job_id,
            status="success",
            topic=brief.topic,
            article=result,
            word_count=len(result.split()),
            created_at=utc_now_iso(),
        )

    except Exception as e:
        logger.error("Job failed", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "ok"}