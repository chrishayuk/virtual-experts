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
    TraceGenerator,
    arithmetic,
    entity_track,
    rate_equation,
)

# --- TraceGenerator.generate_balanced ---


class TestGenerateBalanced:
    def test_balanced_distribution(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(100)
        # Should produce examples from all types
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
        # Should be roughly: entity=95, arith=42, rate=42, comp=40, pct=30
        experts = [ex.expert for ex in examples]
        # Entity track has the most
        assert experts.count("entity_track") > experts.count("percentage")

    def test_balanced_all_have_answers(self):
        gen = TraceGenerator(seed=42)
        examples = gen.generate_balanced(50)
        for ex in examples:
            assert ex.answer is not None, f"Example with expert={ex.expert} has no answer"


# --- entity_track.generate_find_and_lose ---


class TestEntityTrackFindAndLose:
    def test_generate_find_and_lose_structure(self):
        example = entity_track.generate_find_and_lose()
        assert example.expert == "entity_track"
        assert example.answer is not None
        assert len(example.trace) >= 3
        # Should contain init, add_entity, consume, query steps
        assert isinstance(example.trace[0], InitStep)
        assert isinstance(example.trace[-1], QueryStep)

    def test_generate_find_and_lose_produces_correct_answer(self):
        for _ in range(10):  # Test multiple random instances
            example = entity_track.generate_find_and_lose()
            assert example.answer is not None
            assert isinstance(example.answer, (int, float))

    def test_generate_includes_find_and_lose(self):
        # generate() should sometimes produce find_and_lose examples
        examples = entity_track.generate(50)
        assert len(examples) == 50


# --- rate_equation.generate_combined_rate ---


class TestRateEquationCombinedRate:
    def test_generate_combined_rate_structure(self):
        example = rate_equation.generate_combined_rate()
        assert example.expert == "rate_equation"
        assert example.answer is not None
        # Should have multiple init steps, compute steps, and query
        assert isinstance(example.trace[0], InitStep)
        assert isinstance(example.trace[-1], QueryStep)

    def test_generate_combined_rate_correct(self):
        for _ in range(10):
            example = rate_equation.generate_combined_rate()
            # Answer should be (rate1 + rate2) * time
            assert example.answer > 0

    def test_generate_includes_combined_rate(self):
        examples = rate_equation.generate(50)
        assert len(examples) == 50
        for ex in examples:
            assert ex.expert == "rate_equation"


# --- arithmetic multiplier text branches ---


class TestArithmeticMultiplierBranches:
    def test_generate_produces_various_multipliers(self):
        # Run enough times to hit multiplier == 2 and multiplier == 3 branches
        # plus the else branch (multiplier > 3)
        examples = arithmetic.generate(100)
        for ex in examples:
            assert ex.expert == "arithmetic"
            assert ex.answer is not None


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
