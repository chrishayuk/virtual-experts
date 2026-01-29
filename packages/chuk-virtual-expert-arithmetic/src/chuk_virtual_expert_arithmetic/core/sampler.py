"""Vocabulary sampling from schema specifications.

Samples vocabulary items (names, items, phrases) based on vocab specs.

Usage:
    sampler = VocabSampler(vocab)
    items = sampler.sample(schema.vocab)
"""

from __future__ import annotations

import random
from typing import Any

from chuk_virtual_expert_arithmetic.core.transforms import pluralize
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

        Respects distinct_from to ensure unique sampling across related items.

        Args:
            specs: Dict of name -> VocabSpec

        Returns:
            Dict of name -> sampled value(s)
        """
        if specs is None:
            return {}

        items: dict[str, Any] = {}

        for name, spec in specs.items():
            # Collect values to exclude from distinct_from references
            exclude: set[Any] = set()
            if spec.distinct_from:
                for ref_name in spec.distinct_from:
                    if ref_name in items:
                        exclude.add(items[ref_name])

            value = self.sample_one(spec, exclude=exclude)
            items[name] = value

            # Auto-add plural form for countable_singular items
            if spec.path and "countable_singular" in spec.path and isinstance(value, str):
                items[f"{name}_plural"] = pluralize(value)

        return items

    def sample_one(self, spec: VocabSpec, exclude: set[Any] | None = None) -> Any:
        """Sample a single vocabulary item.

        Args:
            spec: Vocabulary specification
            exclude: Values to exclude from sampling (for distinct_from support)

        Returns:
            Sampled value
        """
        if spec.type == "person_with_pronouns":
            return self._vocab.person_with_pronouns()

        elif spec.type == "choice":
            values = spec.values or []
            if exclude:
                values = [v for v in values if v not in exclude]
            return self._rng.choice(values) if values else ""

        elif spec.path:
            if spec.sample:
                return self._vocab.sample(spec.path, spec.sample)
            else:
                return self._sample_with_exclusion(spec.path, exclude)

        return None

    def _sample_with_exclusion(self, path: str, exclude: set[Any] | None = None) -> Any:
        """Sample from a vocab path, excluding certain values.

        Args:
            path: Vocab path to sample from
            exclude: Values to exclude

        Returns:
            Sampled value not in exclude set
        """
        items = self._vocab.get(path)
        if not items or not isinstance(items, list):
            return self._vocab.random(path)

        if exclude:
            available = [item for item in items if item not in exclude]
            if available:
                return self._rng.choice(available)

        # Fallback to random if no exclusions or all excluded
        return self._rng.choice(items) if items else None

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator.

        Args:
            seed: New seed value
        """
        self._rng = random.Random(seed)
