"""Template perturbation for GSM-8K generalization.

Breaks template regularity to improve transfer learning to real benchmarks.

Usage:
    perturbator = TemplatePerturbator(seed=42)
    perturbed = perturbator.perturb("Alice has 5 apples...", level=0.3)
"""

from __future__ import annotations

import random


class TemplatePerturbator:
    """Perturbs generated queries to break template fingerprints.

    Applies random variations to make synthetic data more like real-world
    math problems (e.g., GSM-8K), improving model transfer.

    Perturbation types:
    - Filler phrases: Add natural language filler
    - Question form variation: Vary how questions are asked
    - Clause reordering: Change sentence structure
    - Synonym substitution: Replace common words
    """

    # Filler phrases to add at sentence starts
    FILLER_PHRASES = [
        "As it turns out, ",
        "Interestingly, ",
        "Now, ",
        "Here's the situation: ",
        "Consider this: ",
        "So, ",
        "Well, ",
        "Actually, ",
        "You see, ",
        "",  # Empty = no filler
        "",
        "",  # Weight toward no filler
    ]

    # Question form variations
    QUESTION_STARTERS = {
        "How many": [
            "How many",
            "What is the total number of",
            "Find the number of",
            "Calculate how many",
            "Determine how many",
            "What's the count of",
        ],
        "How much": [
            "How much",
            "What is the total amount of",
            "Find the amount of",
            "Calculate the total",
            "What's the total",
        ],
        "What is": [
            "What is",
            "What's",
            "Find",
            "Calculate",
            "Determine",
            "Figure out",
        ],
    }

    # Common word synonyms for variety
    SYNONYMS = {
        "has": ["owns", "possesses", "holds"],
        "gets": ["receives", "obtains", "acquires"],
        "gives": ["hands", "passes", "transfers"],
        "buys": ["purchases", "gets", "picks up"],
        "sells": ["trades", "exchanges"],
        "makes": ["creates", "produces", "crafts"],
        "total": ["altogether", "in all", "combined"],
        "each": ["every", "per", "apiece"],
        "more": ["additional", "extra"],
        "left": ["remaining", "left over"],
    }

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the perturbator.

        Args:
            seed: Random seed for reproducibility
        """
        self._rng = random.Random(seed)

    def perturb(self, query: str, level: float = 0.3) -> str:
        """Apply random perturbations to a generated query.

        Args:
            query: The original query text
            level: Perturbation probability (0-1). Higher = more changes.

        Returns:
            Perturbed query
        """
        if level <= 0:
            return query

        result = query

        # Apply each perturbation type with probability
        if self._rng.random() < level:
            result = self._add_filler_phrase(result)

        if self._rng.random() < level:
            result = self._vary_question_form(result)

        if self._rng.random() < level * 0.5:  # Less aggressive
            result = self._synonym_substitution(result)

        return result

    def _add_filler_phrase(self, text: str) -> str:
        """Add a filler phrase to the beginning."""
        filler = self._rng.choice(self.FILLER_PHRASES)
        if filler and not text[0].isupper():
            return text
        if filler:
            # Lowercase the first letter of original if adding filler
            if text and text[0].isupper():
                text = text[0].lower() + text[1:]
            return filler + text
        return text

    def _vary_question_form(self, text: str) -> str:
        """Vary question phrasing."""
        for original, variations in self.QUESTION_STARTERS.items():
            if original in text:
                replacement = self._rng.choice(variations)
                return text.replace(original, replacement, 1)
        return text

    def _synonym_substitution(self, text: str) -> str:
        """Replace some words with synonyms."""
        words = text.split()
        result_words = []

        for word in words:
            lower = word.lower().rstrip(".,?!")
            punct = word[len(lower) :] if len(word) > len(lower) else ""

            if lower in self.SYNONYMS and self._rng.random() < 0.3:
                synonym = self._rng.choice(self.SYNONYMS[lower])
                # Preserve capitalization
                if word[0].isupper():
                    synonym = synonym.capitalize()
                result_words.append(synonym + punct)
            else:
                result_words.append(word)

        return " ".join(result_words)

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator."""
        self._rng = random.Random(seed)


class NumericDiversifier:
    """Generates numerically diverse values for training variety.

    Provides methods to generate numbers that:
    - Require carrying in addition
    - Require borrowing in subtraction
    - Are not "round" numbers (multiples of 10)
    - Match difficulty profiles
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the diversifier.

        Args:
            seed: Random seed for reproducibility
        """
        self._rng = random.Random(seed)

    def generate_carrying_pair(self, min_val: int = 10, max_val: int = 99) -> tuple[int, int]:
        """Generate a pair of numbers whose ones digits sum > 10.

        This forces carrying in addition.

        Args:
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Tuple of (a, b) where a + b requires carrying
        """
        # Ensure ones digits sum > 10
        while True:
            a = self._rng.randint(min_val, max_val)
            b = self._rng.randint(min_val, max_val)
            ones_a = a % 10
            ones_b = b % 10
            if ones_a + ones_b >= 10:
                return (a, b)

    def generate_borrowing_pair(self, min_val: int = 20, max_val: int = 99) -> tuple[int, int]:
        """Generate a pair where subtraction requires borrowing.

        Args:
            min_val: Minimum value for the larger number
            max_val: Maximum value for the larger number

        Returns:
            Tuple of (larger, smaller) where larger - smaller requires borrowing
        """
        while True:
            larger = self._rng.randint(min_val, max_val)
            # Smaller must have larger ones digit
            ones_larger = larger % 10
            smaller_max = larger - 1
            smaller_min = max(1, min_val // 2)

            if smaller_max <= smaller_min:
                continue

            smaller = self._rng.randint(smaller_min, smaller_max)
            ones_smaller = smaller % 10

            if ones_smaller > ones_larger:
                return (larger, smaller)

    def avoid_round_number(self, min_val: int = 1, max_val: int = 100, attempts: int = 10) -> int:
        """Generate a number that's not a multiple of 10.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            attempts: Max attempts before giving up

        Returns:
            A non-round number
        """
        for _ in range(attempts):
            value = self._rng.randint(min_val, max_val)
            if value % 10 != 0:
                return value
        # Fallback: just return non-round
        value = self._rng.randint(min_val, max_val)
        if value % 10 == 0:
            value += self._rng.randint(1, 9)
            value = min(value, max_val)
        return value

    def generate_by_difficulty(
        self, difficulty: str = "medium", min_val: int = 1, max_val: int = 100
    ) -> int:
        """Generate a number based on difficulty level.

        Args:
            difficulty: "easy", "medium", or "hard"
            min_val: Base minimum
            max_val: Base maximum

        Returns:
            Generated number
        """
        if difficulty == "easy":
            # Small, often round numbers
            return self._rng.choice([5, 10, 15, 20, 25, 30])

        elif difficulty == "hard":
            # Larger, non-round numbers
            return self.avoid_round_number(max(min_val, 50), max(max_val, 200))

        else:  # medium
            return self._rng.randint(min_val, max_val)

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator."""
        self._rng = random.Random(seed)
