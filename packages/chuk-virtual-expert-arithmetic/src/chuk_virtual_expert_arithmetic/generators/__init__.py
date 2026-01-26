"""Data generators for arithmetic trace training data.

Usage (class wrapper with seed):
    from chuk_virtual_expert_arithmetic.generators import TraceGenerator
    gen = TraceGenerator(seed=42)
    examples = gen.generate_balanced(n=100)

Usage (schema-based - data-driven approach):
    from chuk_virtual_expert_arithmetic.generators import SchemaGenerator
    gen = SchemaGenerator()
    print(gen.schema_names)  # List available schemas
    example = gen.generate("price_chain")  # Generate one example
    examples = gen.generate_batch(n=50)  # Generate batch from all schemas
"""

from typing import Any

from chuk_virtual_expert.trace_example import TraceExample

from chuk_virtual_expert_arithmetic.generators import composition
from chuk_virtual_expert_arithmetic.generators.schema_generator import SchemaGenerator

# ============================================================================
# ARITHMETIC SCHEMA GROUPS
# ============================================================================

SEQUENTIAL_SCHEMAS = [
    "price_chain",
    "subtract_chain",
    "multiply_add",
    "divide_multiply",
    "work_rate",
    "combined_rate",
    "div_then_add",
]

INTERLEAVED_SCHEMAS = [
    "interleaved_mul_mul",
    "parallel_merge",
    "chained_mul_sum",
    "chained_mul_sum_gsm8k",  # GSM-8K style phrasing with people
    "chained_mul_sum_inverted",  # GSM-8K style inverted phrasing (Toulouse)
    "consume_then_sell",
    "consume_then_sell_gsm8k",  # GSM-8K style phrasing for consume_then_sell
    "rate_comparison_total",
]

LONG_CHAIN_SCHEMAS = [
    "long_expense_chain",
]

DIVISION_CHAIN_SCHEMAS = [
    "sub_sub_div_div",  # Subtract twice, divide twice (GSM-8K gap pattern)
    "div_chain",  # Chain of divisions (GSM-8K gap pattern)
]

GAP_CLOSING_SCHEMAS = [
    "half_twice",
    "conditional_rate",
    "fraction_simple",
    "shopping_spree",
    # GSM-8K style patterns
    "material_half",  # "X and half that much" pattern
    "material_twice",  # "X and twice that much" pattern
    "decimal_rate_week",  # Decimal rates like "0.5 hours per day"
    "decimal_rate_week",  # Duplicate for higher decimal frequency
    "decimal_multiply",  # Simple decimal multiplication
    "weekly_sprints",  # "X sprints Y times/week, Z meters each"
    "total_minus_given",  # "Need X total, given Y and Z, remainder?"
    # Domain coverage gaps - boosted for better representation
    "distance_rate",  # Distance = speed * time
    "distance_rate",  # Duplicate for higher frequency
    "distance_round_trip",  # Round trip distance
    "school_supplies",  # School domain
    "school_supplies",  # Duplicate for higher frequency
    "classroom_groups",  # Classroom activities
    # NEW: 100-sample eval gap-closing patterns
    "growth_doubled",  # "doubled/tripled" → multiply pattern
    "growth_doubled",  # Duplicate for higher frequency
    "average_three",  # Average of three values
    "remaining_capacity",  # (limit - base) / unit
    "multi_item_cost",  # n1*p1 + n2*p2 multi-entity
    "multi_item_cost",  # Duplicate for higher frequency
    "ratio_split",  # total/(1+r)*r splits
    "time_from_distance",  # time = distance / speed
    "time_from_distance",  # Duplicate for higher frequency
    "twice_relationship",  # "twice as many" → multiply
    "twice_relationship",  # Duplicate - critical pattern
    "twice_relationship",  # Triple for even higher frequency
    "two_period_sum",  # r1*t1 + r2*t2
    "recover_then_multiply",  # (current + consumed) * mult
    "nested_groups",  # groups * subgroups * per
]

ALL_ARITHMETIC_SCHEMAS = (
    SEQUENTIAL_SCHEMAS
    + INTERLEAVED_SCHEMAS
    + LONG_CHAIN_SCHEMAS
    + DIVISION_CHAIN_SCHEMAS
    + GAP_CLOSING_SCHEMAS
)

# ============================================================================
# ENTITY TRACK SCHEMA GROUPS
# ============================================================================

