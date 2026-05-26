"""
tests/test_seo.py
─────────────────────────────────────────────────────────────────
Unit tests for the SEO Keyword Analyzer tool.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest

# Adjust path to import tools
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.seo_tool import SEOKeywordAnalyzer, CrewAISEOTool, KeywordMetrics, SEOResponse


class TestSEOKeywordAnalyzer(unittest.TestCase):
    """
    Unit tests for SEOKeywordAnalyzer scoring and structure parsing.
    """

    def setUp(self):
        self.analyzer = SEOKeywordAnalyzer()
        # A mock article matching standard structure
        self.article = (
            "# Agentic AI in 2026\n\n"
            "Agentic AI is transforming how we operate. Modern agentic AI tools can plan, "
            "reason, and execute complex workflows without constant human oversight.\n\n"
            "## Why Agentic AI Matters\n\n"
            "Traditional automation is rigid. Agentic AI is flexible and adapts to changing environments.\n\n"
            "### Implementing Agentic AI Systems\n\n"
            "Deploying agentic AI systems requires robust safety guardrails and continuous evaluation."
        )

    def test_seo_parsing_and_scoring(self):
        """
        Verify that headline, introduction, subheadings, word counts, and scores are processed correctly.
        """
        # Target keywords: "agentic ai" (highly optimized) and "automation" (subheading/body optimized)
        keywords = ["agentic ai", "automation"]
        
        res = self.analyzer.analyze(self.article, keywords)

        self.assertIsInstance(res, SEOResponse)
        self.assertEqual(res.word_count, 58)  # 58 words
        self.assertTrue(res.score > 0.0)

        # Metrics checks for "agentic ai"
        # It's in the headline: "# Agentic AI in 2026"
        # It's in the intro: "Agentic AI is transforming..."
        # It's in subheadings: "## Why Agentic AI Matters"
        metrics_ai = res.keyword_metrics["agentic ai"]
        self.assertEqual(metrics_ai.keyword, "agentic ai")
        self.assertTrue(metrics_ai.in_headline)
        self.assertTrue(metrics_ai.in_introduction)
        self.assertTrue(metrics_ai.in_subheadings)
        
        # Occurrence count check
        # Text has "Agentic AI" in: headline (1), intro (2), subheading (1), subheading (1), body (1) -> total 7 occurrences
        self.assertEqual(metrics_ai.count, 7)

        # Metrics check for "automation"
        # Not in headline, not in intro, in body paragraph: "Traditional automation is rigid."
        metrics_auto = res.keyword_metrics["automation"]
        self.assertFalse(metrics_auto.in_headline)
        self.assertFalse(metrics_auto.in_introduction)
        self.assertFalse(metrics_auto.in_subheadings)
        self.assertEqual(metrics_auto.count, 1)

    def test_keyword_density_status(self):
        """
        Verify that keyword density statuses ("low", "optimal", "stuffed", "not_found") are correct.
        """
        # 1. Not found keyword
        res_not_found = self.analyzer.analyze(self.article, ["blockchain"])
        metrics_bc = res_not_found.keyword_metrics["blockchain"]
        self.assertEqual(metrics_bc.status, "not_found")
        self.assertEqual(metrics_bc.count, 0)
        self.assertEqual(metrics_bc.density, 0.0)

        # 2. Stuffed keyword
        stuffed_text = "SEO. SEO. SEO. SEO. SEO. SEO. SEO. SEO. SEO. SEO."
        res_stuffed = self.analyzer.analyze(stuffed_text, ["seo"])
        metrics_seo = res_stuffed.keyword_metrics["seo"]
        self.assertEqual(metrics_seo.status, "stuffed")

    def test_crewai_seo_tool_report(self):
        """
        Verify that the CrewAI tool wrapper outputs a formatted string report.
        """
        crew_tool = CrewAISEOTool()
        report = crew_tool._run(self.article, ["agentic ai"])

        self.assertIn("SEO Evaluation Report", report)
        self.assertIn("Overall SEO Score", report)
        self.assertIn("Word Count: 58", report)
        self.assertIn("agentic ai", report)
        self.assertIn("Placement: Headline, Introduction, Subheadings", report)


if __name__ == "__main__":
    unittest.main()
