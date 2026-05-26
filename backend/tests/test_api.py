"""
tests/test_api.py
─────────────────────────────────────────────────────────────────
Unit tests for the FastAPI API endpoints.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to import app
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from utils.quality_gate import QualityGateResponse
from utils.job_store import job_store, JobBrief


class TestAPI(unittest.TestCase):
    """
    Unit tests for API routes.
    """

    def setUp(self):
        self.client = TestClient(app)
        job_store.clear()

    def test_health_check(self):
        """
        Verify that the health check endpoint returns 200 and OK.
        """
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("api.routes._execute_pipeline")
    def test_generate_endpoint_success(self, mock_execute):
        """
        Verify that the generate endpoint successfully triggers the pipeline
        and returns the correct structured response with Quality Gate metrics,
        and registers the job in JobStore.
        """
        # Mock pipeline output
        mock_article = "# Test Headline\nThis is a mock article."
        mock_gate_res = QualityGateResponse(
            passed=True,
            score=88.5,
            grammar_passed=True,
            grammar_errors_count=1,
            seo_passed=True,
            seo_score=80.0,
            plagiarism_passed=True,
            plagiarism_score=0.0,
            reasons=[]
        )
        mock_execute.return_value = (mock_article, mock_gate_res)

        payload = {
            "topic": "Latest tech trends",
            "tone": "casual",
            "word_count": 500,
            "audience": "young adults",
            "seo_keywords": ["tech"],
            "reference_docs": ["Some existing text."]
        }

        response = self.client.post("/api/v1/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["topic"], "Latest tech trends")
        self.assertEqual(data["article"], mock_article)
        self.assertEqual(data["word_count"], 8)
        self.assertEqual(data["quality_score"], 88.5)
        self.assertEqual(data["quality_passed"], True)
        self.assertEqual(data["quality_reasons"], [])
        self.assertIsNotNone(data["job_id"])
        self.assertIsNotNone(data["created_at"])

        # Check that it was saved to the store
        job = job_store.get_job(data["job_id"])
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "success")
        self.assertEqual(job.brief.topic, "Latest tech trends")

    def test_list_jobs(self):
        """
        Verify that list_jobs endpoint returns all registered jobs.
        """
        brief = JobBrief(topic="Test topic", tone="casual", word_count=200, audience="general")
        job_store.add_job("job_abc", "running", "2026-05-26T10:00:00Z", brief)

        response = self.client.get("/api/v1/jobs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["job_id"], "job_abc")
        self.assertEqual(data[0]["status"], "running")

    def test_get_job_success(self):
        """
        Verify that retrieve job endpoint works.
        """
        brief = JobBrief(topic="Test topic", tone="casual", word_count=200, audience="general")
        job_store.add_job("job_abc", "running", "2026-05-26T10:00:00Z", brief)

        response = self.client.get("/api/v1/jobs/job_abc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "job_abc")
        self.assertEqual(data["status"], "running")

    def test_get_job_not_found(self):
        """
        Verify that retrieving a non-existent job returns 404.
        """
        response = self.client.get("/api/v1/jobs/non_existent_id")
        self.assertEqual(response.status_code, 404)

    def test_get_docs(self):
        """
        Verify that docs retrieval endpoint succeeds and returns documentation markdown.
        """
        response = self.client.get("/api/v1/docs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("content", data)
        self.assertIn("# Automated Technical Documentation", data["content"])

    def test_trigger_docs_generation(self):
        """
        Verify that POST doc generation endpoint regenerates and returns markdown.
        """
        response = self.client.post("/api/v1/docs/generate")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("content", data)

    def test_stream_logs_endpoint(self):
        """
        Verify that the stream logs endpoint returns a StreamingResponse with the SSE MIME type.
        """
        import asyncio
        with patch("asyncio.Queue.get", side_effect=asyncio.CancelledError):
            with self.client.stream("GET", "/api/v1/logs/stream") as response:
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
                # Read first chunk of streaming response (initial system connect message)

                lines = response.iter_lines()
                first_line = next(lines)
                self.assertIn("[SYSTEM] Connected to real-time agent activity log stream", first_line)


if __name__ == "__main__":
    unittest.main()

