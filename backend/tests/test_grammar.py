"""
tests/test_grammar.py
─────────────────────────────────────────────────────────────────
Unit tests and integration checks for the Grammar Check Tool.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to import tools
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.grammar_tool import GrammarCheckTool, CrewAIGrammarCheckTool, GrammarCheckResponse, GrammarMatch


class TestGrammarCheckTool(unittest.TestCase):
    """
    Unit tests for GrammarCheckTool using unittest.mock to avoid real API requests.
    """

    @patch("tools.grammar_tool.requests.post")
    def test_grammar_check_parsing(self, mock_post):
        """
        Verify that LanguageTool API responses are correctly parsed.
        """
        # 1. Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "matches": [
                {
                    "message": "Use 'does' instead of 'do' for singular third-person.",
                    "shortMessage": "Subject-verb agreement error",
                    "offset": 3,
                    "length": 2,
                    "context": {
                        "text": "He do not like bananas.",
                        "offset": 3,
                        "length": 2
                    },
                    "rule": {
                        "id": "HE_DO",
                        "description": "Checks for incorrect use of 'do' with third-person subjects.",
                        "category": {"id": "GRAMMAR", "name": "Grammar"}
                    },
                    "replacements": [{"value": "does"}]
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 2. Run check
        tool = GrammarCheckTool()
        res = tool.check("He do not like bananas.")

        # 3. Assertions
        self.assertIsInstance(res, GrammarCheckResponse)
        self.assertFalse(res.is_valid)
        self.assertEqual(len(res.matches), 1)

        match = res.matches[0]
        self.assertEqual(match.message, "Use 'does' instead of 'do' for singular third-person.")
        self.assertEqual(match.short_message, "Subject-verb agreement error")
        self.assertEqual(match.rule_id, "HE_DO")
        self.assertEqual(match.category, "Grammar")
        self.assertEqual(match.replacements, ["does"])
        self.assertEqual(match.matched_text, "do")

        mock_post.assert_called_once()

    @patch("tools.grammar_tool.requests.post")
    def test_grammar_check_valid_text(self, mock_post):
        """
        Verify that a clean text results in is_valid=True.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"matches": []}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        tool = GrammarCheckTool()
        res = tool.check("He does not like bananas.")

        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.matches), 0)

    def test_grammar_check_empty_text(self):
        """
        Verify that empty text returns immediately with no matches.
        """
        tool = GrammarCheckTool()
        res = tool.check("   ")
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.matches), 0)

    @patch("tools.grammar_tool.requests.post")
    def test_crewai_grammar_tool_report(self, mock_post):
        """
        Verify that the CrewAI tool wrapper outputs a formatted report for agents.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "matches": [
                {
                    "message": "Use 'does' instead of 'do' for singular third-person.",
                    "shortMessage": "Subject-verb agreement error",
                    "offset": 3,
                    "length": 2,
                    "context": {
                        "text": "He do not like bananas.",
                        "offset": 3,
                        "length": 2
                    },
                    "rule": {
                        "id": "HE_DO",
                        "description": "Checks for incorrect use of 'do'.",
                        "category": {"id": "GRAMMAR", "name": "Grammar"}
                    },
                    "replacements": [{"value": "does"}]
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        crew_tool = CrewAIGrammarCheckTool()
        report = crew_tool._run("He do not like bananas.")

        self.assertIn("Found 1 issues", report)
        self.assertIn("Use 'does' instead of 'do'", report)
        self.assertIn("Suggestions: does", report)


if __name__ == "__main__":
    unittest.main()
