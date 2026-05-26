"""
tests/test_quality_gate.py
─────────────────────────────────────────────────────────────────
Unit tests for the Automated Quality Gate.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to import utils
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.quality_gate import QualityGate, QualityGateResponse
from tools.grammar_tool import GrammarCheckResponse
from tools.seo_tool import SEOResponse
from tools.plagiarism_tool import PlagiarismResponse


class TestQualityGate(unittest.TestCase):
    """
    Unit tests for the Automated QualityGate workflow using mocked tools.
    """

    def setUp(self):
        # A mock clean text and keywords
        self.text = "This is a high quality article that is optimized and grammatically correct."
        self.keywords = ["quality", "article"]

    @patch("utils.quality_gate.GrammarCheckTool")
    @patch("utils.quality_gate.SEOKeywordAnalyzer")
    @patch("utils.quality_gate.PlagiarismDetector")
    def test_quality_gate_all_pass(self, mock_plag_class, mock_seo_class, mock_grammar_class):
        """
        Verify that the quality gate passes when all tools return optimal metrics.
        """
        # 1. Setup mock instances
        mock_grammar = MagicMock()
        mock_grammar.check.return_value = GrammarCheckResponse(
            text=self.text, language="en-US", matches=[], is_valid=True
        )
        mock_grammar_class.return_value = mock_grammar

        mock_seo = MagicMock()
        mock_seo.analyze.return_value = SEOResponse(
            score=85.0, keyword_metrics={}, word_count=10, suggestions=[]
        )
        mock_seo_class.return_value = mock_seo

        mock_plag = MagicMock()
        mock_plag.check.return_value = PlagiarismResponse(
            score=5.0, matches=[], is_safe=True, threshold=0.80
        )
        mock_plag_class.return_value = mock_plag

        # 2. Run quality gate
        gate = QualityGate()
        res = gate.evaluate(self.text, self.keywords, reference_docs=["Ref doc A"])

        # 3. Assertions
        self.assertTrue(res.passed)
        self.assertTrue(res.grammar_passed)
        self.assertTrue(res.seo_passed)
        self.assertTrue(res.plagiarism_passed)
        self.assertEqual(res.grammar_errors_count, 0)
        self.assertEqual(res.seo_score, 85.0)
        self.assertEqual(res.plagiarism_score, 5.0)
        
        # Check overall score math:
        # Grammar score comp = 100
        # SEO score comp = 85
        # Plagiarism score comp = 100 - 5 = 95
        # Weighted score = (100 * 0.3) + (85 * 0.4) + (95 * 0.3) = 30 + 34 + 28.5 = 92.5
        self.assertEqual(res.score, 92.5)
        self.assertEqual(len(res.reasons), 0)

    @patch("utils.quality_gate.GrammarCheckTool")
    @patch("utils.quality_gate.SEOKeywordAnalyzer")
    @patch("utils.quality_gate.PlagiarismDetector")
    def test_quality_gate_failures(self, mock_plag_class, mock_seo_class, mock_grammar_class):
        """
        Verify that failures in individual checks cause the gate to fail with proper reasons.
        """
        # Setup mock tools to fail
        # Grammar has 8 errors (limit is 5)
        mock_grammar = MagicMock()
        mock_grammar.check.return_value = GrammarCheckResponse(
            text=self.text, language="en-US", matches=[MagicMock()] * 8, is_valid=False
        )
        mock_grammar_class.return_value = mock_grammar

        # SEO score is 55.0 (limit is 70)
        mock_seo = MagicMock()
        mock_seo.analyze.return_value = SEOResponse(
            score=55.0, keyword_metrics={}, word_count=10, suggestions=[]
        )
        mock_seo_class.return_value = mock_seo

        # Plagiarism score is 20% (limit is 15%)
        mock_plag = MagicMock()
        mock_plag.check.return_value = PlagiarismResponse(
            score=20.0, matches=[MagicMock()], is_safe=False, threshold=0.80
        )
        mock_plag_class.return_value = mock_plag

        gate = QualityGate()
        res = gate.evaluate(self.text, self.keywords, reference_docs=["Ref doc A"])

        self.assertFalse(res.passed)
        self.assertFalse(res.grammar_passed)
        self.assertFalse(res.seo_passed)
        self.assertFalse(res.plagiarism_passed)
        self.assertEqual(len(res.reasons), 3)
        self.assertTrue(any("Grammar check failed" in r for r in res.reasons))
        self.assertTrue(any("SEO optimization failed" in r for r in res.reasons))
        self.assertTrue(any("Plagiarism check failed" in r for r in res.reasons))

    @patch("utils.quality_gate.GrammarCheckTool")
    @patch("utils.quality_gate.SEOKeywordAnalyzer")
    def test_quality_gate_no_plagiarism_check(self, mock_seo_class, mock_grammar_class):
        """
        Verify that plagiarism check is skipped and marked as passed when no reference docs are provided.
        """
        mock_grammar = MagicMock()
        mock_grammar.check.return_value = GrammarCheckResponse(
            text=self.text, language="en-US", matches=[], is_valid=True
        )
        mock_grammar_class.return_value = mock_grammar

        mock_seo = MagicMock()
        mock_seo.analyze.return_value = SEOResponse(
            score=80.0, keyword_metrics={}, word_count=10, suggestions=[]
        )
        mock_seo_class.return_value = mock_seo

        gate = QualityGate()
        res = gate.evaluate(self.text, self.keywords, reference_docs=None)

        self.assertTrue(res.passed)
        self.assertTrue(res.plagiarism_passed)
        self.assertEqual(res.plagiarism_score, 0.0)
        
        # Check overall score math (plagiarism skipped):
        # Grammar score comp = 100
        # SEO score comp = 80
        # Weighted score = (100 * 0.4) + (80 * 0.6) = 40 + 48 = 88.0
        self.assertEqual(res.score, 88.0)


if __name__ == "__main__":
    unittest.main()
