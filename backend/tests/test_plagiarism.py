"""
tests/test_plagiarism.py
─────────────────────────────────────────────────────────────────
Unit tests for the Plagiarism Detector tool.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to import tools
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.plagiarism_tool import PlagiarismDetector, CrewAIPlagiarismTool, PlagiarizedSentence, PlagiarismResponse


class TestPlagiarismDetector(unittest.TestCase):
    """
    Unit tests for PlagiarismDetector using mock SentenceTransformers to test
    sentence splitting, matching, scoring, and output logic offline.
    """

    def test_sentence_splitting(self):
        """
        Verify that sentences are parsed and cleaned correctly.
        """
        detector = PlagiarismDetector()
        text = "This is the first sentence. And here is a second one? Too short."
        sentences = detector._split_into_sentences(text)
        
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0], "This is the first sentence.")
        self.assertEqual(sentences[1], "And here is a second one?")

    @patch("tools.plagiarism_tool.PlagiarismDetector.get_model")
    @patch("tools.plagiarism_tool.util.cos_sim")
    def test_plagiarism_detection_and_scoring(self, mock_cos_sim, mock_get_model):
        """
        Verify that similarity calculations, scores, and matches are parsed correctly.
        """
        # 1. Setup mock model
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Mock encode to return dummy tensors
        mock_model.encode.side_effect = lambda texts, **kwargs: MagicMock()

        # Mock utility cosine similarity score matrix (2 input sentences, 3 reference sentences)
        # Row 0 (input sentence 1): [0.10, 0.95, 0.20] -> match at index 1 (score 0.95, plagiarized)
        # Row 1 (input sentence 2): [0.40, 0.30, 0.50] -> match at index 2 (score 0.50, safe)
        mock_scores_tensor = MagicMock()
        mock_scores_tensor.cpu().numpy.return_value = [
            [0.10, 0.95, 0.20],
            [0.40, 0.30, 0.50]
        ]
        mock_cos_sim.return_value = mock_scores_tensor

        # 2. Run detection
        detector = PlagiarismDetector(threshold=0.80)
        
        input_text = "This is sentence one. This is sentence two."
        reference_docs = [
            "Source doc sentence A. Source doc sentence B.",  # index 0 (contains ref sentence 0, 1)
            "Source doc sentence C."                          # index 1 (contains ref sentence 2)
        ]

        res = detector.check(input_text, reference_docs)

        # 3. Assertions
        self.assertIsInstance(res, PlagiarismResponse)
        self.assertEqual(res.score, 50.0)  # 1 out of 2 sentences plagiarized
        self.assertFalse(res.is_safe)
        
        self.assertEqual(len(res.matches), 1)
        match = res.matches[0]
        self.assertIsInstance(match, PlagiarizedSentence)
        self.assertEqual(match.text, "This is sentence one.")
        self.assertEqual(match.matched_text, "Source doc sentence B.")
        self.assertEqual(match.similarity, 0.95)
        self.assertEqual(match.source_index, 0)

        # Ensure util.cos_sim was called
        mock_cos_sim.assert_called_once()

    @patch("tools.plagiarism_tool.PlagiarismDetector.get_model")
    @patch("tools.plagiarism_tool.util.cos_sim")
    def test_crewai_plagiarism_tool_report(self, mock_cos_sim, mock_get_model):
        """
        Verify that the CrewAI tool wrapper outputs a formatted report.
        """
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_scores_tensor = MagicMock()
        mock_scores_tensor.cpu().numpy.return_value = [
            [0.90]
        ]
        mock_cos_sim.return_value = mock_scores_tensor

        crew_tool = CrewAIPlagiarismTool()
        report = crew_tool._run("This is input text.", ["This is reference text."])

        self.assertIn("Plagiarism Detection Report", report)
        self.assertIn("Overall Plagiarism Score: 100.0%", report)
        self.assertIn("Verdict: DUPLICATE CONTENT DETECTED", report)
        self.assertIn("Matched Sentence (90.0% similarity)", report)


if __name__ == "__main__":
    unittest.main()
