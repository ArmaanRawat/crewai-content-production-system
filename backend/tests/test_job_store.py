"""
tests/test_job_store.py
─────────────────────────────────────────────────────────────────
Unit tests for the thread-safe in-memory JobStore.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from datetime import datetime

# Adjust path to import backend modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.job_store import JobStore, JobBrief, JobRecord


class TestJobStore(unittest.TestCase):
    """
    Unit tests for utils.job_store.JobStore.
    """

    def setUp(self):
        self.store = JobStore()
        self.brief = JobBrief(
            topic="Blockchain Technology",
            tone="professional",
            word_count=500,
            audience="developers",
            seo_keywords=["blockchain"],
            reference_docs=[]
        )

    def test_add_job(self):
        """
        Verify that add_job successfully adds a job to the store with 'running' status.
        """
        job = self.store.add_job("job_123", "running", "2026-05-26T10:00:00Z", self.brief)
        self.assertIsNotNone(job)
        self.assertEqual(job.job_id, "job_123")
        self.assertEqual(job.status, "running")
        self.assertEqual(job.brief.topic, "Blockchain Technology")

        # Verify we can retrieve it
        retrieved = self.store.get_job("job_123")
        self.assertEqual(retrieved.job_id, "job_123")

    def test_update_job_success(self):
        """
        Verify that updating a job for success changes status and stores quality scores.
        """
        self.store.add_job("job_123", "running", "2026-05-26T10:00:00Z", self.brief)
        updated = self.store.update_job_success(
            job_id="job_123",
            article="Some content",
            word_count=2,
            quality_score=95.0,
            quality_passed=True,
            quality_reasons=[]
        )
        self.assertEqual(updated.status, "success")
        self.assertEqual(updated.article, "Some content")
        self.assertEqual(updated.word_count, 2)
        self.assertEqual(updated.quality_score, 95.0)
        self.assertEqual(updated.quality_passed, True)

        # Check retrieval matches
        retrieved = self.store.get_job("job_123")
        self.assertEqual(retrieved.status, "success")

    def test_update_job_failure(self):
        """
        Verify that updating a job for failure changes status and stores the error message.
        """
        self.store.add_job("job_123", "running", "2026-05-26T10:00:00Z", self.brief)
        updated = self.store.update_job_failure("job_123", "Rate limit exceeded")
        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.error, "Rate limit exceeded")

        # Check retrieval matches
        retrieved = self.store.get_job("job_123")
        self.assertEqual(retrieved.status, "failed")
        self.assertEqual(retrieved.error, "Rate limit exceeded")

    def test_list_jobs_sorting(self):
        """
        Verify that list_jobs returns jobs sorted by creation time (newest first).
        """
        self.store.add_job("job_old", "running", "2026-05-26T10:00:00Z", self.brief)
        self.store.add_job("job_new", "running", "2026-05-26T11:00:00Z", self.brief)
        
        jobs_list = self.store.list_jobs()
        self.assertEqual(len(jobs_list), 2)
        self.assertEqual(jobs_list[0].job_id, "job_new")
        self.assertEqual(jobs_list[1].job_id, "job_old")


if __name__ == "__main__":
    unittest.main()
