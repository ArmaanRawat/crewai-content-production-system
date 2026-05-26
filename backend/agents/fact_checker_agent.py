"""
agents/fact_checker_agent.py
─────────────────────────────────────────────────────────────────
The Fact Checker Agent — fifth and final agent in the pipeline.

RESPONSIBILITY:
  - Receives the SEO-optimized article
  - Verifies all factual claims against the original research
  - Flags anything unverifiable or potentially incorrect
  - Returns a verified article with a fact-check report
─────────────────────────────────────────────────────────────────
"""

import os
from crewai import Agent
from crewai_tools import TavilySearchTool as CrewAITavilyTool
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def build_fact_checker_agent() -> Agent:
    """
    Factory function that constructs and returns the Fact Checker Agent.
    """
    logger.info("Building Fact Checker Agent")

    # Fact checker gets Tavily too — it needs to verify claims online
    tavily_tool = CrewAITavilyTool()

    agent = Agent(
        role="Senior Fact Checker",

        goal=(
            "Verify every factual claim in the article against credible sources. "
            "Flag any statements that are inaccurate, misleading, or unverifiable. "
            "Confirm statistics, dates, names, and key assertions are correct. "
            "Return the verified article with a short fact-check summary at the end."
        ),

        backstory=(
            "You are a meticulous fact checker with a background in investigative journalism. "
            "You have worked for major publications where accuracy is non-negotiable. "
            "You approach every article with healthy skepticism — you verify before you trust. "
            "You are known for catching subtle inaccuracies that others miss, "
            "and for being fair — you only flag something if you can prove it is wrong."
        ),

        tools=[tavily_tool],  # needs search to verify claims

        llm="gemini/gemini-2.0-flash-lite",

        verbose=True,
        allow_delegation=False,
        max_iter=2,  # may need more iterations to verify multiple claims
        memory=False,
    )

    logger.info("Fact Checker Agent built successfully")
    return agent