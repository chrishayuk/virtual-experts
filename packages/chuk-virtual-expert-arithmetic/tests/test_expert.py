"""Tests for arithmetic trace-solving experts."""

from __future__ import annotations

import pytest
from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_models import (
    InitStep,
    QueryStep,
)
from chuk_virtual_expert.trace_verifier import TraceVerifier

from chuk_virtual_expert_arithmetic import (
    ArithmeticExpert,
    ComparisonExpert,
    EntityTrackExpert,
    PercentageExpert,
    RateEquationExpert,
)
from chuk_virtual_expert_arithmetic.generators import TraceGenerator

# --- EntityTrackExpert ---


class TestEntityTrackExpert:
    def test_can_handle_gives(self, entity_track_expert: EntityTrackExpert) -> None:
        assert entity_track_expert.can_handle("Alice has 10 eggs. She gives 3 to Bob.")

    def test_can_handle_remaining(self, entity_track_expert: EntityTrackExpert) -> None:
        assert entity_track_expert.can_handle("How many are left after eating 5?")

    def test_cannot_handle_percent(self, entity_track_expert: EntityTrackExpert) -> None:
        assert not entity_track_expert.can_handle("What is 20% off $100?")

    @pytest.mark.asyncio
    async def test_consume(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "eggs", "value": 16},
                    {"op": "consume", "entity": "eggs", "amount": 3},
                    {"op": "consume", "entity": "eggs", "amount": 4},
                    {"op": "query", "var": "eggs"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 9

    @pytest.mark.asyncio
    async def test_transfer(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "alice", "value": 20},
                    {"op": "init", "var": "bob", "value": 5},
                    {"op": "transfer", "from_entity": "alice", "to_entity": "bob", "amount": 7},
                    {"op": "query", "var": "bob"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 12

    @pytest.mark.asyncio
    async def test_add(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "items", "value": 10},
                    {"op": "add_entity", "entity": "items", "amount": 5},
                    {"op": "query", "var": "items"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 15

    @pytest.mark.asyncio
    async def test_consume_then_compute(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "eggs", "value": 16},
                    {"op": "consume", "entity": "eggs", "amount": 3},
                    {"op": "consume", "entity": "eggs", "amount": 4},
                    {"op": "compute", "compute_op": "mul", "args": ["eggs", 2], "var": "revenue"},
                    {"op": "query", "var": "revenue"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 18

    @pytest.mark.asyncio
    async def test_insufficient_consume(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "eggs", "value": 5},
                    {"op": "consume", "entity": "eggs", "amount": 10},
                ],
            },
        )
        assert not result["success"]
        assert "Insufficient" in result["error"]

    @pytest.mark.asyncio
    async def test_insufficient_transfer(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "alice", "value": 5},
                    {"op": "transfer", "from_entity": "alice", "to_entity": "bob", "amount": 10},
                ],
            },
        )
        assert not result["success"]
        assert "Insufficient" in result["error"]

    @pytest.mark.asyncio
    async def test_consume_uninitialized(self, entity_track_expert: EntityTrackExpert) -> None:
        result = await entity_track_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "consume", "entity": "missing", "amount": 5},
                ],
            },
        )
        assert not result["success"]
        assert "not initialized" in result["error"]


# --- ArithmeticExpert ---


