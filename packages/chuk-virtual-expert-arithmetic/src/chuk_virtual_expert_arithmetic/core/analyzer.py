"""Template fingerprint analyzer for GSM-8K comparison.

Analyzes generated queries to measure template regularity and compare
linguistic features to GSM-8K distribution.

Usage:
    from chuk_virtual_expert_arithmetic.core.analyzer import TemplateAnalyzer

    analyzer = TemplateAnalyzer()
    queries = [gen.generate(schema).query for schema in schemas]
    score = analyzer.fingerprint_score(queries)
    metrics = analyzer.analyze(queries)
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from typing import Any


class TemplateAnalyzer:
    """Detect and measure template regularity in generated queries."""

    # Common question starters to track
    QUESTION_STARTERS = [
        "How many",
        "How much",
        "What is",
        "What's",
        "What was",
        "What are",
        "Find",
        "Calculate",
        "Determine",
        "Figure out",
    ]

    # Common sentence patterns
    SENTENCE_PATTERNS = [
        r"^\w+ has \d+",  # "X has N..."
        r"^\w+ bought \d+",  # "X bought N..."
        r"^\w+ wants to",  # "X wants to..."
        r"^\w+ went to",  # "X went to..."
        r"If \w+ has",  # "If X has..."
        r"There are \d+",  # "There are N..."
    ]

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self._pattern_cache: dict[str, re.Pattern[str]] = {}
        for pattern in self.SENTENCE_PATTERNS:
            self._pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)

    def fingerprint_score(self, queries: list[str]) -> float:
        """Score how 'templated' a set of queries looks.

        Higher score = more templated/predictable.
        Lower score = more varied/natural.

        Args:
            queries: List of query strings

        Returns:
            Score from 0.0 (very varied) to 1.0 (very templated)
        """
        if not queries:
            return 0.0

        # Measure multiple aspects of template regularity
        scores = []

        # 1. Question starter uniformity (0-1)
        starter_score = self._question_starter_uniformity(queries)
        scores.append(starter_score)

        # 2. Sentence pattern overlap (0-1)
        pattern_score = self._sentence_pattern_overlap(queries)
        scores.append(pattern_score)

        # 3. N-gram repetition (0-1)
        ngram_score = self._ngram_repetition(queries, n=3)
        scores.append(ngram_score)

        # 4. Length uniformity (0-1)
        length_score = self._length_uniformity(queries)
        scores.append(length_score)

        # Average all scores
        return sum(scores) / len(scores)

    def analyze(self, queries: list[str]) -> dict[str, Any]:
        """Comprehensive analysis of query set.

        Args:
            queries: List of query strings

        Returns:
            Dict with various metrics
        """
        if not queries:
            return {"error": "No queries provided"}

        # Basic stats
        lengths = [len(q) for q in queries]
        word_counts = [len(q.split()) for q in queries]
        sentence_counts = [len(re.split(r"[.!?]+", q)) for q in queries]

        # Question analysis
        question_starters = self._count_question_starters(queries)

        # Vocabulary analysis
        all_words = []
        for q in queries:
            all_words.extend(re.findall(r"\b\w+\b", q.lower()))
        vocab_size = len(set(all_words))
        vocab_richness = vocab_size / len(all_words) if all_words else 0

        return {
            "count": len(queries),
            "fingerprint_score": self.fingerprint_score(queries),
            "length": {
                "mean": sum(lengths) / len(lengths),
                "min": min(lengths),
                "max": max(lengths),
                "std": self._std(lengths),
            },
            "word_count": {
                "mean": sum(word_counts) / len(word_counts),
                "min": min(word_counts),
                "max": max(word_counts),
            },
            "sentence_count": {
                "mean": sum(sentence_counts) / len(sentence_counts),
                "min": min(sentence_counts),
                "max": max(sentence_counts),
            },
            "question_starters": question_starters,
            "vocabulary": {
                "total_words": len(all_words),
                "unique_words": vocab_size,
                "richness": vocab_richness,
            },
            "uniformity": {
                "question_starter": self._question_starter_uniformity(queries),
                "sentence_pattern": self._sentence_pattern_overlap(queries),
                "ngram_repetition": self._ngram_repetition(queries, n=3),
                "length": self._length_uniformity(queries),
            },
        }

    def compare_to_target(
        self, queries: list[str], target_metrics: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Compare query metrics to target (e.g., GSM-8K).

        Args:
            queries: List of query strings
            target_metrics: Target metrics dict (uses GSM-8K defaults if None)

        Returns:
            Dict with comparison results
        """
        # Default GSM-8K-like metrics (approximate)
        if target_metrics is None:
            target_metrics = {
                "length_mean": 180,
                "word_count_mean": 45,
                "sentence_count_mean": 4,
                "vocab_richness": 0.35,
                "fingerprint_score": 0.15,  # GSM-8K is very varied
            }

        current = self.analyze(queries)

        return {
            "current": current,
            "target": target_metrics,
            "gaps": {
                "length": current["length"]["mean"] - target_metrics["length_mean"],
                "word_count": current["word_count"]["mean"]
                - target_metrics["word_count_mean"],
                "sentence_count": current["sentence_count"]["mean"]
                - target_metrics["sentence_count_mean"],
                "vocab_richness": current["vocabulary"]["richness"]
                - target_metrics["vocab_richness"],
                "fingerprint_score": current["fingerprint_score"]
                - target_metrics["fingerprint_score"],
            },
            "recommendations": self._generate_recommendations(current, target_metrics),
        }

    def _question_starter_uniformity(self, queries: list[str]) -> float:
        """Measure how uniform question starters are.

        Returns 1.0 if all queries use the same starter, 0.0 if perfectly varied.
        """
        starters = self._count_question_starters(queries)
        if not starters:
            return 0.0

        total = sum(starters.values())
        if total == 0:
            return 0.0

        # Calculate concentration (Herfindahl index)
        hhi = sum((count / total) ** 2 for count in starters.values())
        # Normalize: 1/n (perfect distribution) to 1.0 (single starter)
        n = len(self.QUESTION_STARTERS)
        return (hhi - 1 / n) / (1 - 1 / n) if n > 1 else hhi

    def _count_question_starters(self, queries: list[str]) -> dict[str, int]:
        """Count occurrences of each question starter."""
        counts: dict[str, int] = Counter()
        for query in queries:
            for starter in self.QUESTION_STARTERS:
                if starter.lower() in query.lower():
                    counts[starter] += 1
                    break
        return dict(counts)

    def _sentence_pattern_overlap(self, queries: list[str]) -> float:
        """Measure how often queries match common patterns."""
        matches = 0
        for query in queries:
            for pattern in self._pattern_cache.values():
                if pattern.search(query):
                    matches += 1
                    break
        return matches / len(queries) if queries else 0.0

    def _ngram_repetition(self, queries: list[str], n: int = 3) -> float:
        """Measure n-gram repetition across queries.

        Returns higher score if same n-grams appear frequently.
        """
        all_ngrams: list[tuple[str, ...]] = []
        for query in queries:
            words = re.findall(r"\b\w+\b", query.lower())
            ngrams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
            all_ngrams.extend(ngrams)

        if not all_ngrams:
            return 0.0

        # Count repeated n-grams
        ngram_counts = Counter(all_ngrams)
        repeated = sum(1 for count in ngram_counts.values() if count > 1)

        return repeated / len(ngram_counts) if ngram_counts else 0.0

    def _length_uniformity(self, queries: list[str]) -> float:
        """Measure how uniform query lengths are.

        Returns 1.0 if all same length, approaching 0.0 if very varied.
        """
        lengths = [len(q) for q in queries]
        if not lengths:
            return 0.0

        mean = sum(lengths) / len(lengths)
        if mean == 0:
            return 0.0

        # Coefficient of variation (lower = more uniform)
        std = self._std(lengths)
        cv = std / mean

        # Convert to 0-1 score (0.5 CV -> 0.5 score, 0 CV -> 1.0)
        return max(0.0, 1.0 - cv)

    def _std(self, values: Sequence[float | int]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return float(variance**0.5)

    def _generate_recommendations(
        self, current: dict[str, Any], target: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations based on gaps."""
        recs = []

        if current["length"]["mean"] < target["length_mean"] * 0.8:
            recs.append("Queries are too short. Use gsm8k_style templates.")

        if current["fingerprint_score"] > target["fingerprint_score"] * 1.5:
            recs.append("Queries are too templated. Increase perturbation_level.")

        if current["vocabulary"]["richness"] < target["vocab_richness"] * 0.8:
            recs.append("Vocabulary is limited. Enable messy_vocab for diversity.")

        if current["sentence_count"]["mean"] < target["sentence_count_mean"] * 0.7:
            recs.append("Queries have too few sentences. Use multi-sentence templates.")

        if not recs:
            recs.append("Queries are well-balanced with target metrics.")

        return recs
