"""
agents/calendar_agent.py
─────────────────────────────────────────────────────────────────
The Content Calendar Agent — standalone planning agent.

RESPONSIBILITY:
  - Receives a topic/niche, target audience, content frequency,
    and time horizon from the content brief
  - Produces a structured, data-driven content calendar
  - Balances trending topics, evergreen content, and SEO value
  - Outputs a week-by-week or month-by-month editorial plan

WHY SEPARATED FROM TASKS:
  - Agent = WHO does the work (role, goal, personality)
  - Task  = WHAT work is done (instructions, expected output)
  - Keeping them separate means you can reuse this agent
    across different tasks later (e.g. repurposing calendar)
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


def build_calendar_agent() -> Agent:
    """
    Factory function that constructs and returns the Content Calendar Agent.

    WHY A FACTORY FUNCTION:
      - Easy to call from crew without instantiating a class
      - Clean, testable, and mockable
      - Config stays inside the function — no global state

    Returns:
        crewai.Agent configured as a content strategy and calendar planner.
    """

    logger.info("Building Content Calendar Agent")

    agent = Agent(
        # ── Identity ──────────────────────────────────────────────────────────
        role="Content Strategy & Calendar Planner",

        goal=(
            "Create detailed, data-driven content calendars that maximize engagement, "
            "SEO value, and audience retention based on the given niche, frequency, and audience."
        ),

        backstory=(
            "You are a seasoned content strategist with 12 years of experience at "
            "digital-first media companies including major publishing platforms and "
            "growth-stage startups. You have built editorial calendars for audiences "
            "ranging from niche B2B communities to mass-market consumer brands. "
            "You are an expert at planning editorial calendars that strike the right "
            "balance between trending topics, evergreen content, and audience growth "
            "initiatives. You understand content lifecycle management, seasonal "
            "relevance, SEO keyword clustering, and how to sequence content to guide "
            "readers through an awareness-to-loyalty funnel. Your calendars are always "
            "practical, clearly structured, and immediately actionable by a content team."
        ),

        # ── Tools ─────────────────────────────────────────────────────────────
        # No external tools needed — the agent reasons from its expertise
        # and the inputs provided in the task description.
        tools=[],

        # ── LLM config ───────────────────────────────────────────────────────
        llm=get_llm(),

        # ── Behaviour flags ───────────────────────────────────────────────────
        verbose=True,            # logs agent's thought process — great for debugging
        allow_delegation=False,  # calendar planner stays focused, doesn't hand off
        max_iter=2,              # max reasoning iterations before giving up
        memory=False,            # no cross-run memory
    )

    logger.info("Content Calendar Agent built successfully")
    return agent
