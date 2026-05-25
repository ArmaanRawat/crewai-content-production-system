"""
tools/tavily_tool.py
─────────────────────────────────────────────────────────────────
Tavily search tool used by the Researcher Agent.

WHAT THIS DOES:
  - Wraps the Tavily Search API
  - Takes a query string
  - Returns clean, structured search results

WHY TAVILY OVER GOOGLE:
  - Built specifically for AI agents
  - Returns summarized content, not raw HTML
  - No scraping needed — results are already clean
  - Has a generous free tier for development

HOW AGENTS USE THIS:
  - The Researcher Agent calls search_web(query)
  - Gets back a list of results with title, url, content
  - Uses those results to build its research summary
─────────────────────────────────────────────────────────────────
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from tavily import TavilyClient

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


# ── Structured result so callers get typed data, not raw dicts ───────────────
@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float  # relevance score from Tavily (0.0 – 1.0)


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    answer: Optional[str]  # Tavily's AI-generated summary (if available)


# ── Tool class ────────────────────────────────────────────────────────────────
class TavilySearchTool:
    """
    Wrapper around the Tavily Search API.

    Usage:
        tool = TavilySearchTool()
        response = tool.search("latest trends in renewable energy")
        for result in response.results:
            print(result.title, result.url)
    """

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "TAVILY_API_KEY is not set. "
                "Add it to your .env file: TAVILY_API_KEY=tvly-xxxx"
            )

        self.client = TavilyClient(api_key=api_key)
        logger.info("TavilySearchTool initialized")

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
    ) -> SearchResponse:
        """
        Search the web using Tavily.

        Args:
            query:          What to search for.
            max_results:    How many results to return (default 5).
            include_answer: Whether to include Tavily's AI summary.

        Returns:
            SearchResponse with a list of SearchResult objects.
        """
        logger.info(f"Searching Tavily", query=query, max_results=max_results)

        try:
            raw = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
                search_depth="advanced",  # deeper search for better results
            )

            # ── Parse results into typed dataclasses ─────────────────────────
            results = [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                )
                for r in raw.get("results", [])
            ]

            response = SearchResponse(
                query=query,
                results=results,
                answer=raw.get("answer"),  # AI summary — can be None
            )

            logger.info(
                f"Tavily search complete",
                query=query,
                results_returned=len(results),
                has_answer=response.answer is not None,
            )

            return response

        except Exception as e:
            logger.error(f"Tavily search failed", query=query, error=str(e))
            raise