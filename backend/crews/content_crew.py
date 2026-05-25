"""
crews/content_crew.py
─────────────────────────────────────────────────────────────────
The Content Crew — wires agents and tasks into a pipeline.

WHAT A CREW IS:
  - A group of agents working together on a set of tasks
  - Manages task execution order
  - Passes output from one agent to the next

PROCESS TYPES:
  - sequential → tasks run one after another (what we use)
  - hierarchical → a manager agent delegates to others (Phase 2)
─────────────────────────────────────────────────────────────────
"""

from crewai import Crew, Process
from tasks import build_research_task, build_writing_task
from utils.logger import get_logger

logger = get_logger(__name__)


def build_content_crew(
    topic: str,
    tone: str,
    word_count: int,
    audience: str,
) -> Crew:
    """
    Builds and returns the content production crew.

    Args:
        topic:       What to research and write about
        tone:        Writing tone (professional/casual/etc)
        word_count:  Target article length
        audience:    Who the article is for

    Returns:
        A configured crewai.Crew ready to run
    """
    logger.info("Building Content Crew", topic=topic)

    # ── Build tasks (agents are embedded inside tasks) ────────────────────────
    research_task = build_research_task(topic, audience)
    writing_task  = build_writing_task(topic, tone, word_count, audience)

    # ── Assemble the crew ─────────────────────────────────────────────────────
    crew = Crew(
        agents=[
            research_task.agent,   # Researcher
            writing_task.agent,    # Writer
        ],
        tasks=[
            research_task,         # runs first
            writing_task,          # runs second, gets research output automatically
        ],
        process=Process.sequential,  # one task at a time, in order
        verbose=True,
    )

    logger.info("Content Crew built successfully")
    return crew


def run_content_crew(
    topic: str,
    tone: str = "professional",
    word_count: int = 800,
    audience: str = "general readers",
) -> str:
    """
    Builds and runs the crew. Returns the final article as a string.

    This is the single function the API route will call.
    """
    logger.info("Running Content Crew", topic=topic, tone=tone)

    crew = build_content_crew(topic, tone, word_count, audience)
    result = crew.kickoff()

    logger.info("Content Crew finished", topic=topic)
    return str(result)