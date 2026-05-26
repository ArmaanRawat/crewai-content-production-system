"""
schemas/content_schema.py
─────────────────────────────────────────────────────────────────
Defines the INPUT contract for the content pipeline.

This is what the user sends to the API when they want
to generate a piece of content.

WHY THIS EXISTS SEPARATELY:
  - Keeps validation logic out of routes and agents
  - Single source of truth for what a "brief" looks like
  - Easy to extend later (add SEO keywords, language, etc.)
─────────────────────────────────────────────────────────────────
"""

from pydantic import BaseModel, Field
from typing import Literal


class ContentBriefRequest(BaseModel):
    """
    The content brief a user submits to kick off the pipeline.

    Example payload:
    {
        "topic": "How AI is transforming healthcare",
        "tone": "professional",
        "word_count": 800,
        "audience": "tech decision-makers"
    }
    """

    topic: str = Field(
        ...,                          # required — no default
        min_length=5,
        max_length=500,
        description="The subject the agents will research and write about.",
        examples=["How AI is transforming healthcare diagnostics"],
    )

    tone: Literal["professional", "casual", "academic", "persuasive"] = Field(
        default="professional",
        description="The writing tone for the final article.",
    )

    word_count: int = Field(
        default=800,
        ge=200,       # minimum 200 words
        le=3000,      # maximum 3000 words
        description="Target word count for the article.",
    )

    audience: str = Field(
        default="general readers",
        max_length=200,
        description="Who the content is written for.",
    )

    seo_keywords: list[str] = Field(
        default=[],
        description="Target keywords for SEO optimization checking.",
    )

    reference_docs: list[str] = Field(
        default=[],
        description="Reference source documents to check for plagiarism.",
    )