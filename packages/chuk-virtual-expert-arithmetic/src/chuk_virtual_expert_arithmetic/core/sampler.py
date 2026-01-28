"""Vocabulary sampling from schema specifications.

Samples vocabulary items (names, items, phrases) based on vocab specs.

Usage:
    sampler = VocabSampler(vocab)
    items = sampler.sample(schema.vocab)
"""

from __future__ import annotations

import random
from typing import Any

from chuk_virtual_expert_arithmetic.models.schema_spec import VocabSpec


class VocabSampler:
    """Samples vocabulary items from specs.

    Supports:
    - Person with pronouns
    - Path-based vocab references
    - Choice from inline values
    - Multiple item sampling
    """

    def __init__(self, vocab: Any, seed: int | None = None) -> None:
        """Initialize the sampler.

        Args:
            vocab: Vocab instance to sample from
            seed: Random seed for reproducibility
        """
        self._vocab = vocab
        self._rng = random.Random(seed)

    def sample(self, specs: dict[str, VocabSpec] | None) -> dict[str, Any]:
        """Sample all vocabulary items.

        Args:
            specs: Dict of name -> VocabSpec

        Returns:
            Dict of name -> sampled value(s)
        """
        if specs is None:
            return {}

        items: dict[str, Any] = {}

        for name, spec in specs.items():
            value = self.sample_one(spec)
            items[name] = value

            # Auto-add plural form for countable_singular items
            if spec.path and "countable_singular" in spec.path and isinstance(value, str):
                items[f"{name}_plural"] = self._pluralize(value)

        return items

    def sample_one(self, spec: VocabSpec) -> Any:
        """Sample a single vocabulary item.

        Args:
            spec: Vocabulary specification

        Returns:
            Sampled value
        """
        if spec.type == "person_with_pronouns":
            return self._vocab.person_with_pronouns()

        elif spec.type == "choice":
            values = spec.values or []
            return self._rng.choice(values) if values else ""

        elif spec.path:
            if spec.sample:
                return self._vocab.sample(spec.path, spec.sample)
            else:
                return self._vocab.random(spec.path)

        return None

    def _pluralize(self, word: str) -> str:
        """Pluralize a word correctly."""
        if word.endswith(("s", "x", "ch", "sh")):
            return word + "es"
        elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        else:
            return word + "s"

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator.

        Args:
            seed: New seed value
        """
        self._rng = random.Random(seed)
