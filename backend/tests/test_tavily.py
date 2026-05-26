"""
tests/test_tavily.py
─────────────────────────────────────────────────────────────────
Unit tests and integration checks for the Tavily Search Tool.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to import tools
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.tavily_tool import TavilySearchTool, SearchResponse, SearchResult


class TestTavilySearchTool(unittest.TestCase):
    """
    Unit tests for TavilySearchTool using unittest.mock to avoid real API requests.
    """

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_key_12345"})
    @patch("tools.tavily_tool.TavilyClient")
    def test_initialization_with_key(self, mock_tavily_client):
        """
        Verify that TavilySearchTool initializes properly when TAVILY_API_KEY is present.
        """
        tool = TavilySearchTool()
        self.assertIsNotNone(tool.client)
        mock_tavily_client.assert_called_once_with(api_key="test_key_12345")

    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_without_key_raises_error(self):
        """
        Verify that TavilySearchTool raises EnvironmentError when TAVILY_API_KEY is missing.
        """
        with self.assertRaises(EnvironmentError) as context:
            TavilySearchTool()
        self.assertIn("TAVILY_API_KEY is not set", str(context.exception))

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test_key_12345"})
    @patch("tools.tavily_tool.TavilyClient")
    def test_search_parsing(self, mock_tavily_client):
        """
        Verify that raw search results are correctly parsed into dataclasses.
        """
        # 1. Setup mock client response
        mock_instance = MagicMock()
        mock_tavily_client.return_value = mock_instance
        
        mock_instance.search.return_value = {
            "results": [
                {
                    "title": "Artificial Intelligence in 2026",
                    "url": "https://example.com/ai-2026",
                    "content": "AI systems are becoming agentic and highly autonomous in 2026.",
                    "score": 0.98
                },
                {
                    "title": "Future of Tech",
                    "url": "https://example.com/future-tech",
                    "content": "An overview of future technology trends.",
                    "score": 0.85
                }
            ],
            "answer": "AI trends in 2026 show rapid growth in autonomous agents."
        }

        # 2. Instantiate tool and run search
        tool = TavilySearchTool()
        response = tool.search("AI trends 2026", max_results=2)

        # 3. Assertions
        self.assertIsInstance(response, SearchResponse)
        self.assertEqual(response.query, "AI trends 2026")
        self.assertEqual(response.answer, "AI trends in 2026 show rapid growth in autonomous agents.")
        
        # Check results
        self.assertEqual(len(response.results), 2)
        
        first_result = response.results[0]
        self.assertIsInstance(first_result, SearchResult)
        self.assertEqual(first_result.title, "Artificial Intelligence in 2026")
        self.assertEqual(first_result.url, "https://example.com/ai-2026")
        self.assertEqual(first_result.content, "AI systems are becoming agentic and highly autonomous in 2026.")
        self.assertEqual(first_result.score, 0.98)

        second_result = response.results[1]
        self.assertIsInstance(second_result, SearchResult)
        self.assertEqual(second_result.title, "Future of Tech")
        self.assertEqual(second_result.url, "https://example.com/future-tech")
        self.assertEqual(second_result.content, "An overview of future technology trends.")
        self.assertEqual(second_result.score, 0.85)

        # Ensure Tavily API was called correctly
        mock_instance.search.assert_called_once_with(
            query="AI trends 2026",
            max_results=2,
            include_answer=True,
            search_depth="advanced"
        )


if __name__ == "__main__":
    unittest.main()
