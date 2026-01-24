"""Tests for TraceSolverExpert and TraceVerifier."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

import pytest

from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_models import (
    BaseTraceStep,
    ComputeOp,
    ComputeStep,
    FormulaStep,
    GivenStep,
    InitStep,
    QueryStep,
    StateAssertStep,
)
from chuk_virtual_expert.trace_solver import TraceSolverExpert
from chuk_virtual_expert.trace_verifier import TraceVerifier

# --- Custom domain step for testing ---


class DoubleStep(BaseTraceStep):
    """Double a variable's value."""

    op: Literal["double"] = "double"
    var: str


# --- Concrete test expert ---


class SimpleTraceExpert(TraceSolverExpert):
    """Minimal concrete TraceSolverExpert for testing."""

    name: ClassVar[str] = "simple"
    description: ClassVar[str] = "Simple test expert"

    def can_handle(self, prompt: str) -> bool:
        return "simple" in prompt.lower()

    async def execute_step(self, step: BaseTraceStep, state: dict[str, Any]) -> dict[str, Any]:
        if isinstance(step, DoubleStep):
            if step.var in state:
                state[step.var] = state[step.var] * 2
            return state
        raise ValueError(f"Unknown step type: {type(step).__name__}")


# --- TraceSolverExpert tests ---


