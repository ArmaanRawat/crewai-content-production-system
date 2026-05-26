"""
tools/grammar_tool.py
─────────────────────────────────────────────────────────────────
LanguageTool API integration for spelling, grammar, and style checks.
─────────────────────────────────────────────────────────────────
"""

import os
import requests
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv
from crewai.tools import BaseTool
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


# ── Structured results for programmatic usage (e.g. Quality Gate) ─────────────
@dataclass
class GrammarMatch:
    message: str
    short_message: str
    offset: int
    length: int
    matched_text: str
    replacements: List[str]
    rule_id: str
    rule_description: str
    category: str


@dataclass
class GrammarCheckResponse:
    text: str
    language: str
    matches: List[GrammarMatch]
    is_valid: bool


# ── Plain Python Tool Wrapper ──────────────────────────────────────────────────
class GrammarCheckTool:
    """
    Programmatic wrapper around the LanguageTool API.
    Used for direct queries and quality gate scoring.
    """

    def __init__(self, api_url: Optional[str] = None):
        # Fall back to public API if no custom server is specified
        self.api_url = api_url or os.getenv(
            "LANGUAGETOOL_API_URL", "https://api.languagetool.org/v2/check"
        )
        logger.info("GrammarCheckTool initialized", api_url=self.api_url)

    def check(self, text: str, language: str = "en-US") -> GrammarCheckResponse:
        """
        Send text to LanguageTool API and return structured grammar results.
        """
        logger.info("Checking grammar", text_len=len(text), language=language)

        if not text.strip():
            return GrammarCheckResponse(
                text=text,
                language=language,
                matches=[],
                is_valid=True
            )

        payload = {
            "text": text,
            "language": language
        }

        try:
            response = requests.post(self.api_url, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            matches = []
            for item in data.get("matches", []):
                rule = item.get("rule", {})
                category = rule.get("category", {})
                replacements = [r.get("value", "") for r in item.get("replacements", [])]

                matches.append(
                    GrammarMatch(
                        message=item.get("message", ""),
                        short_message=item.get("shortMessage", ""),
                        offset=item.get("offset", 0),
                        length=item.get("length", 0),
                        matched_text=item.get("context", {}).get("text", "")[
                            item.get("context", {}).get("offset", 0) : 
                            item.get("context", {}).get("offset", 0) + item.get("context", {}).get("length", 0)
                        ] or text[item.get("offset", 0) : item.get("offset", 0) + item.get("length", 0)],
                        replacements=replacements,
                        rule_id=rule.get("id", ""),
                        rule_description=rule.get("description", ""),
                        category=category.get("name", "General")
                    )
                )

            is_valid = len(matches) == 0
            logger.info("Grammar check complete", matches_found=len(matches), is_valid=is_valid)

            return GrammarCheckResponse(
                text=text,
                language=language,
                matches=matches,
                is_valid=is_valid
            )

        except Exception as e:
            logger.error("Grammar check failed", error=str(e))
            raise


# ── CrewAI Tool Integration ────────────────────────────────────────────────────
class CrewAIGrammarCheckTool(BaseTool):
    """
    CrewAI agent tool wrapper. Exposes a text description and string-based report
    suitable for agent ingestion (e.g. Editor Agent).
    """
    name: str = "Grammar Checker Tool"
    description: str = (
        "Checks a text for spelling, grammar, style, and punctuation errors. "
        "Expects 'text' as string input, and optionally 'language' (defaults to 'en-US'). "
        "Returns a detailed report with suggestions for corrections."
    )

    def _run(self, text: str, language: str = "en-US") -> str:
        try:
            tool = GrammarCheckTool()
            res = tool.check(text, language)

            if res.is_valid:
                return "Grammar Check Result: No grammar or spelling errors found!"

            report = [f"Grammar Check Result: Found {len(res.matches)} issues."]
            for idx, match in enumerate(res.matches, 1):
                report.append(
                    f"\nIssue {idx}:"
                    f"\n  - Message: {match.message}"
                    f"\n  - Text: \"{match.matched_text}\""
                    f"\n  - Category: {match.category}"
                    f"\n  - Rule ID: {match.rule_id}"
                    f"\n  - Suggestions: {', '.join(match.replacements[:5]) if match.replacements else 'None'}"
                )

            return "\n".join(report)

        except Exception as e:
            return f"Error performing grammar check: {str(e)}"
