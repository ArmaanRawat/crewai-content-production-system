"""
agents/writer_agent.py
─────────────────────────────────────────────────────────────────
The Writer Agent — second agent in the pipeline.

RESPONSIBILITY:
  - Receives the research summary from the Researcher Agent
  - Generates a well-structured, engaging article
  - Respects tone, word count, and audience from the brief
─────────────────────────────────────────────────────────────────
"""

import os
from crewai import Agent
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.helpers import get_llm

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
logger = get_logger(__name__)


def build_writer_agent() -> Agent:
    """
    Factory function that constructs and returns the Writer Agent.
    """
    logger.info("Building Writer Agent")

    agent = Agent(
        role="Professional Content Writer",

        goal=(
            "Write a high-quality, engaging article based on the research summary provided. "
            "Match the requested tone, word count, and target audience. "
            "Structure the article with a clear intro, body, and conclusion."
        ),

        backstory=(
            "You are an experienced content writer with a decade of experience "
            "writing for top publications across tech, business, and lifestyle. "
            "You are known for turning complex research into clear, compelling narratives "
            "that keep readers engaged from start to finish. "
            "You always write in the tone and style requested, never improvising on format."
        ),

        tools=[],  # Writer uses no external tools — only the research passed to it

        llm=get_llm(),  # gemini-3.5-flash is too expensive

        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=False,
    )

    logger.info("Writer Agent built successfully")
    return agent