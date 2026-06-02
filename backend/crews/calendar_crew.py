"""
crews/calendar_crew.py
─────────────────────────────────────────────────────────────────
The Content Calendar Crew — wires the calendar agent into a task
pipeline that produces a structured multi-week content calendar.

WHAT A CREW IS:
  - A group of agents working together on a set of tasks
  - Manages task execution order
  - Passes output from one agent to the next

PROCESS TYPES:
  - sequential → tasks run one after another (what we use)
  - hierarchical → a manager agent delegates to others (Phase 2)
─────────────────────────────────────────────────────────────────
"""

from crewai import Crew, Process, Task
from agents.calendar_agent import build_calendar_agent
from utils.logger import get_logger

logger = get_logger(__name__)


def build_calendar_crew(niche: str, audience: str, frequency: str, weeks: int) -> Crew:
    logger.info("Building Calendar Crew", niche=niche, audience=audience, frequency=frequency, weeks=weeks)

    calendar_agent = build_calendar_agent()

    calendar_task = Task(
        description=(
            f"Create a {weeks}-week content calendar for the '{niche}' niche, "
            f"targeting '{audience}' as the primary audience, with a '{frequency}' publishing frequency. "
            f"For each piece of content, specify the following details:\n"
            f"  - Week number\n"
            f"  - Day/Date\n"
            f"  - Content Title\n"
            f"  - Content Type (blog/video/social/newsletter)\n"
            f"  - Primary Keyword\n"
            f"  - Brief Description (2-3 sentences)\n"
            f"  - Content Goal (awareness/engagement/conversion/retention)\n\n"
            f"Ensure the calendar spans exactly {weeks} weeks and aligns each publishing slot "
            f"with the '{frequency}' frequency. Vary content types strategically across the calendar "
            f"to serve different goals throughout the {weeks}-week period."
        ),
        expected_output=(
            f"A structured {weeks}-week content calendar in a clear table or list format, "
            f"with at least one piece of content per publishing slot as defined by the '{frequency}' "
            f"publishing frequency. Each entry must include: Week number, Day/Date, Content Title, "
            f"Content Type, Primary Keyword, Brief Description (2-3 sentences), and Content Goal. "
            f"The calendar must be followed by a strategic overview paragraph explaining the content "
            f"mix rationale — covering how the selected content types, topics, and goals work together "
            f"to serve the '{audience}' audience within the '{niche}' niche over the {weeks}-week period."
        ),
        agent=calendar_agent,
    )

    crew = Crew(
        agents=[calendar_agent],
        tasks=[calendar_task],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("Calendar Crew built successfully")
    return crew


def run_calendar_crew(niche: str, audience: str, frequency: str, weeks: int) -> str:
    """
    Builds and runs the calendar crew. Returns the content calendar as a string.

    This is the single function the API route will call.
    """
    logger.info("Running Calendar Crew", niche=niche, audience=audience, frequency=frequency, weeks=weeks)

    crew = build_calendar_crew(niche, audience, frequency, weeks)
    result = crew.kickoff()

    logger.info("Calendar Crew finished", niche=niche)
    return str(result)