ENTITY_TRACK_SCHEMAS = [
    "entity_simple_transfer",
    "entity_consume_sequence",
    "entity_consume_multiply",
    "entity_bidirectional",
    "entity_find_lose",
]

# ============================================================================
# RATE EQUATION SCHEMA GROUPS
# ============================================================================

RATE_EQUATION_SCHEMAS = [
    "rate_production",
    "rate_distance",
    "rate_consumption",
    "rate_earning",
]

# ============================================================================
# COMPARISON SCHEMA GROUPS
# ============================================================================

COMPARISON_SCHEMAS = [
    "comparison_times_more",
    "comparison_sum_diff",
    "comparison_more_less",
    "comparison_half",
]

# ============================================================================
# PERCENTAGE SCHEMA GROUPS
# ============================================================================

PERCENTAGE_SCHEMAS = [
    "percent_off",
    "percent_increase",
    "percent_tip",
    "percent_simple",
]

# All schemas
ALL_SCHEMAS = (
    ALL_ARITHMETIC_SCHEMAS
    + ENTITY_TRACK_SCHEMAS
    + RATE_EQUATION_SCHEMAS
    + COMPARISON_SCHEMAS
    + PERCENTAGE_SCHEMAS
)


class TraceGenerator:
    """Convenience wrapper for trace generation.

    Provides seed-based determinism and unified generate methods.
    Uses SchemaGenerator for all expert types (data-driven).
    """

    def __init__(self, seed: int | None = None) -> None:
        import random

        self._rng = random.Random(seed)
        self._schema_gen = SchemaGenerator()

    def _seeded_schema_generate(self, schemas: list[str], n: int) -> list[TraceExample]:
        """Generate from schemas with seeded random."""
        import random

        state = random.getstate()
        random.seed(self._rng.randint(0, 2**32 - 1))
        try:
            return self._schema_gen.generate_batch(schemas, n)
        finally:
            random.setstate(state)

    def generate_entity_track(self, n: int = 10) -> list[TraceExample]:
        """Generate entity tracking examples from schemas."""
        return self._seeded_schema_generate(ENTITY_TRACK_SCHEMAS, n)

    def generate_arithmetic(
        self,
        n: int = 10,
        interleaved_ratio: float = 0.3,
        long_chain_ratio: float = 0.1,
        gap_closing_ratio: float = 0.25,
    ) -> list[TraceExample]:
        """Generate arithmetic examples from schemas.

        Args:
            n: Number of examples
            interleaved_ratio: Fraction from interleaved patterns (default 0.3)
            long_chain_ratio: Fraction from long chain patterns (default 0.1)
            gap_closing_ratio: Fraction from gap-closing patterns (default 0.25)
        """
        import random

        state = random.getstate()
        random.seed(self._rng.randint(0, 2**32 - 1))
        try:
            n_long = max(1, int(n * long_chain_ratio))
            n_interleaved = max(1, int(n * interleaved_ratio))
            n_gap_closing = max(1, int(n * gap_closing_ratio))
            n_sequential = n - n_long - n_interleaved - n_gap_closing

            examples: list[TraceExample] = []
            examples.extend(self._schema_gen.generate_batch(LONG_CHAIN_SCHEMAS, n_long))
            examples.extend(self._schema_gen.generate_batch(INTERLEAVED_SCHEMAS, n_interleaved))
            examples.extend(self._schema_gen.generate_batch(GAP_CLOSING_SCHEMAS, n_gap_closing))
            examples.extend(self._schema_gen.generate_batch(SEQUENTIAL_SCHEMAS, n_sequential))

            random.shuffle(examples)
            return examples
        finally:
            random.setstate(state)

    def generate_rate_equation(self, n: int = 10) -> list[TraceExample]:
        """Generate rate equation examples from schemas."""
        return self._seeded_schema_generate(RATE_EQUATION_SCHEMAS, n)

    def generate_comparison(self, n: int = 10) -> list[TraceExample]:
        """Generate comparison examples from schemas."""
        return self._seeded_schema_generate(COMPARISON_SCHEMAS, n)

    def generate_percentage(self, n: int = 10) -> list[TraceExample]:
        """Generate percentage examples from schemas."""
        return self._seeded_schema_generate(PERCENTAGE_SCHEMAS, n)

    def generate_composition(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate compositional (multi-expert) examples."""
        import random as _random

        state = _random.getstate()
        _random.seed(self._rng.randint(0, 2**32 - 1))
        try:
            return composition.generate(n)
        finally:
            _random.setstate(state)

    def generate_all(self, n_per_type: int = 10) -> list[TraceExample]:
        """Generate examples for all expert types (equal distribution)."""
        examples: list[TraceExample] = []
        examples.extend(self.generate_entity_track(n_per_type))
        examples.extend(self.generate_arithmetic(n_per_type))
        examples.extend(self.generate_rate_equation(n_per_type))
        examples.extend(self.generate_comparison(n_per_type))
        examples.extend(self.generate_percentage(n_per_type))
        self._shuffle(examples)
        return examples

    def generate_balanced(
        self,
        n: int = 250,
        include_composition: bool = False,
        interleaved_ratio: float = 0.3,
        long_chain_ratio: float = 0.1,
        gap_closing_ratio: float = 0.25,
    ) -> list[TraceExample]:
        """Generate examples with balanced distribution weighted by complexity.

        Distribution (without composition — default):
            entity_track:  25%, arithmetic: 35%, rate_equation: 10%,
            comparison: 18%, percentage: 12%

        Distribution (with composition):
            entity_track:  20% (5 schema-based patterns)
            arithmetic:    30% (16 schema-based patterns)
            rate_equation: 10% (4 schema-based patterns)
            comparison:    15% (4 schema-based patterns)
            percentage:    10% (4 schema-based patterns)
            composition:   15% (4 patterns, multi-expert)

        Args:
            n: Total number of examples
            include_composition: Include multi-expert composition examples.
                When True, returns mixed list of TraceExample and dict.
                When False (default), returns only TraceExample objects.
            interleaved_ratio: Fraction of arithmetic from interleaved patterns
            long_chain_ratio: Fraction of arithmetic from long chain patterns
            gap_closing_ratio: Fraction of arithmetic from gap-closing patterns

        Returns:
            List of TraceExample objects (when include_composition=False).
            Mixed list of TraceExample and dict (when include_composition=True).
        """
        if include_composition:
            n_entity = max(1, int(n * 0.20))
            n_arith = max(1, int(n * 0.30))
            n_rate = max(1, int(n * 0.10))
            n_comp = max(1, int(n * 0.15))
            n_pct = max(1, int(n * 0.10))
            n_composed = max(1, int(n * 0.15))
        else:
            n_entity = max(1, int(n * 0.25))
            n_arith = max(1, int(n * 0.35))
            n_rate = max(1, int(n * 0.10))
            n_comp = max(1, int(n * 0.18))
            n_pct = max(1, int(n * 0.12))
            n_composed = 0

        examples: list[Any] = []
        examples.extend(self.generate_entity_track(n_entity))
        examples.extend(
            self.generate_arithmetic(
                n_arith,
                interleaved_ratio=interleaved_ratio,
                long_chain_ratio=long_chain_ratio,
                gap_closing_ratio=gap_closing_ratio,
            )
        )
        examples.extend(self.generate_rate_equation(n_rate))
        examples.extend(self.generate_comparison(n_comp))
        examples.extend(self.generate_percentage(n_pct))
        if n_composed > 0:
            examples.extend(self.generate_composition(n_composed))
        self._shuffle(examples)
        return examples

    def _shuffle(self, examples: list[Any]) -> None:
        import random

        state = random.getstate()
        random.seed(self._rng.randint(0, 2**32 - 1))
        random.shuffle(examples)
        random.setstate(state)

    def generate_from_schemas(
        self,
        n: int = 10,
        schema_names: list[str] | None = None,
    ) -> list[TraceExample]:
        """Generate examples from JSON schemas (data-driven approach).

        Args:
            n: Number of examples to generate
            schema_names: List of schemas to use (None = all available)

        Returns:
            List of TraceExamples generated from schemas
        """
        if schema_names is None:
            schema_names = ALL_SCHEMAS
        return self._seeded_schema_generate(schema_names, n)


__all__ = [
    "TraceGenerator",
    "SchemaGenerator",
    "composition",
    "ALL_SCHEMAS",
    "ALL_ARITHMETIC_SCHEMAS",
    "ENTITY_TRACK_SCHEMAS",
    "RATE_EQUATION_SCHEMAS",
    "COMPARISON_SCHEMAS",
    "PERCENTAGE_SCHEMAS",
    "SEQUENTIAL_SCHEMAS",
    "INTERLEAVED_SCHEMAS",
    "LONG_CHAIN_SCHEMAS",
    "DIVISION_CHAIN_SCHEMAS",
    "GAP_CLOSING_SCHEMAS",
]
