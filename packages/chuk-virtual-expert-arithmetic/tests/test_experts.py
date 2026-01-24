"""Tests for arithmetic trace-solving experts."""

from __future__ import annotations

import pytest

from chuk_virtual_expert.registry_v2 import ExpertRegistry
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
    def setup_method(self):
        self.expert = EntityTrackExpert()

    def test_can_handle_gives(self):
        assert self.expert.can_handle("Alice has 10 eggs. She gives 3 to Bob.")

    def test_can_handle_remaining(self):
        assert self.expert.can_handle("How many are left after eating 5?")

    def test_cannot_handle_percent(self):
        assert not self.expert.can_handle("What is 20% off $100?")

    def test_consume(self):
        steps = [
            {"init": "eggs", "value": 16},
            {"consume": {"entity": "eggs", "amount": 3}},
            {"consume": {"entity": "eggs", "amount": 4}},
            {"query": "eggs"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 9

    def test_transfer(self):
        steps = [
            {"init": "alice", "value": 20},
            {"init": "bob", "value": 5},
            {"transfer": {"from": "alice", "to": "bob", "amount": 7}},
            {"query": "bob"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 12

    def test_add(self):
        steps = [
            {"init": "items", "value": 10},
            {"add": {"entity": "items", "amount": 5}},
            {"query": "items"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 15

    def test_consume_then_compute(self):
        steps = [
            {"init": "eggs", "value": 16},
            {"consume": {"entity": "eggs", "amount": 3}},
            {"consume": {"entity": "eggs", "amount": 4}},
            {"compute": {"op": "mul", "args": ["eggs", 2], "var": "revenue"}},
            {"query": "revenue"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 18

    def test_insufficient_consume(self):
        steps = [
            {"init": "eggs", "value": 5},
            {"consume": {"entity": "eggs", "amount": 10}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "Insufficient" in result.error

    def test_insufficient_transfer(self):
        steps = [
            {"init": "alice", "value": 5},
            {"transfer": {"from": "alice", "to": "bob", "amount": 10}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "Insufficient" in result.error

    def test_consume_uninitialized(self):
        steps = [
            {"consume": {"entity": "missing", "amount": 5}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "not initialized" in result.error


# --- ArithmeticExpert ---


class TestArithmeticExpert:
    def setup_method(self):
        self.expert = ArithmeticExpert()

    def test_can_handle_cost(self):
        assert self.expert.can_handle("How much does it cost?")

    def test_can_handle_total(self):
        assert self.expert.can_handle("What is the total?")

    def test_can_handle_expression(self):
        assert self.expert.can_handle("What is 5 + 3?")

    def test_cannot_handle_weather(self):
        assert not self.expert.can_handle("What is the weather?")

    def test_pure_arithmetic(self):
        steps = [
            {"init": "price", "value": 100},
            {"init": "tax", "value": 8.5},
            {"init": "shipping", "value": 5},
            {"compute": {"op": "add", "args": ["price", "tax"], "var": "with_tax"}},
            {
                "compute": {
                    "op": "add",
                    "args": ["with_tax", "shipping"],
                    "var": "total",
                }
            },
            {"query": "total"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 113.5

    def test_multiplication_chain(self):
        steps = [
            {"init": "unit_price", "value": 12},
            {"init": "quantity", "value": 5},
            {
                "compute": {
                    "op": "mul",
                    "args": ["unit_price", "quantity"],
                    "var": "subtotal",
                }
            },
            {"init": "shipping", "value": 8},
            {
                "compute": {
                    "op": "add",
                    "args": ["subtotal", "shipping"],
                    "var": "total",
                }
            },
            {"query": "total"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 68

    def test_unknown_step_fails(self):
        steps = [
            {"init": "x", "value": 10},
            {"consume": {"entity": "x", "amount": 5}},  # Not arithmetic
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success


# --- PercentageExpert ---


class TestPercentageExpert:
    def setup_method(self):
        self.expert = PercentageExpert()

    def test_can_handle_percent(self):
        assert self.expert.can_handle("What is 20% off?")

    def test_can_handle_discount(self):
        assert self.expert.can_handle("The discount is applied to the price")

    def test_cannot_handle_speed(self):
        assert not self.expert.can_handle("A car travels at 60 km/h")

    def test_percent_off(self):
        steps = [
            {"init": "price", "value": 200},
            {"init": "discount_rate", "value": 25},
            {
                "percent_off": {
                    "base": "price",
                    "rate": "discount_rate",
                    "var": "sale_price",
                }
            },
            {"query": "sale_price"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 150

    def test_percent_increase(self):
        steps = [
            {"init": "rent", "value": 1500},
            {"init": "increase_rate", "value": 10},
            {
                "percent_increase": {
                    "base": "rent",
                    "rate": "increase_rate",
                    "var": "new_rent",
                }
            },
            {"query": "new_rent"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == pytest.approx(1650)

    def test_percent_of(self):
        steps = [
            {"init": "total", "value": 340},
            {"init": "rate", "value": 15},
            {"percent_of": {"base": "total", "rate": "rate", "var": "portion"}},
            {"query": "portion"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 51

    def test_percent_off_literal_rate(self):
        steps = [
            {"init": "price", "value": 100},
            {"percent_off": {"base": "price", "rate": 20, "var": "sale"}},
            {"query": "sale"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 80


# --- RateEquationExpert ---


class TestRateEquationExpert:
    def setup_method(self):
        self.expert = RateEquationExpert()

    def test_can_handle_speed(self):
        assert self.expert.can_handle("A car travels at 60 km/h")

    def test_can_handle_rate(self):
        assert self.expert.can_handle("The rate is 5 per hour")

    def test_cannot_handle_percentage(self):
        assert not self.expert.can_handle("What is 20% off?")

    def test_distance_formula(self):
        steps = [
            {"given": {"speed": 60, "time": 2.5}},
            {"formula": "distance = speed * time"},
            {"compute": {"op": "mul", "args": ["speed", "time"], "var": "distance"}},
            {"query": "distance"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 150

    def test_work_rate(self):
        steps = [
            {"given": {"rate": 120, "hours": 7.5}},
            {"formula": "widgets = rate * hours"},
            {"compute": {"op": "mul", "args": ["rate", "hours"], "var": "widgets"}},
            {"query": "widgets"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 900

    def test_unknown_step_fails(self):
        steps = [
            {"init": "x", "value": 10},
            {"unknown_rate_op": {"something": "bad"}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "Unknown rate_equation operation" in result.error


# --- ComparisonExpert ---


class TestComparisonExpert:
    def setup_method(self):
        self.expert = ComparisonExpert()

    def test_can_handle_more_than(self):
        assert self.expert.can_handle("How many more does Tom have?")

    def test_can_handle_difference(self):
        assert self.expert.can_handle("What is the difference?")

    def test_cannot_handle_total(self):
        assert not self.expert.can_handle("What is the total cost?")

    def test_difference(self):
        steps = [
            {"init": "jerry_books", "value": 12},
            {"compute": {"op": "mul", "args": ["jerry_books", 3], "var": "tom_books"}},
            {
                "compare": {
                    "op": "sub",
                    "args": ["tom_books", "jerry_books"],
                    "var": "difference",
                }
            },
            {"query": "difference"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 24

    def test_ratio_comparison(self):
        steps = [
            {"init": "a", "value": 100},
            {"init": "b", "value": 25},
            {"compare": {"op": "div", "args": ["a", "b"], "var": "ratio"}},
            {"query": "ratio"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 4


# --- TraceVerifier Integration ---


class TestTraceVerifierIntegration:
    def setup_method(self):
        self.registry = ExpertRegistry()
        self.registry.register(EntityTrackExpert())
        self.registry.register(ArithmeticExpert())
        self.registry.register(PercentageExpert())
        self.registry.register(RateEquationExpert())
        self.registry.register(ComparisonExpert())
        self.verifier = TraceVerifier(self.registry)

    def test_entity_track_full(self):
        yaml_str = """
expert: entity_track
trace:
  - {init: eggs, value: 16}
  - {consume: {entity: eggs, amount: 3}}
  - {consume: {entity: eggs, amount: 4}}
  - {compute: {op: mul, args: [eggs, 2], var: revenue}}
  - {query: revenue}
"""
        result = self.verifier.verify(yaml_str, expected_answer=18)
        assert result.answer_correct
        assert result.reward == 1.0

    def test_arithmetic_full(self):
        yaml_str = """
expert: arithmetic
trace:
  - {init: price, value: 100}
  - {init: tax, value: 8.5}
  - {compute: {op: add, args: [price, tax], var: total}}
  - {query: total}
"""
        result = self.verifier.verify(yaml_str, expected_answer=108.5)
        assert result.answer_correct
        assert result.reward == 1.0

    def test_percentage_full(self):
        yaml_str = """
expert: percentage
trace:
  - {init: price, value: 200}
  - {percent_off: {base: price, rate: 25, var: sale_price}}
  - {query: sale_price}
"""
        result = self.verifier.verify(yaml_str, expected_answer=150)
        assert result.answer_correct
        assert result.reward == 1.0

    def test_rate_equation_full(self):
        yaml_str = """
expert: rate_equation
trace:
  - {given: {speed: 60, time: 2.5}}
  - {formula: "distance = speed * time"}
  - {compute: {op: mul, args: [speed, time], var: distance}}
  - {query: distance}
"""
        result = self.verifier.verify(yaml_str, expected_answer=150)
        assert result.answer_correct
        assert result.reward == 1.0

    def test_comparison_full(self):
        yaml_str = """
expert: comparison
trace:
  - {init: jerry, value: 12}
  - {compute: {op: mul, args: [jerry, 3], var: tom}}
  - {compare: {op: sub, args: [tom, jerry], var: diff}}
  - {query: diff}
"""
        result = self.verifier.verify(yaml_str, expected_answer=24)
        assert result.answer_correct
        assert result.reward == 1.0

    def test_wrong_answer_reward(self):
        yaml_str = """
expert: arithmetic
trace:
  - {init: x, value: 10}
  - {query: x}
"""
        result = self.verifier.verify(yaml_str, expected_answer=99)
        assert not result.answer_correct
        assert result.reward == 0.7

    def test_invalid_trace_reward(self):
        yaml_str = """
expert: entity_track
trace:
  - {consume: {entity: missing, amount: 999}}
"""
        result = self.verifier.verify(yaml_str, expected_answer=10)
        assert result.reward == 0.5


# --- TraceGenerator ---


class TestTraceGenerator:
    def setup_method(self):
        self.gen = TraceGenerator(seed=42)

    def test_generate_entity_track(self):
        examples = self.gen.generate_entity_track(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "entity_track"
            assert "trace" in ex
            assert "expected_answer" in ex

    def test_generate_arithmetic(self):
        examples = self.gen.generate_arithmetic(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "arithmetic"

    def test_generate_percentage(self):
        examples = self.gen.generate_percentage(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "percentage"

    def test_generate_rate_equation(self):
        examples = self.gen.generate_rate_equation(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "rate_equation"

    def test_generate_comparison(self):
        examples = self.gen.generate_comparison(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "comparison"

    def test_generate_all(self):
        examples = self.gen.generate_all(n_per_type=3)
        assert len(examples) == 15

    def test_generated_traces_execute_correctly(self):
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
            import yaml

            yaml_str = yaml.dump({"expert": ex["expert"], "trace": ex["trace"]})
            result = verifier.verify(yaml_str, expected_answer=ex["expected_answer"])
            assert result.answer_correct, (
                f"Failed for {ex['expert']}: expected {ex['expected_answer']}, "
                f"got {result.computed_answer}"
            )
