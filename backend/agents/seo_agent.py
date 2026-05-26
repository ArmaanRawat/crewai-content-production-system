"""
agents/seo_agent.py
─────────────────────────────────────────────────────────────────
The SEO Optimizer Agent — fourth agent in the pipeline.

RESPONSIBILITY:
  - Receives the edited article from the Editor Agent
  - Optimizes it for search engines
  - Adds/improves keywords, meta description, headings
  - Ensures readability score is high
  - Does NOT change the core content or tone
─────────────────────────────────────────────────────────────────
"""

import os
from crewai import Agent
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.helpers import get_llm

load_dotenv()
logger = get_logger(__name__)


def build_seo_agent() -> Agent:
    """
    Factory function that constructs and returns the SEO Agent.
    """
    logger.info("Building SEO Agent")

    agent = Agent(
        role="SEO Optimization Specialist",

        goal=(
            "Optimize the edited article for search engines without compromising quality. "
            "Identify and naturally integrate relevant keywords. "
            "Improve headings, meta description, and structure for SEO. "
            "Ensure the article ranks well while remaining engaging for human readers."
        ),

        backstory=(
            "You are an SEO specialist with 10 years of experience helping content "
            "rank on the first page of Google. You understand both search algorithms "
            "and human psychology. You never keyword-stuff — you integrate keywords "
            "naturally and strategically. You know that good SEO starts with good content, "
            "and your job is to make great content discoverable."
        ),

        tools=[],

        llm=get_llm(),

        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=False,
    )

    logger.info("SEO Agent built successfully")
    return agent