class TestArithmeticExpert:
    def test_can_handle_cost(self, arithmetic_expert: ArithmeticExpert) -> None:
        assert arithmetic_expert.can_handle("How much does it cost?")

    def test_can_handle_total(self, arithmetic_expert: ArithmeticExpert) -> None:
        assert arithmetic_expert.can_handle("What is the total?")

    def test_can_handle_expression(self, arithmetic_expert: ArithmeticExpert) -> None:
        assert arithmetic_expert.can_handle("What is 5 + 3?")

    def test_cannot_handle_weather(self, arithmetic_expert: ArithmeticExpert) -> None:
        assert not arithmetic_expert.can_handle("What is the weather?")

    @pytest.mark.asyncio
    async def test_pure_arithmetic(self, arithmetic_expert: ArithmeticExpert) -> None:
        result = await arithmetic_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "price", "value": 100},
                    {"op": "init", "var": "tax", "value": 8.5},
                    {"op": "init", "var": "shipping", "value": 5},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["price", "tax"],
                        "var": "with_tax",
                    },
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["with_tax", "shipping"],
                        "var": "total",
                    },
                    {"op": "query", "var": "total"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 113.5

    @pytest.mark.asyncio
    async def test_multiplication_chain(self, arithmetic_expert: ArithmeticExpert) -> None:
        result = await arithmetic_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "unit_price", "value": 12},
                    {"op": "init", "var": "quantity", "value": 5},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["unit_price", "quantity"],
                        "var": "subtotal",
                    },
                    {"op": "init", "var": "shipping", "value": 8},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["subtotal", "shipping"],
                        "var": "total",
                    },
                    {"op": "query", "var": "total"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 68

    @pytest.mark.asyncio
    async def test_unknown_step_fails(self, arithmetic_expert: ArithmeticExpert) -> None:
        result = await arithmetic_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 10},
                    {"op": "consume", "entity": "x", "amount": 5},
                ],
            },
        )
        assert not result["success"]


# --- PercentageExpert ---


class TestPercentageExpert:
    def test_can_handle_percent(self, percentage_expert: PercentageExpert) -> None:
        assert percentage_expert.can_handle("What is 20% off?")

    def test_can_handle_discount(self, percentage_expert: PercentageExpert) -> None:
        assert percentage_expert.can_handle("The discount is applied to the price")

    def test_cannot_handle_speed(self, percentage_expert: PercentageExpert) -> None:
        assert not percentage_expert.can_handle("A car travels at 60 km/h")

    @pytest.mark.asyncio
    async def test_percent_off(self, percentage_expert: PercentageExpert) -> None:
        result = await percentage_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "price", "value": 200},
                    {"op": "init", "var": "discount_rate", "value": 25},
                    {
                        "op": "percent_off",
                        "base": "price",
                        "rate": "discount_rate",
                        "var": "sale_price",
                    },
                    {"op": "query", "var": "sale_price"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 150

    @pytest.mark.asyncio
    async def test_percent_increase(self, percentage_expert: PercentageExpert) -> None:
        result = await percentage_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "rent", "value": 1500},
                    {"op": "init", "var": "increase_rate", "value": 10},
                    {
                        "op": "percent_increase",
                        "base": "rent",
                        "rate": "increase_rate",
                        "var": "new_rent",
                    },
                    {"op": "query", "var": "new_rent"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == pytest.approx(1650)

    @pytest.mark.asyncio
    async def test_percent_of(self, percentage_expert: PercentageExpert) -> None:
        result = await percentage_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "total", "value": 340},
                    {"op": "init", "var": "rate", "value": 15},
                    {"op": "percent_of", "base": "total", "rate": "rate", "var": "portion"},
                    {"op": "query", "var": "portion"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 51

    @pytest.mark.asyncio
    async def test_percent_off_literal_rate(self, percentage_expert: PercentageExpert) -> None:
        result = await percentage_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "price", "value": 100},
                    {"op": "percent_off", "base": "price", "rate": 20, "var": "sale"},
                    {"op": "query", "var": "sale"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 80


# --- RateEquationExpert ---


class TestRateEquationExpert:
    def test_can_handle_speed(self, rate_equation_expert: RateEquationExpert) -> None:
        assert rate_equation_expert.can_handle("A car travels at 60 km/h")

    def test_can_handle_rate(self, rate_equation_expert: RateEquationExpert) -> None:
        assert rate_equation_expert.can_handle("The rate is 5 per hour")

    def test_cannot_handle_percentage(self, rate_equation_expert: RateEquationExpert) -> None:
        assert not rate_equation_expert.can_handle("What is 20% off?")

    @pytest.mark.asyncio
    async def test_distance_formula(self, rate_equation_expert: RateEquationExpert) -> None:
        result = await rate_equation_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "given", "values": {"speed": 60, "time": 2.5}},
                    {"op": "formula", "expression": "distance = speed * time"},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["speed", "time"],
                        "var": "distance",
                    },
                    {"op": "query", "var": "distance"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 150

    @pytest.mark.asyncio
    async def test_work_rate(self, rate_equation_expert: RateEquationExpert) -> None:
        result = await rate_equation_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "given", "values": {"rate": 120, "hours": 7.5}},
                    {"op": "formula", "expression": "widgets = rate * hours"},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["rate", "hours"],
                        "var": "widgets",
                    },
                    {"op": "query", "var": "widgets"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 900

    @pytest.mark.asyncio
    async def test_unknown_step_fails(self, rate_equation_expert: RateEquationExpert) -> None:
        result = await rate_equation_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 10},
                    {"op": "consume", "entity": "x", "amount": 5},
                ],
            },
        )
        assert not result["success"]