class TestTraceSolverExpert:
    def setup_method(self):
        self.expert = SimpleTraceExpert()

    def test_get_operations(self):
        assert self.expert.get_operations() == ["execute_trace"]

    @pytest.mark.asyncio
    async def test_init_and_query(self):
        steps = [
            InitStep(var="x", value=42),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 42
        assert result.state["x"] == 42.0

    @pytest.mark.asyncio
    async def test_compute_add(self):
        steps = [
            InitStep(var="a", value=10),
            InitStep(var="b", value=20),
            ComputeStep(compute_op=ComputeOp.ADD, args=["a", "b"], var="sum"),
            QueryStep(var="sum"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    @pytest.mark.asyncio
    async def test_compute_sub(self):
        steps = [
            InitStep(var="a", value=50),
            InitStep(var="b", value=20),
            ComputeStep(compute_op=ComputeOp.SUB, args=["a", "b"], var="diff"),
            QueryStep(var="diff"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    @pytest.mark.asyncio
    async def test_compute_mul(self):
        steps = [
            InitStep(var="a", value=7),
            InitStep(var="b", value=6),
            ComputeStep(compute_op=ComputeOp.MUL, args=["a", "b"], var="product"),
            QueryStep(var="product"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 42

    @pytest.mark.asyncio
    async def test_compute_div(self):
        steps = [
            InitStep(var="a", value=100),
            InitStep(var="b", value=4),
            ComputeStep(compute_op=ComputeOp.DIV, args=["a", "b"], var="quotient"),
            QueryStep(var="quotient"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 25

    @pytest.mark.asyncio
    async def test_given_step(self):
        steps = [
            GivenStep(values={"speed": 60, "time": 2.5}),
            ComputeStep(compute_op=ComputeOp.MUL, args=["speed", "time"], var="distance"),
            QueryStep(var="distance"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 150

    @pytest.mark.asyncio
    async def test_formula_step_noop(self):
        steps = [
            GivenStep(values={"rate": 10, "hours": 3}),
            FormulaStep(expression="total = rate * hours"),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "hours"], var="total"),
            QueryStep(var="total"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 30

    @pytest.mark.asyncio
    async def test_state_assertion_pass(self):
        steps = [
            InitStep(var="x", value=10),
            StateAssertStep(assertions={"x": 10}),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success

    @pytest.mark.asyncio
    async def test_state_assertion_fail(self):
        steps = [
            InitStep(var="x", value=10),
            StateAssertStep(assertions={"x": 99}),
        ]
        result = await self.expert.execute_trace(steps)
        assert not result.success
        assert "state" in result.error

    @pytest.mark.asyncio
    async def test_domain_step(self):
        steps = [
            InitStep(var="x", value=5),
            DoubleStep(var="x"),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 10

    @pytest.mark.asyncio
    async def test_unknown_domain_step(self):
        """Test that unrecognized step types raise in execute_step."""

        class UnknownStep(BaseTraceStep):
            op: Literal["unknown_op"] = "unknown_op"

        steps = [
            InitStep(var="x", value=5),
            UnknownStep(),
        ]
        result = await self.expert.execute_trace(steps)
        assert not result.success
        assert "Unknown step type" in result.error

    @pytest.mark.asyncio
    async def test_variable_not_found(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.ADD, args=["missing_var", 1], var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_operation(self):
        params = {
            "trace": [
                {"op": "init", "var": "x", "value": 7},
                {"op": "query", "var": "x"},
            ]
        }
        data = await self.expert.execute_operation("execute_trace", params)
        assert data["success"]
        assert data["answer"] == 7
        assert data["formatted"] == "7"

    @pytest.mark.asyncio
    async def test_execute_operation_unknown(self):
        with pytest.raises(ValueError):
            await self.expert.execute_operation("unknown", {})

    @pytest.mark.asyncio
    async def test_int_answer_for_whole_numbers(self):
        steps = [
            InitStep(var="x", value=10.0),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.answer == 10
        assert isinstance(result.answer, int)

    @pytest.mark.asyncio
    async def test_float_answer_for_decimals(self):
        steps = [
            InitStep(var="x", value=10.5),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.answer == 10.5
        assert isinstance(result.answer, float)

    @pytest.mark.asyncio
    async def test_resolve_literal_number(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.ADD, args=[3, 4], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 7

    @pytest.mark.asyncio
    async def test_steps_executed_count(self):
        steps = [
            InitStep(var="x", value=1),
            InitStep(var="y", value=2),
            ComputeStep(compute_op=ComputeOp.ADD, args=["x", "y"], var="z"),
            QueryStep(var="z"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.steps_executed == 4

    @pytest.mark.asyncio
    async def test_compute_mod(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.MOD, args=[10, 3], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 1

    @pytest.mark.asyncio
    async def test_compute_pow(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.POW, args=[2, 10], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 1024

    @pytest.mark.asyncio
    async def test_compute_sqrt(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.SQRT, args=[144], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 12

    @pytest.mark.asyncio
    async def test_compute_abs(self):
        steps = [
            InitStep(var="x", value=-5),
            ComputeStep(compute_op=ComputeOp.ABS, args=["x"], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 5

    @pytest.mark.asyncio
    async def test_compute_min(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.MIN, args=[5, 3, 8], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 3

    @pytest.mark.asyncio
    async def test_compute_max(self):
        steps = [
            ComputeStep(compute_op=ComputeOp.MAX, args=[5, 3, 8], var="r"),
            QueryStep(var="r"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer == 8

    @pytest.mark.asyncio
    async def test_compute_invalid_op_via_execute_operation(self):
        """Invalid compute ops are caught during Pydantic parsing."""
        params = {
            "trace": [
                {"op": "compute", "compute_op": "unknown_op", "args": [1, 2], "var": "r"},
            ]
        }
        data = await self.expert.execute_operation("execute_trace", params)
        assert not data["success"]

    @pytest.mark.asyncio
    async def test_query_nonexistent_var(self):
        steps = [
            InitStep(var="x", value=10),
            QueryStep(var="missing"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer is None

    @pytest.mark.asyncio
    async def test_no_query_returns_none(self):
        steps = [
            InitStep(var="x", value=10),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.success
        assert result.answer is None

    @pytest.mark.asyncio
    async def test_near_integer_rounding(self):
        """Test that near-integer floats are returned as int."""
        steps = [
            InitStep(var="x", value=9.999999999),
            QueryStep(var="x"),
        ]
        result = await self.expert.execute_trace(steps)
        assert result.answer == 10
        assert isinstance(result.answer, int)

    def test_resolve_non_numeric_arg(self):
        """Test resolving a non-string, non-numeric arg."""
        assert self.expert.resolve(True, {}) == 1.0


# --- TraceVerifier tests ---


class TestTraceVerifier:
    def setup_method(self):
        self.registry = ExpertRegistry()
        self.registry.register(SimpleTraceExpert())
        self.verifier = TraceVerifier(self.registry)

    @pytest.mark.asyncio
    async def test_execute_yaml(self):
        yaml_str = "expert: simple\ntrace:\n  - op: init\n    var: x\n    value: 42\n  - op: query\n    var: x\n"
        result = await self.verifier.execute_yaml(yaml_str)
        assert result.success
        assert result.answer == 42

    @pytest.mark.asyncio
    async def test_verify_correct_answer(self):
        yaml_str = "expert: simple\ntrace:\n  - op: init\n    var: x\n    value: 42\n  - op: query\n    var: x\n"
        result = await self.verifier.verify(yaml_str, expected_answer=42)
        assert result.parsed
        assert result.trace_valid
        assert result.answer_correct
        assert result.reward == 1.0

    @pytest.mark.asyncio
    async def test_verify_wrong_answer(self):
        yaml_str = "expert: simple\ntrace:\n  - op: init\n    var: x\n    value: 42\n  - op: query\n    var: x\n"
        result = await self.verifier.verify(yaml_str, expected_answer=99)
        assert result.parsed
        assert result.trace_valid
        assert not result.answer_correct
        assert result.reward == 0.7

    @pytest.mark.asyncio
    async def test_verify_invalid_yaml(self):
        result = await self.verifier.verify("{{{{invalid yaml", expected_answer=42)
        assert not result.parsed
        assert result.reward == 0.0

    @pytest.mark.asyncio
    async def test_verify_wrong_expert(self):
        yaml_str = "expert: wrong_name\ntrace:\n  - op: init\n    var: x\n    value: 42\n  - op: query\n    var: x\n"
        result = await self.verifier.verify(yaml_str, expected_answer=42, expected_expert="simple")
        assert result.parsed
        assert result.reward == 0.3

    @pytest.mark.asyncio
    async def test_verify_trace_error(self):
        """Invalid op value causes Pydantic parse error."""
        yaml_str = "expert: simple\ntrace:\n  - op: invalid_step_type\n"
        result = await self.verifier.verify(yaml_str, expected_answer=42)
        assert not result.parsed
        assert result.reward == 0.0

    @pytest.mark.asyncio
    async def test_verify_no_expected(self):
        yaml_str = "expert: simple\ntrace:\n  - op: init\n    var: x\n    value: 42\n  - op: query\n    var: x\n"
        result = await self.verifier.verify(yaml_str, expected_answer=None)
        assert result.parsed
        assert result.trace_valid
        assert result.reward == 0.7

    @pytest.mark.asyncio
    async def test_verify_unknown_expert(self):
        yaml_str = "expert: nonexistent\ntrace:\n  - op: init\n    var: x\n    value: 1\n"
        result = await self.verifier.execute_yaml(yaml_str)
        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_numeric_tolerance(self):
        yaml_str = "expert: simple\ntrace:\n  - op: init\n    var: x\n    value: 10.001\n  - op: query\n    var: x\n"
        result = await self.verifier.verify(yaml_str, expected_answer=10.0, tolerance=0.01)
        assert result.answer_correct

    @pytest.mark.asyncio
    async def test_non_trace_solver_expert(self):
        """Test that non-TraceSolverExpert experts are rejected."""
        from chuk_virtual_expert.expert import VirtualExpert

        class DummyExpert(VirtualExpert):
            name: ClassVar[str] = "dummy"
            description: ClassVar[str] = "Not a trace solver"

            def can_handle(self, prompt: str) -> bool:
                return False

            def get_operations(self) -> list[str]:
                return []

            async def execute_operation(self, operation: str, parameters: dict) -> dict:
                return {}

        registry = ExpertRegistry()
        registry.register(DummyExpert())
        verifier = TraceVerifier(registry)

        yaml_str = "expert: dummy\ntrace:\n  - op: init\n    var: x\n    value: 1\n"
        result = await verifier.execute_yaml(yaml_str)
        assert not result.success
        assert "not a TraceSolverExpert" in result.error

    def test_string_answer_comparison(self):
        """Test _check_answer with non-numeric strings."""
        assert self.verifier._check_answer("hello", "hello")
        assert not self.verifier._check_answer("hello", "world")

    def test_check_answer_none(self):
        """Test _check_answer with None computed."""
        assert not self.verifier._check_answer(None, 42)
