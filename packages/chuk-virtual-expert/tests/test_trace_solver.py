"""Tests for TraceSolverExpert and TraceVerifier."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.models import Trace, TraceStep
from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_solver import TraceSolverExpert
from chuk_virtual_expert.trace_verifier import TraceVerifier

# --- Concrete test expert ---


class SimpleTraceExpert(TraceSolverExpert):
    """Minimal concrete TraceSolverExpert for testing."""

    name: ClassVar[str] = "simple"
    description: ClassVar[str] = "Simple test expert"

    def can_handle(self, prompt: str) -> bool:
        return "simple" in prompt.lower()

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        op = next(iter(step))
        if op == "double":
            var = step["double"]
            if var in state:
                state[var] = state[var] * 2
            return state
        raise ValueError(f"Unknown operation: {op}")


# --- TraceStep and Trace model tests ---


class TestTraceStep:
    def test_operation(self):
        step = TraceStep(raw={"init": "x", "value": 10})
        assert step.operation == "init"

    def test_payload(self):
        step = TraceStep(raw={"init": "x", "value": 10})
        assert step.payload == "x"

    def test_compute_payload(self):
        step = TraceStep(raw={"compute": {"op": "add", "args": [1, 2], "var": "r"}})
        assert step.operation == "compute"
        assert step.payload == {"op": "add", "args": [1, 2], "var": "r"}


class TestTrace:
    def test_from_yaml(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 5}\n  - {query: x}\n"
        trace = Trace.from_yaml(yaml_str)
        assert trace.expert == "simple"
        assert len(trace.steps) == 2
        assert trace.query_var == "x"

    def test_from_yaml_no_query(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 5}\n"
        trace = Trace.from_yaml(yaml_str)
        assert trace.query_var is None

    def test_from_yaml_invalid(self):
        with pytest.raises(ValueError):
            Trace.from_yaml("not a dict")


# --- TraceSolverExpert tests ---


class TestTraceSolverExpert:
    def setup_method(self):
        self.expert = SimpleTraceExpert()

    def test_get_operations(self):
        assert self.expert.get_operations() == ["execute_trace"]

    def test_init_and_query(self):
        steps = [
            {"init": "x", "value": 42},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 42
        assert result.state["x"] == 42.0

    def test_compute_add(self):
        steps = [
            {"init": "a", "value": 10},
            {"init": "b", "value": 20},
            {"compute": {"op": "add", "args": ["a", "b"], "var": "sum"}},
            {"query": "sum"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    def test_compute_sub(self):
        steps = [
            {"init": "a", "value": 50},
            {"init": "b", "value": 20},
            {"compute": {"op": "sub", "args": ["a", "b"], "var": "diff"}},
            {"query": "diff"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    def test_compute_mul(self):
        steps = [
            {"init": "a", "value": 7},
            {"init": "b", "value": 6},
            {"compute": {"op": "mul", "args": ["a", "b"], "var": "product"}},
            {"query": "product"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 42

    def test_compute_div(self):
        steps = [
            {"init": "a", "value": 100},
            {"init": "b", "value": 4},
            {"compute": {"op": "div", "args": ["a", "b"], "var": "quotient"}},
            {"query": "quotient"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 25

    def test_given_step(self):
        steps = [
            {"given": {"speed": 60, "time": 2.5}},
            {"compute": {"op": "mul", "args": ["speed", "time"], "var": "distance"}},
            {"query": "distance"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 150

    def test_formula_step_noop(self):
        steps = [
            {"given": {"rate": 10, "hours": 3}},
            {"formula": "total = rate * hours"},
            {"compute": {"op": "mul", "args": ["rate", "hours"], "var": "total"}},
            {"query": "total"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    def test_state_assertion_pass(self):
        steps = [
            {"init": "x", "value": 10},
            {"state": {"x": 10}},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success

    def test_state_assertion_fail(self):
        steps = [
            {"init": "x", "value": 10},
            {"state": {"x": 99}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "state" in result.error

    def test_domain_step(self):
        steps = [
            {"init": "x", "value": 5},
            {"double": "x"},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 10

    def test_unknown_domain_step(self):
        steps = [
            {"init": "x", "value": 5},
            {"unknown_op": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "Unknown operation" in result.error

    def test_variable_not_found(self):
        steps = [
            {"compute": {"op": "add", "args": ["missing_var", 1], "var": "r"}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "not found" in result.error

    def test_execute_operation(self):
        params = {"trace": [{"init": "x", "value": 7}, {"query": "x"}]}
        data = self.expert.execute_operation("execute_trace", params)
        assert data["success"]
        assert data["answer"] == 7
        assert data["formatted"] == "7"

    def test_execute_operation_unknown(self):
        with pytest.raises(ValueError):
            self.expert.execute_operation("unknown", {})

    def test_int_answer_for_whole_numbers(self):
        steps = [
            {"init": "x", "value": 10.0},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.answer == 10
        assert isinstance(result.answer, int)

    def test_float_answer_for_decimals(self):
        steps = [
            {"init": "x", "value": 10.5},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.answer == 10.5
        assert isinstance(result.answer, float)

    def test_resolve_literal_number(self):
        steps = [
            {"compute": {"op": "add", "args": [3, 4], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 7

    def test_steps_executed_count(self):
        steps = [
            {"init": "x", "value": 1},
            {"init": "y", "value": 2},
            {"compute": {"op": "add", "args": ["x", "y"], "var": "z"}},
            {"query": "z"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.steps_executed == 4

    def test_compute_mod(self):
        steps = [
            {"compute": {"op": "mod", "args": [10, 3], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 1

    def test_compute_pow(self):
        steps = [
            {"compute": {"op": "pow", "args": [2, 10], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 1024

    def test_compute_sqrt(self):
        steps = [
            {"compute": {"op": "sqrt", "args": [144], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 12

    def test_compute_abs(self):
        steps = [
            {"init": "x", "value": -5},
            {"compute": {"op": "abs", "args": ["x"], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 5

    def test_compute_min(self):
        steps = [
            {"compute": {"op": "min", "args": [5, 3, 8], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 3

    def test_compute_max(self):
        steps = [
            {"compute": {"op": "max", "args": [5, 3, 8], "var": "r"}},
            {"query": "r"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 8

    def test_compute_unknown_op(self):
        steps = [
            {"compute": {"op": "unknown_op", "args": [1, 2], "var": "r"}},
        ]
        result = self.expert.execute_trace(steps)
        assert not result.success
        assert "Unknown compute op" in result.error

    def test_query_nonexistent_var(self):
        steps = [
            {"init": "x", "value": 10},
            {"query": "missing"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer is None

    def test_no_query_returns_none(self):
        steps = [
            {"init": "x", "value": 10},
        ]
        result = self.expert.execute_trace(steps)
        assert result.success
        assert result.answer is None

    def test_near_integer_rounding(self):
        """Test that near-integer floats are returned as int."""
        steps = [
            {"init": "x", "value": 9.999999999},
            {"query": "x"},
        ]
        result = self.expert.execute_trace(steps)
        assert result.answer == 10
        assert isinstance(result.answer, int)

    def test_resolve_non_numeric_arg(self):
        """Test resolving a non-string, non-numeric arg."""
        # resolve() should handle arbitrary types by converting to float
        assert self.expert.resolve(True, {}) == 1.0


# --- TraceVerifier tests ---


class TestTraceVerifier:
    def setup_method(self):
        self.registry = ExpertRegistry()
        self.registry.register(SimpleTraceExpert())
        self.verifier = TraceVerifier(self.registry)

    def test_execute_yaml(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 42}\n  - {query: x}\n"
        result = self.verifier.execute_yaml(yaml_str)
        assert result.success
        assert result.answer == 42

    def test_verify_correct_answer(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 42}\n  - {query: x}\n"
        result = self.verifier.verify(yaml_str, expected_answer=42)
        assert result.parsed
        assert result.trace_valid
        assert result.answer_correct
        assert result.reward == 1.0

    def test_verify_wrong_answer(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 42}\n  - {query: x}\n"
        result = self.verifier.verify(yaml_str, expected_answer=99)
        assert result.parsed
        assert result.trace_valid
        assert not result.answer_correct
        assert result.reward == 0.7

    def test_verify_invalid_yaml(self):
        result = self.verifier.verify("{{{{invalid yaml", expected_answer=42)
        assert not result.parsed
        assert result.reward == 0.0

    def test_verify_wrong_expert(self):
        yaml_str = "expert: wrong_name\ntrace:\n  - {init: x, value: 42}\n  - {query: x}\n"
        result = self.verifier.verify(yaml_str, expected_answer=42, expected_expert="simple")
        assert result.parsed
        assert result.reward == 0.3

    def test_verify_trace_error(self):
        yaml_str = "expert: simple\ntrace:\n  - {unknown_op: bad}\n"
        result = self.verifier.verify(yaml_str, expected_answer=42)
        assert result.parsed
        assert not result.trace_valid
        assert result.reward == 0.5

    def test_verify_no_expected(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 42}\n  - {query: x}\n"
        result = self.verifier.verify(yaml_str, expected_answer=None)
        assert result.parsed
        assert result.trace_valid
        assert result.reward == 0.7

    def test_verify_unknown_expert(self):
        yaml_str = "expert: nonexistent\ntrace:\n  - {init: x, value: 1}\n"
        result = self.verifier.execute_yaml(yaml_str)
        assert not result.success
        assert "not found" in result.error

    def test_numeric_tolerance(self):
        yaml_str = "expert: simple\ntrace:\n  - {init: x, value: 10.001}\n  - {query: x}\n"
        result = self.verifier.verify(yaml_str, expected_answer=10.0, tolerance=0.01)
        assert result.answer_correct

    def test_non_trace_solver_expert(self):
        """Test that non-TraceSolverExpert experts are rejected."""
        from chuk_virtual_expert.expert import VirtualExpert

        class DummyExpert(VirtualExpert):
            name: ClassVar[str] = "dummy"
            description: ClassVar[str] = "Not a trace solver"

            def can_handle(self, prompt: str) -> bool:
                return False

            def get_operations(self) -> list[str]:
                return []

            def execute_operation(self, operation: str, parameters: dict) -> dict:
                return {}

        registry = ExpertRegistry()
        registry.register(DummyExpert())
        verifier = TraceVerifier(registry)

        yaml_str = "expert: dummy\ntrace:\n  - {init: x, value: 1}\n"
        result = verifier.execute_yaml(yaml_str)
        assert not result.success
        assert "not a TraceSolverExpert" in result.error

    def test_string_answer_comparison(self):
        """Test _check_answer with non-numeric strings."""
        assert self.verifier._check_answer("hello", "hello")
        assert not self.verifier._check_answer("hello", "world")

    def test_check_answer_none(self):
        """Test _check_answer with None computed."""
        assert not self.verifier._check_answer(None, 42)
