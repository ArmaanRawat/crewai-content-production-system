"""
utils/job_store.py
─────────────────────────────────────────────────────────────────
Thread-safe, in-memory store for tracking content generation jobs.
Since there is no DB in Phase 1, this acts as the database.
─────────────────────────────────────────────────────────────────
"""

import threading
from typing import Dict, List, Optional
from pydantic import BaseModel

class JobBrief(BaseModel):
    topic: str
    tone: str
    word_count: int
    audience: str
    seo_keywords: List[str] = []
    reference_docs: List[str] = []

class JobRecord(BaseModel):
    job_id: str
    status: str  # 'running', 'success', 'failed'
    created_at: str
    brief: JobBrief
    article: Optional[str] = None
    word_count: int = 0
    quality_score: Optional[float] = None
    quality_passed: Optional[bool] = None
    quality_reasons: List[str] = []
    error: Optional[str] = None

class JobStore:
    """
    Thread-safe storage for monitoring task states.
    """
    def __init__(self):
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def add_job(self, job_id: str, status: str, created_at: str, brief: JobBrief) -> JobRecord:
        with self._lock:
            record = JobRecord(
                job_id=job_id,
                status=status,
                created_at=created_at,
                brief=brief
            )
            self._jobs[job_id] = record
            return record

    def update_job_success(
        self,
        job_id: str,
        article: str,
        word_count: int,
        quality_score: float,
        quality_passed: bool,
        quality_reasons: List[str]
    ) -> Optional[JobRecord]:
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = "success"
                job.article = article
                job.word_count = word_count
                job.quality_score = quality_score
                job.quality_passed = quality_passed
                job.quality_reasons = quality_reasons
                return job
            return None

    def update_job_failure(self, job_id: str, error: str) -> Optional[JobRecord]:
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.status = "failed"
                job.error = error
                return job
            return None

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job.model_copy(deep=True)
            return None

    def list_jobs(self) -> List[JobRecord]:
        with self._lock:
            # Sort jobs newest first
            sorted_jobs = sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True
            )
            return [j.model_copy(deep=True) for j in sorted_jobs]

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()

# Global job store instance
job_store = JobStore()