# --- ComparisonExpert ---


class TestComparisonExpert:
    def test_can_handle_more_than(self, comparison_expert: ComparisonExpert) -> None:
        assert comparison_expert.can_handle("How many more does Tom have?")

    def test_can_handle_difference(self, comparison_expert: ComparisonExpert) -> None:
        assert comparison_expert.can_handle("What is the difference?")

    def test_cannot_handle_total(self, comparison_expert: ComparisonExpert) -> None:
        assert not comparison_expert.can_handle("What is the total cost?")

    @pytest.mark.asyncio
    async def test_difference(self, comparison_expert: ComparisonExpert) -> None:
        result = await comparison_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "jerry_books", "value": 12},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["jerry_books", 3],
                        "var": "tom_books",
                    },
                    {
                        "op": "compare",
                        "compute_op": "sub",
                        "args": ["tom_books", "jerry_books"],
                        "var": "difference",
                    },
                    {"op": "query", "var": "difference"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 24

    @pytest.mark.asyncio
    async def test_ratio_comparison(self, comparison_expert: ComparisonExpert) -> None:
        result = await comparison_expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "a", "value": 100},
                    {"op": "init", "var": "b", "value": 25},
                    {"op": "compare", "compute_op": "div", "args": ["a", "b"], "var": "ratio"},
                    {"op": "query", "var": "ratio"},
                ],
            },
        )
        assert result["success"]
        assert result["answer"] == 4


# --- TraceVerifier Integration ---


class TestTraceVerifierIntegration:
    @pytest.fixture(autouse=True)
    def _setup_verifier(self) -> None:
        registry = ExpertRegistry()
        registry.register(EntityTrackExpert())
        registry.register(ArithmeticExpert())
        registry.register(PercentageExpert())
        registry.register(RateEquationExpert())
        registry.register(ComparisonExpert())
        self.verifier = TraceVerifier(registry)

    @pytest.mark.asyncio
    async def test_entity_track_full(self) -> None:
        yaml_str = """
expert: entity_track
trace:
  - {op: init, var: eggs, value: 16}
  - {op: consume, entity: eggs, amount: 3}
  - {op: consume, entity: eggs, amount: 4}
  - {op: compute, compute_op: mul, args: [eggs, 2], var: revenue}
  - {op: query, var: revenue}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=18)
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_arithmetic_full(self) -> None:
        yaml_str = """
expert: arithmetic
trace:
  - {op: init, var: price, value: 100}
  - {op: init, var: tax, value: 8.5}
  - {op: compute, compute_op: add, args: [price, tax], var: total}
  - {op: query, var: total}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=108.5)
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_percentage_full(self) -> None:
        yaml_str = """
expert: percentage
trace:
  - {op: init, var: price, value: 200}
  - {op: percent_off, base: price, rate: 25, var: sale_price}
  - {op: query, var: sale_price}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=150)
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_rate_equation_full(self) -> None:
        yaml_str = """
