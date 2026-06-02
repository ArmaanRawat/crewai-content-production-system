"""
tests/test_e2e.py
─────────────────────────────────────────────────────────────────
End-to-end tests for the feedback, translation, and calendar API routes.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from utils.job_store import job_store, JobBrief

# Register the new routers onto the app if not already present.
# This mirrors how they will be mounted in production.
from api.feedback_routes import router as feedback_router
from api.translation_routes import router as translation_router
from api.calender_routes import router as calendar_router

_registered_prefixes = {route.path for route in app.routes}

def _prefix_already_mounted(prefix: str) -> bool:
    return any(
        getattr(route, "path", "").startswith(prefix)
        for route in app.routes
    )

if not _prefix_already_mounted("/api/v1/feedback"):
    app.include_router(feedback_router, prefix="/api/v1/feedback")

if not _prefix_already_mounted("/api/v1/translation"):
    app.include_router(translation_router, prefix="/api/v1/translation")

if not _prefix_already_mounted("/api/v1/calendar"):
    app.include_router(calendar_router, prefix="/api/v1/calendar")


# ---------------------------------------------------------------------------
# TestFeedbackRoutes
# ---------------------------------------------------------------------------

class TestFeedbackRoutes(unittest.TestCase):
    """
    End-to-end tests for the /api/v1/feedback routes.
    """

    def setUp(self):
        self.client = TestClient(app)
        job_store.clear()

        # Add a completed test job with article content.
        brief = JobBrief(
            topic="Test Article",
            tone="professional",
            word_count=500,
            audience="general",
        )
        job_store.add_job("test_job_001", "success", "2026-06-01T10:00:00Z", brief)
        job_store._jobs["test_job_001"].article = "This is a test article about technology."

    @patch("api.feedback_routes.run_feedback_crew")
    def test_feedback_submit_success(self, mock_run_feedback_crew):
        """
        POST /api/v1/feedback/submit with a valid job_id and feedback text
        should return 200, status 'running', feedback_job_id, and original_job_id.
        """
        mock_run_feedback_crew.return_value = "This is a revised article about technology."

        payload = {
            "job_id": "test_job_001",
            "feedback": "Please make the article more concise and add more examples.",
        }
        response = self.client.post("/api/v1/feedback/submit", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("feedback_job_id", data)
        self.assertIsNotNone(data["feedback_job_id"])
        self.assertIn("original_job_id", data)
        self.assertEqual(data["original_job_id"], "test_job_001")

    def test_feedback_submit_job_not_found(self):
        """
        POST /api/v1/feedback/submit with a nonexistent job_id should return 404.
        """
        payload = {
            "job_id": "nonexistent_job_999",
            "feedback": "Please improve the introduction section significantly.",
        }
        response = self.client.post("/api/v1/feedback/submit", json=payload)

        self.assertEqual(response.status_code, 404)

    def test_feedback_submit_no_article(self):
        """
        POST /api/v1/feedback/submit for a job that has no article (still running)
        should return 404.
        """
        brief = JobBrief(
            topic="In-Progress Article",
            tone="casual",
            word_count=300,
            audience="general",
        )
        job_store.add_job("running_job_002", "running", "2026-06-01T11:00:00Z", brief)
        # Do not set article — it remains None.

        payload = {
            "job_id": "running_job_002",
            "feedback": "Please improve the writing style throughout the piece.",
        }
        response = self.client.post("/api/v1/feedback/submit", json=payload)

        self.assertEqual(response.status_code, 404)

    def test_feedback_get_job(self):
        """
        GET /api/v1/feedback/jobs/{job_id} for an existing job should return 200
        and the correct job_id.
        """
        response = self.client.get("/api/v1/feedback/jobs/test_job_001")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "test_job_001")


# ---------------------------------------------------------------------------
# TestTranslationRoutes
# ---------------------------------------------------------------------------

class TestTranslationRoutes(unittest.TestCase):
    """
    End-to-end tests for the /api/v1/translation routes.
    """

    def setUp(self):
        self.client = TestClient(app)
        job_store.clear()

        # Add a completed test job with article content.
        brief = JobBrief(
            topic="Test Article",
            tone="professional",
            word_count=500,
            audience="general",
        )
        job_store.add_job("test_job_001", "success", "2026-06-01T10:00:00Z", brief)
        job_store._jobs["test_job_001"].article = "This is a test article about technology."

    @patch("api.translation_routes.run_translation_crew")
    def test_translation_submit_success(self, mock_run_translation_crew):
        """
        POST /api/v1/translation/submit with a valid job_id and supported language
        should return 200, status 'running', translation_job_id, and target_language.
        """
        mock_run_translation_crew.return_value = "Este es un articulo de prueba sobre tecnologia."

        payload = {
            "job_id": "test_job_001",
            "target_language": "Spanish",
        }
        response = self.client.post("/api/v1/translation/submit", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("translation_job_id", data)
        self.assertIsNotNone(data["translation_job_id"])
        self.assertEqual(data["target_language"], "Spanish")

    def test_translation_unsupported_language(self):
        """
        POST /api/v1/translation/submit with an unsupported target_language
        should return a 4xx error. FastAPI/Pydantic raises a validation error
        (422) when the @validator rejects the language value.
        """
        payload = {
            "job_id": "test_job_001",
            "target_language": "Klingon",
        }
        response = self.client.post("/api/v1/translation/submit", json=payload)

        self.assertIn(response.status_code, (400, 422))

    def test_translation_job_not_found(self):
        """
        POST /api/v1/translation/submit with a nonexistent job_id should return 404.
        """
        payload = {
            "job_id": "nonexistent_job_999",
            "target_language": "French",
        }
        response = self.client.post("/api/v1/translation/submit", json=payload)

        self.assertEqual(response.status_code, 404)

    def test_get_supported_languages(self):
        """
        GET /api/v1/translation/languages should return 200 and a list that
        includes at least 'Spanish' and 'French'.
        """
        response = self.client.get("/api/v1/translation/languages")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # The route returns {"supported_languages": [...]}
        languages = data.get("supported_languages", data)
        if isinstance(languages, dict):
            languages = list(languages.values())
        # Flatten in case it is nested.
        if languages and isinstance(languages[0], list):
            languages = languages[0]
        self.assertIn("Spanish", languages)
        self.assertIn("French", languages)

    def test_translation_get_job(self):
        """
        GET /api/v1/translation/jobs/{job_id} for an existing job should return 200.
        """
        response = self.client.get("/api/v1/translation/jobs/test_job_001")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "test_job_001")


# ---------------------------------------------------------------------------
# TestCalendarRoutes
# ---------------------------------------------------------------------------

class TestCalendarRoutes(unittest.TestCase):
    """
    End-to-end tests for the /api/v1/calendar routes.
    """

    def setUp(self):
        self.client = TestClient(app)
        job_store.clear()

    @patch("api.calender_routes.run_calendar_crew")
    def test_calendar_generate_success(self, mock_run_calendar_crew):
        """
        POST /api/v1/calendar/generate with valid input should return 200,
        status 'running', and include calendar_job_id, niche, and weeks.
        """
        mock_run_calendar_crew.return_value = "Week 1: Topic A\nWeek 2: Topic B\nWeek 3: Topic C\nWeek 4: Topic D"

        payload = {
            "niche": "Tech Startups",
            "audience": "founders",
            "frequency": "weekly",
            "weeks": 4,
        }
        response = self.client.post("/api/v1/calendar/generate", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("calendar_job_id", data)
        self.assertIsNotNone(data["calendar_job_id"])
        self.assertEqual(data["niche"], "Tech Startups")
        self.assertEqual(data["weeks"], 4)

    def test_calendar_invalid_weeks(self):
        """
        POST /api/v1/calendar/generate with weeks=15 (exceeds max of 12)
        should return 422 (Unprocessable Entity).
        """
        payload = {
            "niche": "Tech Startups",
            "audience": "founders",
            "frequency": "weekly",
            "weeks": 15,
        }
        response = self.client.post("/api/v1/calendar/generate", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_calendar_get_job(self):
        """
        GET /api/v1/calendar/jobs/{job_id} for an existing job should return 200.
        """
        brief = JobBrief(
            topic="Content Calendar: Tech Startups (4 weeks)",
            tone="informational",
            word_count=0,
            audience="founders",
        )
        job_store.add_job("calendar_job_001", "running", "2026-06-01T10:00:00Z", brief)

        response = self.client.get("/api/v1/calendar/jobs/calendar_job_001")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "calendar_job_001")

    def test_calendar_job_not_found(self):
        """
        GET /api/v1/calendar/jobs/{job_id} for a nonexistent job should return 404.
        """
        response = self.client.get("/api/v1/calendar/jobs/nonexistent_calendar_job")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
