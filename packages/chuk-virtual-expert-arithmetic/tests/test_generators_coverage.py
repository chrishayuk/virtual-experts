"""Additional generator and expert coverage tests."""

from __future__ import annotations

import pytest
from chuk_virtual_expert.trace_models import InitStep, QueryStep

from chuk_virtual_expert_arithmetic import (
    ComparisonExpert,
    EntityTrackExpert,
    PercentageExpert,
)
from chuk_virtual_expert_arithmetic.generators import (
    ALL_ARITHMETIC_SCHEMAS,
    ENTITY_TRACK_SCHEMAS,
    RATE_EQUATION_SCHEMAS,
    SchemaGenerator,
    TraceGenerator,
)

# --- TraceGenerator.generate_balanced ---


class TestGenerateBalanced:
    def test_balanced_distribution(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(100)
        # Should produce examples from all expert types
        experts = {ex.expert for ex in examples}
        assert "entity_track" in experts
        assert "arithmetic" in experts
        assert "rate_equation" in experts
        assert "comparison" in experts
        assert "percentage" in experts

    def test_balanced_minimum_counts(self):
        gen = TraceGenerator(seed=1)
        examples = gen.generate_balanced(10)
        # With n=10, each type should get at least 1
        experts = [ex.expert for ex in examples]
        assert experts.count("entity_track") >= 1
        assert experts.count("arithmetic") >= 1

    def test_balanced_large(self):
        gen = TraceGenerator(seed=99)
        examples = gen.generate_balanced(250)
        # Distribution: entity=25%, arith=35%, rate=10%, comp=18%, pct=12%
        experts = [ex.expert for ex in examples]
        assert experts.count("entity_track") > 0
        assert experts.count("arithmetic") > 0
        # Arithmetic should have the most examples
        assert experts.count("arithmetic") > experts.count("percentage")

    def test_balanced_all_have_answers(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(50)
        for ex in examples:
            assert ex.answer is not None, f"Example with expert={ex.expert} has no answer"

    def test_balanced_returns_consistent_type(self):
        """Default generate_balanced returns only TraceExample objects."""
        from chuk_virtual_expert.trace_example import TraceExample

        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(50)
        for ex in examples:
            assert isinstance(ex, TraceExample)

    def test_balanced_with_composition_returns_mixed_types(self):
        """With include_composition=True, returns mixed TraceExample and dict."""
        from chuk_virtual_expert.trace_example import TraceExample

        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(100, include_composition=True)
        # Should have both TraceExample and dict
        has_trace_example = any(isinstance(ex, TraceExample) for ex in examples)
        has_dict = any(isinstance(ex, dict) for ex in examples)
        assert has_trace_example
        assert has_dict


# --- Entity Track Schema Generation ---


class TestEntityTrackSchemaGeneration:
    def test_generate_entity_track_structure(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_entity_track(10)
        for example in examples:
            assert example.expert == "entity_track"
            assert example.answer is not None
            assert len(example.trace) >= 2
            # Should start with init and end with query
            assert isinstance(example.trace[0], InitStep)
            assert isinstance(example.trace[-1], QueryStep)

    def test_generate_entity_track_correct_answers(self):
        gen = TraceGenerator(seed=123)
        for example in gen.generate_entity_track(20):
            assert example.answer is not None
            assert isinstance(example.answer, (int, float))

    def test_entity_track_schemas_exist(self):
        # Verify we have entity track schemas defined
        assert len(ENTITY_TRACK_SCHEMAS) >= 1
        schema_gen = SchemaGenerator()
        for schema_name in ENTITY_TRACK_SCHEMAS:
            assert schema_name in schema_gen.schema_names


# --- Rate Equation Schema Generation ---


class TestRateEquationSchemaGeneration:
    def test_generate_rate_equation_structure(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_rate_equation(10)
        for example in examples:
            assert example.expert == "rate_equation"
            assert example.answer is not None
            # Should have init steps and query
            assert isinstance(example.trace[0], InitStep)
            assert isinstance(example.trace[-1], QueryStep)

    def test_generate_rate_equation_correct_answers(self):
        gen = TraceGenerator(seed=456)
        for example in gen.generate_rate_equation(20):
            assert example.answer is not None
            assert example.answer > 0

    def test_rate_equation_schemas_exist(self):
        # Verify we have rate equation schemas defined
        assert len(RATE_EQUATION_SCHEMAS) >= 1
        schema_gen = SchemaGenerator()
        for schema_name in RATE_EQUATION_SCHEMAS:
            assert schema_name in schema_gen.schema_names


# --- Arithmetic Schema Generation ---


class TestArithmeticSchemaGeneration:
    def test_generate_arithmetic_structure(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_arithmetic(20)
        for example in examples:
            assert example.expert == "arithmetic"
            assert example.answer is not None

    def test_generate_arithmetic_variety(self):
        # Generate enough to get examples from different schema groups
        gen = TraceGenerator(seed=789)
        examples = gen.generate_arithmetic(50)
        assert len(examples) == 50
        for ex in examples:
            assert ex.expert == "arithmetic"
            assert ex.answer is not None

    def test_arithmetic_schemas_exist(self):
        # Verify we have arithmetic schemas defined
        assert len(ALL_ARITHMETIC_SCHEMAS) >= 1
        schema_gen = SchemaGenerator()
        for schema_name in ALL_ARITHMETIC_SCHEMAS:
            assert schema_name in schema_gen.schema_names


# --- Expert edge cases (uncovered error branches) ---


class TestEntityTrackExpertEdgeCases:
    @pytest.mark.asyncio
    async def test_transfer_initializes_missing_from_entity(self):
        """Transfer where from_entity is not in state should initialize to 0."""
        expert = EntityTrackExpert()
        # This will fail because from_entity starts at 0 and amount > 0
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "bob", "value": 5},
                    {"op": "transfer", "from_entity": "alice", "to_entity": "bob", "amount": 3},
                ],
            },
        )
        # alice not initialized so gets set to 0, then 0 < 3 so insufficient
        assert not result["success"]
        assert "Insufficient" in result["error"]

    @pytest.mark.asyncio
    async def test_add_entity_not_initialized(self):
        """add_entity on uninitialized entity should initialize to 0."""
        expert = EntityTrackExpert()
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "add_entity", "entity": "new_item", "amount": 7},
                    {"op": "query", "var": "new_item"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 7

    @pytest.mark.asyncio
    async def test_unknown_step_type(self):
        """Unknown step type routed to entity_track should raise error."""
        expert = EntityTrackExpert()
        # Use percent_off which entity_track doesn't handle
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 100},
                    {"op": "percent_off", "base": "x", "rate": 20, "var": "y"},
                ],
            },
        )
        assert not result["success"]


class TestComparisonExpertEdgeCases:
    @pytest.mark.asyncio
    async def test_unknown_step_type(self):
        """Unknown step type routed to comparison should raise error."""
        expert = ComparisonExpert()
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 10},
                    {"op": "consume", "entity": "x", "amount": 5},
                ],
            },
        )
        assert not result["success"]


class TestPercentageExpertEdgeCases:
    @pytest.mark.asyncio
    async def test_unknown_step_type(self):
        """Unknown step type routed to percentage should raise error."""
        expert = PercentageExpert()
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 10},
                    {"op": "consume", "entity": "x", "amount": 5},
                ],
            },
        )
        assert not result["success"]
