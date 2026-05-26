"""
api/routes.py
─────────────────────────────────────────────────────────────────
FastAPI routes for content generation, job monitoring,
real-time log streaming, and automated technical documentation.
─────────────────────────────────────────────────────────────────
"""

import time
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from schemas import ContentBriefRequest, ContentResponse
from crews import run_content_crew
from utils.logger import get_logger, register_listener, unregister_listener
from utils.helpers import generate_job_id, utc_now_iso, elapsed_seconds
from utils.quality_gate import QualityGate
from utils.job_store import job_store, JobBrief

logger = get_logger(__name__)
router = APIRouter()


def _execute_pipeline(brief: ContentBriefRequest):
    """
    Synchronous helper to run the CrewAI content crew and Quality Gate check.
    This runs entirely within the thread pool executor.
    """
    # 1. Run Content Crew (Researcher -> Writer)
    article = run_content_crew(
        topic=brief.topic,
        tone=brief.tone,
        word_count=brief.word_count,
        audience=brief.audience,
    )

    # 2. Run Quality Gate Checks
    gate = QualityGate()
    keywords = brief.seo_keywords if brief.seo_keywords else [brief.topic]
    gate_res = gate.evaluate(article, keywords, brief.reference_docs)

    return article, gate_res


def run_pipeline_background(job_id: str, brief: ContentBriefRequest, created_at: str, start_time: float):
    """
    Background runner that executes the blocking pipeline,
    updates job_store, and logs progress.
    """
    try:
        article, gate_res = _execute_pipeline(brief)
        elapsed = elapsed_seconds(start_time)
        logger.info("Job complete", job_id=job_id, elapsed=elapsed)

        word_count = len(article.split())
        job_store.update_job_success(
            job_id=job_id,
            article=article,
            word_count=word_count,
            quality_score=gate_res.score,
            quality_passed=gate_res.passed,
            quality_reasons=gate_res.reasons
        )
    except Exception as e:
        logger.error("Job failed in background", job_id=job_id, error=str(e))
        job_store.update_job_failure(job_id, str(e))


@router.post("/generate", response_model=ContentResponse)
async def generate_content(brief: ContentBriefRequest, background_tasks: BackgroundTasks):
    """
    Kick off the content pipeline and evaluate via Quality Gate.
    Registers job state before execution and updates it upon completion.
    """
    job_id = generate_job_id()
    created_at = utc_now_iso()
    start = time.time()

    logger.info("Job started", job_id=job_id, topic=brief.topic)

    # Register job in store
    store_brief = JobBrief(
        topic=brief.topic,
        tone=brief.tone,
        word_count=brief.word_count,
        audience=brief.audience,
        seo_keywords=brief.seo_keywords,
        reference_docs=brief.reference_docs
    )
    job_store.add_job(job_id, "running", created_at, store_brief)

    # Add pipeline execution to background tasks
    background_tasks.add_task(
        run_pipeline_background,
        job_id,
        brief,
        created_at,
        start
    )

    return ContentResponse(
        job_id=job_id,
        status="running",
        topic=brief.topic,
        created_at=created_at,
    )


@router.get("/jobs")
async def list_jobs():
    """
    Retrieve list of all content generation jobs and their states.
    """
    return job_store.list_jobs()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Retrieve details of a specific job by ID.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/docs")
async def get_docs():
    """
    Retrieve the current project markdown documentation.
    """
    docs_path = Path(__file__).parent.parent.parent / "docs" / "architecture_and_api.md"
    if not docs_path.exists():
        try:
            from utils.doc_generator import generate_docs
            content = generate_docs()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Documentation file not found and automatic generation failed: {e}"
            )
    else:
        with open(docs_path, "r", encoding="utf-8") as f:
            content = f.read()
    
    return {
        "status": "success",
        "content": content
    }


@router.post("/docs/generate")
async def trigger_docs_generation():
    """
    Manually trigger regeneration of technical documentation.
    """
    try:
        from utils.doc_generator import generate_docs
        content = generate_docs()
        return {
            "status": "success",
            "message": "Technical documentation regenerated successfully",
            "content": content
        }
    except Exception as e:
        logger.error("Failed to generate documentation via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stream")
async def stream_logs():
    """
    Stream live application logs in real-time via Server-Sent Events (SSE).
    """
    queue = asyncio.Queue()
    register_listener(queue)

    async def log_generator():
        try:
            yield "data: [SYSTEM] Connected to real-time agent activity log stream\n\n"
            while True:
                log_line = await queue.get()
                yield f"data: {log_line}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unregister_listener(queue)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    return {"status": "ok"}