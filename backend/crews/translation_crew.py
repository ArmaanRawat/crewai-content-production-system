"""
crews/translation_crew.py
─────────────────────────────────────────────────────────────────
The Translation Crew — translates an article into a target language
while preserving formatting, tone, style, and cultural context.

WHAT THIS CREW DOES:
  - Takes a completed article and a target language as input
  - Delegates the full translation task to a single translation agent
  - Returns the translated article with a brief Translation Notes section

PROCESS TYPE:
  - sequential → single task runs to completion
─────────────────────────────────────────────────────────────────
"""

from crewai import Crew, Process, Task
from agents.translation_agent import build_translation_agent
from utils.logger import get_logger

logger = get_logger(__name__)


def build_translation_crew(article: str, target_language: str) -> Crew:
    logger.info("Building Translation Crew", target_language=target_language)

    translation_agent = build_translation_agent()

    translation_task = Task(
        description=(
            f"Translate the following article into {target_language}.\n\n"
            f"Requirements:\n"
            f"- Preserve all formatting exactly, including headings, bullet points, numbered lists, and paragraph breaks.\n"
            f"- Maintain the original tone and style of the writing throughout.\n"
            f"- Adapt any cultural references, idioms, or expressions appropriately for the target audience of {target_language} speakers.\n"
            f"- Do not omit or add content beyond what is necessary for natural, accurate translation.\n\n"
            f"Article to translate:\n\n"
            f"{article}"
        ),
        expected_output=(
            f"The complete translated article in {target_language}, with the same structure and formatting as the original "
            f"(headings, bullet points, numbered lists, and paragraph breaks all preserved). "
            f"At the end of the translated article, include a brief 'Translation Notes' section written in English "
            f"that describes any cultural adaptations, idiomatic substitutions, or reference adjustments made during translation."
        ),
        agent=translation_agent,
    )

    crew = Crew(
        agents=[translation_agent],
        tasks=[translation_task],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("Translation Crew built successfully", target_language=target_language)
    return crew


def run_translation_crew(article: str, target_language: str) -> str:
    """
    Builds and runs the Translation Crew. Returns the translated article as a string.

    This is the single function the API route will call.
    """
    logger.info("Running Translation Crew", target_language=target_language)

    crew = build_translation_crew(article, target_language)
    result = crew.kickoff()

    logger.info("Translation Crew finished", target_language=target_language)
    return str(result)
