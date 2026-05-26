"""
agents/editor_agent.py
─────────────────────────────────────────────────────────────────
The Editor Agent — third agent in the pipeline.

RESPONSIBILITY:
  - Receives the draft article from the Writer Agent
  - Refines tone, clarity, grammar, and structure
  - Ensures the article matches the requested tone and audience
  - Returns a polished, publication-ready article
─────────────────────────────────────────────────────────────────
"""

import os
from crewai import Agent
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.helpers import get_llm

load_dotenv()
logger = get_logger(__name__)


def build_editor_agent() -> Agent:
    """
    Factory function that constructs and returns the Editor Agent.
    """
    logger.info("Building Editor Agent")

    agent = Agent(
        role="Senior Content Editor",

        goal=(
            "Review and refine the draft article provided by the Writer Agent. "
            "Improve clarity, flow, grammar, and structure. "
            "Ensure the tone matches the brief exactly. "
            "Make it engaging, tight, and publication-ready without changing core facts."
        ),

        backstory=(
            "You are a senior editor with 20 years of experience at top-tier publications. "
            "You have an exceptional eye for weak sentences, tonal inconsistencies, "
            "and structural problems. You never rewrite from scratch — you refine. "
            "You cut filler, sharpen arguments, and make every word count. "
            "You preserve the writer's voice while elevating the overall quality."
        ),

        tools=[],  # Editor works only on the text passed to it

        llm=get_llm(),

        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=False,
    )

    logger.info("Editor Agent built successfully")
    return agent