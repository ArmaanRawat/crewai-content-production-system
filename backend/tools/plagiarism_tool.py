"""
tools/plagiarism_tool.py
─────────────────────────────────────────────────────────────────
Semantic Plagiarism Detection tool using SentenceTransformers.
─────────────────────────────────────────────────────────────────
"""

import re
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
from sentence_transformers import util
from crewai.tools import BaseTool
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Structured results for programmatic usage (e.g. Quality Gate) ─────────────
@dataclass
class PlagiarizedSentence:
    text: str
    matched_text: str
    similarity: float
    source_index: int


@dataclass
class PlagiarismResponse:
    score: float                  # Percentage of plagiarized sentences (0 - 100)
    matches: List[PlagiarizedSentence]
    is_safe: bool                 # True if plagiarism score is below threshold
    threshold: float


# ── Plain Python Plagiarism Detector ──────────────────────────────────────────
class PlagiarismDetector:
    """
    Programmatic plagiarism detector comparing text against reference documents
    semantically using SentenceTransformers.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """
        Lazily load and cache the SentenceTransformer model.
        """
        if cls._model is None:
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except ImportError:
                logger.error("Failed to import sentence_transformers. Package might not be installed.")
                raise
        return cls._model

    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold
        logger.info("PlagiarismDetector initialized", threshold=threshold)

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into clean sentences.
        """
        # Split by punctuation followed by space
        raw_sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            # Ignore short sentences/fragments (e.g. less than 15 characters)
            if s_clean and len(s_clean) >= 15:
                sentences.append(s_clean)
        return sentences

    def check(self, text: str, reference_docs: List[str]) -> PlagiarismResponse:
        """
        Check an article text against a list of reference documents.
        Returns a detailed similarity analysis.
        """
        logger.info("Checking for plagiarism", text_len=len(text), ref_docs_count=len(reference_docs))

        if not text.strip():
            return PlagiarismResponse(score=0.0, matches=[], is_safe=True, threshold=self.threshold)

        if not reference_docs:
            return PlagiarismResponse(score=0.0, matches=[], is_safe=True, threshold=self.threshold)

        # ── Split texts into sentences ───────────────────────────────────────
        input_sentences = self._split_into_sentences(text)
        if not input_sentences:
            return PlagiarismResponse(score=0.0, matches=[], is_safe=True, threshold=self.threshold)

        # Map reference sentences back to their source document index
        ref_sentences = []
        ref_doc_mapping = []
        for doc_idx, doc in enumerate(reference_docs):
            doc_sentences = self._split_into_sentences(doc)
            for sentence in doc_sentences:
                ref_sentences.append(sentence)
                ref_doc_mapping.append(doc_idx)

        if not ref_sentences:
            return PlagiarismResponse(score=0.0, matches=[], is_safe=True, threshold=self.threshold)

        # ── Semantic Embedding Similarity ─────────────────────────────────────
        try:
            model = self.get_model()

            # Compute embeddings
            logger.info("Encoding input sentences", count=len(input_sentences))
            input_embeddings = model.encode(input_sentences, convert_to_tensor=True, show_progress_bar=False)
            
            logger.info("Encoding reference sentences", count=len(ref_sentences))
            ref_embeddings = model.encode(ref_sentences, convert_to_tensor=True, show_progress_bar=False)

            # Compute cosine similarity matrix
            cos_scores = util.cos_sim(input_embeddings, ref_embeddings)

            # Convert to numpy for easy processing
            # Ensure it moves to CPU first
            scores_matrix = cos_scores.cpu().numpy()

            matches = []
            plagiarized_count = 0

            # ── Evaluate matches ──────────────────────────────────────────────
            for input_idx, sentence_scores in enumerate(scores_matrix):
                best_match_idx = int(np.argmax(sentence_scores))
                best_score = float(sentence_scores[best_match_idx])

                if best_score >= self.threshold:
                    plagiarized_count += 1
                    matches.append(
                        PlagiarizedSentence(
                            text=input_sentences[input_idx],
                            matched_text=ref_sentences[best_match_idx],
                            similarity=round(best_score, 3),
                            source_index=ref_doc_mapping[best_match_idx]
                        )
                    )

            plagiarism_percentage = (plagiarized_count / len(input_sentences)) * 100
            plagiarism_percentage = round(plagiarism_percentage, 1)

            is_safe = plagiarism_percentage < 15.0  # safe if duplicate content is < 15%
            logger.info("Plagiarism check complete", score=plagiarism_percentage, matches_count=len(matches), is_safe=is_safe)

            return PlagiarismResponse(
                score=plagiarism_percentage,
                matches=matches,
                is_safe=is_safe,
                threshold=self.threshold
            )

        except Exception as e:
            logger.error("Plagiarism detection failed", error=str(e))
            raise


# ── CrewAI Tool Integration ────────────────────────────────────────────────────
class CrewAIPlagiarismTool(BaseTool):
    """
    CrewAI agent tool wrapper. Exposes plagiarism checks to agents.
    """
    name: str = "Semantic Plagiarism Checker Tool"
    description: str = (
        "Useful to verify if an article contains plagiarized or duplicate content from a database "
        "of existing reference texts. "
        "Expects two inputs: 'text' (the article content) and 'reference_docs' (a list of existing texts to check against)."
    )

    def _run(self, text: str, reference_docs: List[str]) -> str:
        try:
            detector = PlagiarismDetector()
            res = detector.check(text, reference_docs)

            report = [
                f"Plagiarism Detection Report",
                f"───────────────────────────",
                f"Overall Plagiarism Score: {res.score}%",
                f"Verdict: {'SAFE' if res.is_safe else 'DUPLICATE CONTENT DETECTED'}",
                f"Threshold: {res.threshold * 100}% similarity",
                f"\nMatches Found:"
            ]

            if not res.matches:
                report.append("  * No duplicate sentence matches found.")
            else:
                for idx, match in enumerate(res.matches, 1):
                    report.append(
                        f"  {idx}. Matched Sentence ({match.similarity * 100:.1f}% similarity):"
                        f"\n     - Checked text: \"{match.text}\""
                        f"\n     - Matched source: \"{match.matched_text}\""
                        f"\n     - Source doc index: {match.source_index}"
                    )

            return "\n".join(report)

        except Exception as e:
            return f"Error executing Plagiarism Checker: {str(e)}"
