"""
tools/seo_tool.py
─────────────────────────────────────────────────────────────────
SEO Keyword Analyzer and scoring tool.
─────────────────────────────────────────────────────────────────
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from crewai.tools import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Structured results for programmatic usage (e.g. Quality Gate) ─────────────
@dataclass
class KeywordMetrics:
    keyword: str
    count: int
    density: float           # Percentage (e.g., 1.5 for 1.5%)
    in_headline: bool
    in_introduction: bool
    in_subheadings: bool
    status: str              # "optimal", "low", "stuffed", "not_found"


@dataclass
class SEOResponse:
    score: float             # Overall SEO score (0 - 100)
    keyword_metrics: Dict[str, KeywordMetrics]
    word_count: int
    suggestions: List[str]


# ── Plain Python SEO Tool ──────────────────────────────────────────────────────
class SEOKeywordAnalyzer:
    """
    Programmatic analyzer for scoring article SEO metrics.
    """

    def __init__(self):
        logger.info("SEOKeywordAnalyzer initialized")

    def analyze(self, text: str, keywords: List[str]) -> SEOResponse:
        """
        Analyzes the text against the provided list of keywords.
        Returns detailed density, structural presence, and an overall SEO score.
        """
        logger.info("Analyzing text for SEO", keywords=keywords, text_len=len(text))

        if not text.strip() or not keywords:
            return SEOResponse(
                score=0.0,
                keyword_metrics={},
                word_count=0,
                suggestions=["Text or keywords list is empty."]
            )

        # ── Parse Article Structure ───────────────────────────────────────────
        lines = [line.strip() for line in text.split("\n")]
        
        # 1. Headline (Markdown H1 or the first non-empty line)
        headline = ""
        headline_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("# "):
                headline = line[2:]
                headline_idx = idx
                break
        if not headline:
            # Fallback to first non-empty line
            for idx, line in enumerate(lines):
                if line:
                    headline = line
                    headline_idx = idx
                    break

        # 2. Subheadings (Markdown H2, H3, H4)
        subheadings = []
        for line in lines:
            if line.startswith("## ") or line.startswith("### ") or line.startswith("#### "):
                # Strip markdown headers
                subheadings.append(line.lstrip("#").strip())

        # 3. Introduction (First paragraph that is not a heading and is not empty)
        introduction = ""
        for idx, line in enumerate(lines):
            if idx > headline_idx and line and not line.startswith("#"):
                introduction = line
                break

        # 4. Total Word Count (Cleaned text)
        # Strip markdown symbols and calculate words
        clean_text = re.sub(r'[#*`_\[\]()\-+]', ' ', text)
        words = [w.lower() for w in clean_text.split() if w.strip()]
        word_count = len(words)

        keyword_metrics = {}
        suggestions = []
        total_score = 0.0

        if word_count == 0:
            return SEOResponse(score=0.0, keyword_metrics={}, word_count=0, suggestions=["No words found in text."])

        # ── Score Weights ─────────────────────────────────────────────────────
        # Overall score components (per keyword basis, averaged):
        # 1. Density score: 40% (Target density: 1.0% - 2.5%)
        # 2. Headline presence: 20%
        # 3. Introduction presence: 20%
        # 4. Subheadings presence: 20%

        for keyword in keywords:
            kw_clean = keyword.strip().lower()
            if not kw_clean:
                continue

            # Count occurrences using regex to match word boundaries
            # Escape to avoid regex injection
            pattern = r'\b' + re.escape(kw_clean) + r'\b'
            count = len(re.findall(pattern, clean_text.lower()))
            
            # Density
            density = (count / word_count) * 100

            # Structural Checks
            in_headline = kw_clean in headline.lower() if headline else False
            in_intro = kw_clean in introduction.lower() if introduction else False
            in_subs = any(kw_clean in s.lower() for s in subheadings)

            # Determine status & density score
            density_score = 0.0
            if count == 0:
                status = "not_found"
                suggestions.append(f"Keyword '{keyword}' is missing from the article.")
            elif density < 0.5:
                status = "low"
                density_score = (density / 1.0) * 40.0  # Linear scaling up to 1%
                suggestions.append(f"Keyword '{keyword}' has very low density ({density:.2f}%). Try mentioning it more often.")
            elif 0.5 <= density < 1.0:
                status = "low"
                density_score = 25.0 + ((density - 0.5) / 0.5) * 15.0  # Scale between 25 and 40 points
            elif 1.0 <= density <= 2.5:
                status = "optimal"
                density_score = 40.0  # Full points
            else:  # density > 2.5
                status = "stuffed"
                # Penalize stuffing (linear reduction down to 0 points at 5%)
                density_score = max(0.0, 40.0 - ((density - 2.5) / 2.5) * 40.0)
                suggestions.append(f"Keyword '{keyword}' density is too high ({density:.2f}%). Reduce to avoid keyword stuffing.")

            # Component Scores
            headline_score = 20.0 if in_headline else 0.0
            intro_score = 20.0 if in_intro else 0.0
            subs_score = 20.0 if in_subs else 0.0

            if not in_headline:
                suggestions.append(f"Add the keyword '{keyword}' to your headline.")
            if not in_intro:
                suggestions.append(f"Mention the keyword '{keyword}' in the opening paragraph.")
            if not in_subs and subheadings:
                suggestions.append(f"Include the keyword '{keyword}' in at least one subheading.")

            kw_score = density_score + headline_score + intro_score + subs_score
            total_score += kw_score

            keyword_metrics[keyword] = KeywordMetrics(
                keyword=keyword,
                count=count,
                density=round(density, 2),
                in_headline=in_headline,
                in_introduction=in_intro,
                in_subheadings=in_subs,
                status=status
            )

        # Average the scores over all unique keywords
        avg_score = round(total_score / len(keywords), 1) if keywords else 0.0

        # Word count suggestion
        if word_count < 300:
            suggestions.append("The article is very short. Consider expanding it to at least 500 words for better SEO ranking.")
            avg_score = max(0.0, avg_score - 10.0)  # penalty for very short text

        logger.info("SEO analysis complete", score=avg_score, suggestions_count=len(suggestions))
        
        return SEOResponse(
            score=avg_score,
            keyword_metrics=keyword_metrics,
            word_count=word_count,
            suggestions=suggestions
        )


# ── CrewAI Tool Integration ────────────────────────────────────────────────────
class CrewAISEOTool(BaseTool):
    """
    CrewAI agent tool wrapper. Allows agents to run SEO checks and get recommendations.
    """
    name: str = "SEO Keyword Analyzer Tool"
    description: str = (
        "Analyzes an article against a list of target keywords to evaluate density and "
        "placement (headline, introduction, subheadings). "
        "Expects two inputs: 'text' (the article content) and 'keywords' (a list of keyword strings)."
    )

    def _run(self, text: str, keywords: List[str]) -> str:
        try:
            analyzer = SEOKeywordAnalyzer()
            res = analyzer.analyze(text, keywords)

            report = [
                f"SEO Evaluation Report",
                f"──────────────────────",
                f"Overall SEO Score: {res.score}/100",
                f"Word Count: {res.word_count}",
                f"\nKeyword Breakdown:"
            ]

            for kw, metrics in res.keyword_metrics.items():
                placement = []
                if metrics.in_headline: placement.append("Headline")
                if metrics.in_introduction: placement.append("Introduction")
                if metrics.in_subheadings: placement.append("Subheadings")
                placement_str = ", ".join(placement) if placement else "None"

                report.append(
                    f"  * '{kw}':"
                    f"\n    - Occurrences: {metrics.count}"
                    f"\n    - Density: {metrics.density}% ({metrics.status.upper()})"
                    f"\n    - Placement: {placement_str}"
                )

            if res.suggestions:
                report.append("\nSuggestions for Improvement:")
                for suggestion in res.suggestions:
                    report.append(f"  - {suggestion}")
            else:
                report.append("\nAwesome! The article is fully optimized for the target keywords.")

            return "\n".join(report)

        except Exception as e:
            return f"Error executing SEO Keyword Analyzer: {str(e)}"
