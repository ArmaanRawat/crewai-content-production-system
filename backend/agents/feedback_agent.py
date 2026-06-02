"""
agents/feedback_agent.py
─────────────────────────────────────────────────────────────────
The Client Feedback Agent — revision stage of the pipeline.

RESPONSIBILITY:
  - Receives an original article and client feedback instructions
  - Applies the requested changes while preserving quality, tone,
    and factual accuracy
  - Produces a fully revised article ready for delivery

WHY SEPARATED FROM TASKS:
  - Agent = WHO does the work (role, goal, personality)
  - Task  = WHAT work is done (instructions, expected output)
  - Keeping them separate means you can reuse this agent
    across different revision workflows later
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


def build_feedback_agent() -> Agent:
    """
    Factory function that constructs and returns the Client Feedback Agent.

    WHY A FACTORY FUNCTION:
      - Easy to call from crew without instantiating a class
      - Clean, testable, and mockable
      - Config stays inside the function — no global state

    Returns:
        crewai.Agent configured as a client feedback specialist.
    """

    logger.info("Building Client Feedback Agent")

    agent = Agent(
        # ── Identity ──────────────────────────────────────────────────────────
        role="Client Feedback Specialist",

        goal=(
            "Revise articles based on client feedback while preserving quality, "
            "tone, and factual accuracy. Translate client requests into precise "
            "content revisions that satisfy the client's intent without compromising "
            "the integrity and readability of the original article."
        ),

        backstory=(
            "You are a seasoned editor with over a decade of experience working "
            "directly with clients across publishing, marketing, and media industries. "
            "You have an exceptional ability to interpret client feedback — whether "
            "vague or highly specific — and transform it into targeted, meaningful "
            "revisions. You are known for your meticulous attention to detail, your "
            "respect for the original author's voice, and your commitment to delivering "
            "polished content that meets client expectations on the first revision. "
            "You never introduce inaccuracies and always ensure the revised article "
            "reads as a cohesive, high-quality piece."
        ),

        # ── Tools ─────────────────────────────────────────────────────────────
        # No external tools needed — this agent works purely from the
        # original article text and the client's feedback instructions.
        tools=[],

        # ── LLM config ───────────────────────────────────────────────────────
        llm=get_llm(),

        # ── Behaviour flags ───────────────────────────────────────────────────
        verbose=True,            # logs agent's thought process — great for debugging
        allow_delegation=False,  # feedback agent stays focused, doesn't hand off
        max_iter=3,              # max reasoning iterations before giving up
        memory=False,            # no cross-run memory in Phase 1
    )

    logger.info("Client Feedback Agent built successfully")
    return agent
