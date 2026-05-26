"""
tests/test_doc_generator.py
─────────────────────────────────────────────────────────────────
Unit tests for the Automated Technical Documentation Generator.
─────────────────────────────────────────────────────────────────
"""

import os
import unittest
from pathlib import Path

# Adjust path to import backend modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.doc_generator import generate_docs


class TestDocGenerator(unittest.TestCase):
    """
    Unit tests for utils.doc_generator.
    """

    def test_generate_docs_execution(self):
        """
        Verify that generate_docs runs without error, generates a markdown string,
        and saves it to the correct path with expected content sections.
        """
        # Run generation
        content = generate_docs()
        
        # Verify returned content is valid markdown
        self.assertIsInstance(content, str)
        self.assertIn("# Automated Technical Documentation", content)
        self.assertIn("## 1. FastAPI Router & Endpoints", content)
        self.assertIn("## 2. Integrated Utility & Agent Tools", content)
        self.assertIn("## 3. Automated Quality Gate System", content)

        # Verify file creation
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        output_path = docs_dir / "architecture_and_api.md"
        self.assertTrue(output_path.exists(), f"Docs file was not created at: {output_path}")

        # Verify written file content
        with open(output_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        self.assertEqual(content, file_content)


if __name__ == "__main__":
    unittest.main()
