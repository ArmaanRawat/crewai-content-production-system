"""
agents/researcher_agent.py
─────────────────────────────────────────────────────────────────
The Researcher Agent — first agent in the pipeline.

RESPONSIBILITY:
  - Receives a topic from the content brief
  - Uses Tavily to search the web for relevant information
  - Synthesizes findings into a structured research summary
  - Passes that summary to the Writer Agent

WHY SEPARATED FROM TASKS:
  - Agent = WHO does the work (role, goal, personality)
  - Task  = WHAT work is done (instructions, expected output)
  - Keeping them separate means you can reuse this agent
    across different tasks later (e.g. fact-checking task)
─────────────────────────────────────────────────────────────────
"""

import os
from crewai import Agent
from crewai_tools import TavilySearchTool as CrewAITavilyTool
from dotenv import load_dotenv


from utils.logger import get_logger
from utils.helpers import get_llm

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

logger = get_logger(__name__)


def build_researcher_agent() -> Agent:
    """
    Factory function that constructs and returns the Researcher Agent.

    WHY A FACTORY FUNCTION:
      - Easy to call from crew without instantiating a class
      - Clean, testable, and mockable
      - Config stays inside the function — no global state

    Returns:
        crewai.Agent configured as a research specialist.
    """

    logger.info("Building Researcher Agent")

    # ── Tavily tool — CrewAI's built-in wrapper ───────────────────────────────
    # CrewAI has its own TavilySearchTool that integrates directly
    # with the agent's tool-calling loop. We use this instead of our
    # custom wrapper for agent usage. Our custom wrapper (tools/tavily_tool.py)
    # is used for direct/manual calls outside of CrewAI.
    tavily_tool = CrewAITavilyTool()

    agent = Agent(
        # ── Identity ──────────────────────────────────────────────────────────
        role="Senior Research Specialist",

        goal=(
            "Conduct thorough, accurate research on the given topic. "
            "Find the most relevant, up-to-date information from credible sources. "
            "Synthesize findings into a clear, well-organized research summary "
            "that gives the Writer Agent everything needed to produce a great article."
        ),

        backstory=(
            "You are a veteran research journalist with 15 years of experience "
            "investigating complex topics across technology, science, business, and culture. "
            "You are known for finding the most credible sources, spotting key trends, "
            "and distilling large amounts of information into clear, actionable summaries. "
            "You never guess — you only report what you can verify."
        ),

        # ── Tools this agent can use ──────────────────────────────────────────
        tools=[tavily_tool],

        # ── LLM config ───────────────────────────────────────────────────────
        llm=get_llm(),
    

        # ── Behaviour flags ───────────────────────────────────────────────────
        verbose=True,        # logs agent's thought process — great for debugging
        allow_delegation=False,  # researcher stays focused, doesn't hand off
        max_iter=3,          # max reasoning iterations before giving up
        memory=False,        # no cross-run memory in Phase 1
    )

    logger.info("Researcher Agent built successfully")
    return agent