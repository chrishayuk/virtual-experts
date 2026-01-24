"""Data generators for arithmetic trace training data.

Usage (module-level):
    from chuk_virtual_expert_arithmetic.generators import entity_track, arithmetic
    examples = entity_track.generate(50)

Usage (class wrapper with seed):
    from chuk_virtual_expert_arithmetic.generators import TraceGenerator
    gen = TraceGenerator(seed=42)
    examples = gen.generate_all(n_per_type=10)
"""

from chuk_virtual_expert_arithmetic.generators import (
    arithmetic,
    comparison,
    entity_track,
    percentage,
    rate_equation,
)


class TraceGenerator:
    """Convenience wrapper over per-type generator modules.

    Provides seed-based determinism and a unified generate_all() interface.
    """

    def __init__(self, seed: int | None = None) -> None:
        import random
        self._rng = random.Random(seed)

    def _seeded_generate(self, module, n: int) -> list[dict]:
        """Generate with temporarily seeded global random."""
        import random
        state = random.getstate()
        random.seed(self._rng.randint(0, 2**32 - 1))
        try:
            return module.generate(n)
        finally:
            random.setstate(state)

    def generate_entity_track(self, n: int = 10) -> list[dict]:
        return self._seeded_generate(entity_track, n)

    def generate_arithmetic(self, n: int = 10) -> list[dict]:
        return self._seeded_generate(arithmetic, n)

    def generate_rate_equation(self, n: int = 10) -> list[dict]:
        return self._seeded_generate(rate_equation, n)

    def generate_comparison(self, n: int = 10) -> list[dict]:
        return self._seeded_generate(comparison, n)

    def generate_percentage(self, n: int = 10) -> list[dict]:
        return self._seeded_generate(percentage, n)

    def generate_all(self, n_per_type: int = 10) -> list[dict]:
        """Generate examples for all expert types (equal distribution)."""
        examples = []
        examples.extend(self.generate_entity_track(n_per_type))
        examples.extend(self.generate_arithmetic(n_per_type))
        examples.extend(self.generate_rate_equation(n_per_type))
        examples.extend(self.generate_comparison(n_per_type))
        examples.extend(self.generate_percentage(n_per_type))
        self._shuffle(examples)
        return examples

    def generate_balanced(self, n: int = 235) -> list[dict]:
        """Generate examples with balanced distribution weighted by complexity.

        Distribution (matches GSM-8K training proportions):
            entity_track: 42%
            arithmetic:   17%
            rate_equation: 17%
            comparison:   17%
            percentage:    7%
        """
        n_entity = max(1, int(n * 0.42))
        n_arith = max(1, int(n * 0.17))
        n_rate = max(1, int(n * 0.17))
        n_comp = max(1, int(n * 0.17))
        n_pct = max(1, int(n * 0.07))

        examples = []
        examples.extend(self.generate_entity_track(n_entity))
        examples.extend(self.generate_arithmetic(n_arith))
        examples.extend(self.generate_rate_equation(n_rate))
        examples.extend(self.generate_comparison(n_comp))
        examples.extend(self.generate_percentage(n_pct))
        self._shuffle(examples)
        return examples

    def _shuffle(self, examples: list[dict]) -> None:
        import random
        state = random.getstate()
        random.seed(self._rng.randint(0, 2**32 - 1))
        random.shuffle(examples)
        random.setstate(state)


__all__ = [
    "TraceGenerator",
    "entity_track",
    "arithmetic",
    "rate_equation",
    "comparison",
    "percentage",
]
