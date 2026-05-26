"""
schemas/response_schema.py
─────────────────────────────────────────────────────────────────
Defines the OUTPUT contract for the content pipeline.

This is what the API always sends back — success or failure.

WHY CONSISTENT RESPONSE SHAPES MATTER:
  - Frontend always knows what structure to expect
  - Errors are predictable and handleable
  - Easy to add fields later without breaking clients
─────────────────────────────────────────────────────────────────
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResearchOutput(BaseModel):
    """
    Structured output from the Researcher Agent.
    Nested inside ContentResponse so the frontend can
    display research and article separately if needed.
    """

    summary: str = Field(description="Key findings from the research phase.")
    sources: list[str] = Field(
        default=[],
        description="URLs or references gathered during research.",
    )


class ContentResponse(BaseModel):
    """
    The full API response returned after a pipeline run.

    SUCCESS shape:
    {
        "job_id": "job_a1b2c3d4e5f6",
        "status": "success",
        "topic": "How AI is transforming healthcare",
        "research": { "summary": "...", "sources": [...] },
        "article": "Full article text here...",
        "word_count": 823,
        "created_at": "2024-01-15T10:30:00Z",
        "error": null
    }

    FAILURE shape:
    {
        "job_id": "job_a1b2c3d4e5f6",
        "status": "failed",
        "topic": "...",
        "research": null,
        "article": null,
        "word_count": 0,
        "created_at": "2024-01-15T10:30:00Z",
        "error": "OpenAI rate limit exceeded"
    }
    """

    job_id: str = Field(description="Unique ID for this pipeline run.")

    status: str = Field(
        description="Pipeline run status: 'success' or 'failed'."
    )

    topic: str = Field(description="The original topic that was requested.")

    research: Optional[ResearchOutput] = Field(
        default=None,
        description="Output from the Researcher Agent.",
    )

    article: Optional[str] = Field(
        default=None,
        description="Final article text from the Writer Agent.",
    )

    word_count: int = Field(
        default=0,
        description="Actual word count of the generated article.",
    )

    created_at: str = Field(
        description="ISO-8601 UTC timestamp of when the job completed.",
    )

    quality_score: Optional[float] = Field(
        default=None,
        description="Aggregated Quality Gate score (0-100).",
    )

    quality_passed: Optional[bool] = Field(
        default=None,
        description="True if article passed all quality gate checks.",
    )

    quality_reasons: Optional[list[str]] = Field(
        default=None,
        description="Detailed list of fail reasons or warnings.",
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if the pipeline failed.",
    )