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
from tasks import build_research_task, build_writing_task, build_editing_task, build_seo_task, build_fact_check_task
from utils.logger import get_logger

logger = get_logger(__name__)


def build_content_crew(topic, tone, word_count, audience) -> Crew:
    logger.info("Building Content Crew", topic=topic)

    research_task = build_research_task(topic, audience)
    writing_task  = build_writing_task(topic, tone, word_count, audience)
    editing_task  = build_editing_task(topic, tone, audience)
    seo_task      = build_seo_task(topic, audience)
    fact_check_task = build_fact_check_task(topic)  
    crew = Crew(
        agents=[
            research_task.agent,
            writing_task.agent,
            editing_task.agent,
            seo_task.agent,
            fact_check_task.agent,
        ],
        tasks=[
            research_task,   # runs first
            writing_task,    # runs second
            editing_task,    # runs third
            seo_task,        # runs fourth
            fact_check_task, # runs fifth
        ],
        process=Process.sequential,
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

