"""
utils/quality_gate.py
─────────────────────────────────────────────────────────────────
Automated Quality Gate for Content Pipelines.
Checks grammar, SEO, and plagiarism, and computes a pass/fail status.
─────────────────────────────────────────────────────────────────
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from tools import GrammarCheckTool, SEOKeywordAnalyzer, PlagiarismDetector
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityGateResponse:
    passed: bool
    score: float
    grammar_passed: bool
    grammar_errors_count: int
    seo_passed: bool
    seo_score: float
    plagiarism_passed: bool
    plagiarism_score: float
    reasons: List[str]


class QualityGate:
    """
    Automated gate validation for final content delivery.
    Evaluates:
      - Spelling & Grammar (Max 5 errors)
      - SEO Score (Min 70/100)
      - Plagiarism (Max 15% duplicate sentences)
    """

    def __init__(
        self,
        max_grammar_errors: int = 5,
        min_seo_score: float = 70.0,
        max_plagiarism_pct: float = 15.0
    ):
        self.max_grammar_errors = max_grammar_errors
        self.min_seo_score = min_seo_score
        self.max_plagiarism_pct = max_plagiarism_pct

        # Initialize tools
        self.grammar_tool = GrammarCheckTool()
        self.seo_analyzer = SEOKeywordAnalyzer()
        self.plagiarism_detector = PlagiarismDetector()

        logger.info(
            "QualityGate initialized",
            max_grammar=max_grammar_errors,
            min_seo=min_seo_score,
            max_plagiarism=max_plagiarism_pct
        )

    def evaluate(
        self,
        text: str,
        keywords: List[str],
        reference_docs: Optional[List[str]] = None
    ) -> QualityGateResponse:
        """
        Evaluate article against quality parameters.
        """
        logger.info("Evaluating quality gate", text_len=len(text), keywords=keywords)

        reasons = []
        
        # 1. Spelling & Grammar Check
        try:
            grammar_res = self.grammar_tool.check(text)
            grammar_errors = len(grammar_res.matches)
            grammar_passed = grammar_errors <= self.max_grammar_errors
            if not grammar_passed:
                reasons.append(
                    f"Grammar check failed: found {grammar_errors} errors, "
                    f"limit is {self.max_grammar_errors}."
                )
        except Exception as e:
            logger.error("Grammar check failed in quality gate", error=str(e))
            grammar_errors = 0
            grammar_passed = False
            reasons.append(f"Grammar check error: {str(e)}")

        # 2. SEO Score Check
        try:
            seo_res = self.seo_analyzer.analyze(text, keywords)
            seo_score = seo_res.score
            seo_passed = seo_score >= self.min_seo_score
            if not seo_passed:
                reasons.append(
                    f"SEO optimization failed: score is {seo_score}/100, "
                    f"minimum required is {self.min_seo_score}."
                )
            # Add detailed keyword status suggestions if failed
            for kw, metrics in seo_res.keyword_metrics.items():
                if metrics.status == "stuffed":
                    reasons.append(f"SEO Warning: Keyword '{kw}' is stuffed ({metrics.density}%).")
                elif metrics.status == "not_found":
                    reasons.append(f"SEO Warning: Keyword '{kw}' was not found in the text.")
        except Exception as e:
            logger.error("SEO check failed in quality gate", error=str(e))
            seo_score = 0.0
            seo_passed = False
            reasons.append(f"SEO check error: {str(e)}")

        # 3. Plagiarism Check (Semantic Similarity)
        plagiarism_score = 0.0
        plagiarism_passed = True
        
        if reference_docs:
            try:
                plag_res = self.plagiarism_detector.check(text, reference_docs)
                plagiarism_score = plag_res.score
                plagiarism_passed = plagiarism_score <= self.max_plagiarism_pct
                if not plagiarism_passed:
                    reasons.append(
                        f"Plagiarism check failed: duplicate content is {plagiarism_score}%, "
                        f"maximum limit allowed is {self.max_plagiarism_pct}%."
                    )
            except Exception as e:
                logger.error("Plagiarism check failed in quality gate", error=str(e))
                plagiarism_passed = False
                reasons.append(f"Plagiarism check error: {str(e)}")
        else:
            logger.info("Plagiarism check skipped: no reference documents provided")

        # ── Compute Overall Quality Score (0 - 100) ───────────────────────────
        # Components:
        # - Grammar: 100 minus 10 points per error (min 0)
        # - SEO: seo_score
        # - Plagiarism: 100 minus plagiarism_score (if tested)
        grammar_score_comp = max(0.0, 100.0 - (grammar_errors * 10.0))
        
        if reference_docs:
            plag_score_comp = 100.0 - plagiarism_score
            # Weights: Grammar (30%), SEO (40%), Plagiarism (30%)
            overall_score = (grammar_score_comp * 0.3) + (seo_score * 0.4) + (plag_score_comp * 0.3)
        else:
            # Weights: Grammar (40%), SEO (60%)
            overall_score = (grammar_score_comp * 0.4) + (seo_score * 0.6)

        overall_score = round(overall_score, 1)
        passed = grammar_passed and seo_passed and plagiarism_passed

        logger.info(
            "Quality gate evaluation finished",
            passed=passed,
            score=overall_score,
            reasons_count=len(reasons)
        )

        return QualityGateResponse(
            passed=passed,
            score=overall_score,
            grammar_passed=grammar_passed,
            grammar_errors_count=grammar_errors,
            seo_passed=seo_passed,
            seo_score=seo_score,
            plagiarism_passed=plagiarism_passed,
            plagiarism_score=plagiarism_score,
            reasons=reasons
        )