expert: rate_equation
trace:
  - {op: given, values: {speed: 60, time: 2.5}}
  - {op: formula, expression: "distance = speed * time"}
  - {op: compute, compute_op: mul, args: [speed, time], var: distance}
  - {op: query, var: distance}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=150)
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_comparison_full(self) -> None:
        yaml_str = """
expert: comparison
trace:
  - {op: init, var: jerry, value: 12}
  - {op: compute, compute_op: mul, args: [jerry, 3], var: tom}
  - {op: compare, compute_op: sub, args: [tom, jerry], var: diff}
  - {op: query, var: diff}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=24)
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_wrong_answer_reward(self) -> None:
        yaml_str = """
expert: arithmetic
trace:
  - {op: init, var: x, value: 10}
  - {op: query, var: x}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=99)
        assert not result.answer_correct
        assert result.reward == 0.7

    @pytest.mark.asyncio
    async def test_invalid_trace_reward(self) -> None:
        yaml_str = """
expert: entity_track
trace:
  - {op: consume, entity: missing, amount: 999}
"""
        result = await self.verifier.verify(yaml_str, expected_answer=10)
        assert result.reward == 0.5


# --- TraceGenerator ---


class TestTraceGenerator:
    @pytest.fixture(autouse=True)
    def _setup_generator(self) -> None:
        self.gen = TraceGenerator(seed=42)

    def test_generate_entity_track(self) -> None:
        examples = self.gen.generate_entity_track(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "entity_track"
            assert len(ex.trace) > 0
            assert ex.answer is not None

    def test_generate_arithmetic(self) -> None:
        examples = self.gen.generate_arithmetic(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "arithmetic"

    def test_generate_percentage(self) -> None:
        examples = self.gen.generate_percentage(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "percentage"

    def test_generate_rate_equation(self) -> None:
        examples = self.gen.generate_rate_equation(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "rate_equation"

    def test_generate_comparison(self) -> None:
        examples = self.gen.generate_comparison(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "comparison"

    def test_generate_all(self) -> None:
        examples = self.gen.generate_all(n_per_type=3)
        assert len(examples) == 15

    def test_model_dump_produces_valid_format(self) -> None:
        examples = self.gen.generate_arithmetic(1)
        data = examples[0].model_dump(mode="json")
        assert data["expert"] == "arithmetic"
        assert isinstance(data["trace"], list)
        assert data["trace"][0]["op"] == "init"

    def test_traces_have_typed_steps(self) -> None:
        examples = self.gen.generate_entity_track(5)
        for ex in examples:
            # All traces should end with QueryStep
            assert isinstance(ex.trace[-1], QueryStep)
            # First step should be InitStep
            assert isinstance(ex.trace[0], InitStep)

    @pytest.mark.asyncio
    async def test_generated_traces_execute_correctly(self) -> None:
        """Verify that generated traces produce correct answers."""
        registry = ExpertRegistry()
        registry.register(EntityTrackExpert())
        registry.register(ArithmeticExpert())
        registry.register(PercentageExpert())
        registry.register(RateEquationExpert())
        registry.register(ComparisonExpert())
        verifier = TraceVerifier(registry)

        examples = self.gen.generate_all(n_per_type=5)
        for ex in examples:
            # Use model_dump(mode="json") for clean YAML serialization
            data = ex.model_dump(mode="json")
            import yaml

            yaml_str = yaml.dump({"expert": data["expert"], "trace": data["trace"]})
            result = await verifier.verify(yaml_str, expected_answer=data["answer"])
            assert result.answer_correct, (
                f"Failed for {data['expert']}: expected {data['answer']}, got {result.computed_answer}"
            )
