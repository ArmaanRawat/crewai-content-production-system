"""
crews/feedback_crew.py
─────────────────────────────────────────────────────────────────
The Feedback Crew — applies client feedback to a draft article
and returns a fully revised version with a revision summary.

WHAT THIS CREW DOES:
  - Takes an original article and client feedback as inputs
  - Instructs the feedback agent to revise the article addressing
    every feedback point while preserving accuracy, tone, and structure
  - Appends a "Revision Summary" detailing each change made and why

PROCESS:
  - sequential with a single task (one agent, one pass)
─────────────────────────────────────────────────────────────────
"""

from crewai import Crew, Process, Task
from agents.feedback_agent import build_feedback_agent
from utils.logger import get_logger

logger = get_logger(__name__)


def build_feedback_crew(article: str, feedback: str) -> Crew:
    logger.info("Building Feedback Crew")

    feedback_agent = build_feedback_agent()

    revision_task = Task(
        description=(
            f"You are a professional editor. Carefully read the original article and the "
            f"client feedback provided below. Produce a revised version of the article that "
            f"addresses ALL feedback points. While revising, preserve the factual accuracy, "
            f"overall tone, and structural flow of the original. Do not introduce unverified "
            f"claims or drastically change the article's voice.\n\n"
            f"After the revised article, append a section titled 'Revision Summary' that lists "
            f"each change you made and the specific feedback point it addresses.\n\n"
            f"---ORIGINAL ARTICLE---\n"
            f"{article}\n\n"
            f"---CLIENT FEEDBACK---\n"
            f"{feedback}\n"
        ),
        expected_output=(
            "The complete revised article incorporating all client feedback, followed by a "
            "'Revision Summary' section that enumerates each change made and the reason for it."
        ),
        agent=feedback_agent,
    )

    crew = Crew(
        agents=[feedback_agent],
        tasks=[revision_task],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("Feedback Crew built successfully")
    return crew


def run_feedback_crew(article: str, feedback: str) -> str:
    """
    Builds and runs the Feedback Crew.

    Parameters
    ----------
    article  : The original draft article text.
    feedback : The client feedback to incorporate.

    Returns
    -------
    str : The revised article with an appended Revision Summary.
    """
    logger.info("Running Feedback Crew")

    crew = build_feedback_crew(article, feedback)
    result = crew.kickoff()

    logger.info("Feedback Crew finished")
    return str(result)
