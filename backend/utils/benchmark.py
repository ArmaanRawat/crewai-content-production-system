"""
utils/benchmark.py
─────────────────────────────────────────────────────────────────
Human Evaluation Benchmark for the CrewAI Content Production System.

Generates 3 complete articles on predefined topics, runs each through
the QualityGate, and prints a structured evaluation report.
─────────────────────────────────────────────────────────────────
"""

import time
from dataclasses import dataclass
from typing import List

from utils.logger import get_logger
from utils.quality_gate import QualityGate
from crews.content_crew import run_content_crew

logger = get_logger(__name__)

# ── Benchmark Topic Definitions ───────────────────────────────────────────────

BENCHMARK_TOPICS = [
    {
        "topic": "The Future of Renewable Energy",
        "tone": "informative",
        "word_count": 800,
        "audience": "environmentally conscious general readers",
        "seo_keywords": ["renewable energy", "solar power", "wind energy", "clean energy", "sustainability"],
    },
    {
        "topic": "Machine Learning in Healthcare",
        "tone": "professional",
        "word_count": 900,
        "audience": "healthcare professionals and technology enthusiasts",
        "seo_keywords": ["machine learning", "healthcare AI", "medical diagnosis", "predictive analytics", "patient outcomes"],
    },
    {
        "topic": "Remote Work Productivity Tips",
        "tone": "conversational",
        "word_count": 700,
        "audience": "remote workers and team managers",
        "seo_keywords": ["remote work", "productivity", "work from home", "time management", "collaboration tools"],
    },
]

# ── BenchmarkResult Dataclass ─────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    topic: str
    tone: str
    word_count_target: int
    word_count_actual: int
    quality_score: float
    quality_passed: bool
    grammar_errors: int
    seo_score: float
    plagiarism_score: float
    generation_time_seconds: float
    article_preview: str


# ── Core Benchmark Runner ─────────────────────────────────────────────────────

def run_benchmark() -> List[BenchmarkResult]:
    """
    Runs the full benchmark over all BENCHMARK_TOPICS.

    For each topic:
      - Calls run_content_crew() and measures wall-clock generation time.
      - Evaluates the resulting article with QualityGate.evaluate().
      - Captures a 200-character preview of the article.
      - Logs and skips any topic that raises an exception.

    Returns a list of BenchmarkResult, one per successfully evaluated topic.
    """
    quality_gate = QualityGate()
    results: List[BenchmarkResult] = []

    for entry in BENCHMARK_TOPICS:
        topic = entry["topic"]
        tone = entry["tone"]
        word_count_target = entry["word_count"]
        audience = entry["audience"]
        seo_keywords = entry["seo_keywords"]

        logger.info(
            "Benchmark: starting article generation",
            topic=topic,
            tone=tone,
            word_count=word_count_target,
            audience=audience,
        )

        try:
            # ── Generation ────────────────────────────────────────────────────
            start_time = time.time()
            article = run_content_crew(
                topic=topic,
                tone=tone,
                word_count=word_count_target,
                audience=audience,
            )
            generation_time = round(time.time() - start_time, 2)

            logger.info(
                "Benchmark: article generated",
                topic=topic,
                generation_time_seconds=generation_time,
            )

            # ── Quality Evaluation ────────────────────────────────────────────
            quality_response = quality_gate.evaluate(
                text=article,
                keywords=seo_keywords,
                reference_docs=None,
            )

            # ── Word Count ────────────────────────────────────────────────────
            word_count_actual = len(article.split())

            # ── Article Preview ───────────────────────────────────────────────
            article_preview = article[:200]

            result = BenchmarkResult(
                topic=topic,
                tone=tone,
                word_count_target=word_count_target,
                word_count_actual=word_count_actual,
                quality_score=quality_response.score,
                quality_passed=quality_response.passed,
                grammar_errors=quality_response.grammar_errors_count,
                seo_score=quality_response.seo_score,
                plagiarism_score=quality_response.plagiarism_score,
                generation_time_seconds=generation_time,
                article_preview=article_preview,
            )

            results.append(result)

            logger.info(
                "Benchmark: evaluation complete",
                topic=topic,
                quality_score=quality_response.score,
                quality_passed=quality_response.passed,
            )

        except Exception as exc:
            logger.error(
                "Benchmark: article generation or evaluation failed, skipping topic",
                topic=topic,
                error=str(exc),
            )
            continue

    return results


# ── Report Printer ────────────────────────────────────────────────────────────

def print_benchmark_report(results: List[BenchmarkResult]) -> None:
    """
    Prints a structured human-readable benchmark report to stdout.

    Covers per-article metrics and an overall summary.
    """
    print()
    print("=== HUMAN EVALUATION BENCHMARK REPORT ===")
    print()

    if not results:
        print("No benchmark results to display.")
        return

    for index, result in enumerate(results, start=1):
        pass_label = "PASS" if result.quality_passed else "FAIL"

        print(f"Article {index}: {result.topic}")
        print(f"  Tone              : {result.tone}")
        print(f"  Word Count        : {result.word_count_actual} (target: {result.word_count_target})")
        print(f"  Quality Score     : {result.quality_score}/100")
        print(f"  Quality Gate      : {pass_label}")
        print(f"  Grammar Errors    : {result.grammar_errors}")
        print(f"  SEO Score         : {result.seo_score}/100")
        print(f"  Plagiarism Score  : {result.plagiarism_score}%")
        print(f"  Generation Time   : {result.generation_time_seconds}s")
        print(f"  Article Preview   : {result.article_preview}")
        print()

    # ── Summary Statistics ────────────────────────────────────────────────────
    total_articles = len(results)
    passed_count = sum(1 for r in results if r.quality_passed)
    avg_quality_score = round(
        sum(r.quality_score for r in results) / total_articles, 1
    )
    avg_generation_time = round(
        sum(r.generation_time_seconds for r in results) / total_articles, 2
    )

    print("--- SUMMARY ---")
    print(f"  Total Articles      : {total_articles}")
    print(f"  Passed Quality Gate : {passed_count} / {total_articles}")
    print(f"  Avg Quality Score   : {avg_quality_score}/100")
    print(f"  Avg Generation Time : {avg_generation_time}s")
    print()


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    benchmark_results = run_benchmark()
    print_benchmark_report(benchmark_results)
