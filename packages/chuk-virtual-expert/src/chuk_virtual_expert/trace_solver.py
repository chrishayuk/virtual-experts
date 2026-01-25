"""
TraceSolverExpert - async base class for trace-executing virtual experts.

Provides common trace operations (init, given, compute, formula, query, state)
and dispatches domain-specific steps to subclass execute_step().
Uses typed Pydantic step models with isinstance dispatch — no magic strings.
"""

from __future__ import annotations

import math
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import TypeAdapter

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import TraceResult
from chuk_virtual_expert.trace_models import (
    BaseTraceStep,
    ComputeOp,
    ComputeStep,
    FormulaStep,
    GivenStep,
    InitStep,
    QueryStep,
    StateAssertStep,
    TraceStep,
)

# Type adapter for parsing raw dicts into typed TraceStep unions
_step_adapter: TypeAdapter[TraceStep] = TypeAdapter(TraceStep)


class TraceSolverExpert(VirtualExpert):
    """
    Base class for experts that execute symbolic traces.

    Handles common operations via isinstance dispatch:
    - InitStep: Initialize a variable
    - GivenStep: Initialize multiple variables
    - ComputeStep: Arithmetic with ComputeOp enum
    - FormulaStep: Informational annotation (no-op)
    - QueryStep: Specify which variable to return
    - StateAssertStep: Assert expected variable values

    Subclasses implement execute_step() for domain-specific steps.
    """

    # Subclasses must override
    name: ClassVar[str] = "trace_solver"
    description: ClassVar[str] = "Base trace solver expert"

    # Numeric tolerance for comparisons
    tolerance: ClassVar[float] = 0.01

    def get_operations(self) -> list[str]:
        """Return available operations."""
        return ["execute_trace"]

    async def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation - dispatches execute_trace."""
        if operation == "execute_trace":
            raw_steps = parameters.get("trace", [])
            # Parse raw dicts into typed steps
            try:
                steps = [_step_adapter.validate_python(s) for s in raw_steps]
            except Exception as e:
                return {
                    "success": False,
                    "answer": None,
                    "state": {},
                    "error": str(e),
                    "steps_executed": 0,
                    "formatted": "",
                }
            result = await self.execute_trace(steps)
            return {
                "success": result.success,
                "answer": result.answer,
                "state": result.state,
                "error": result.error,
                "steps_executed": result.steps_executed,
                "formatted": str(result.answer) if result.answer is not None else "",
            }
        raise ValueError(f"Unknown operation: {operation}")

    async def execute_trace(self, steps: Sequence[BaseTraceStep]) -> TraceResult:
        """
        Execute a sequence of typed trace steps.

        Handles common steps internally, delegates domain steps to execute_step().

        Enforces: query targets must be computed/modified variables, not raw init values.
        This prevents the model from short-circuiting by querying extracted values directly.
        """
        state: dict[str, Any] = {}
        init_only_vars: set[str] = set()  # Vars set only by init, never modified
        query_var: str | None = None
        steps_executed = 0

        for i, step in enumerate(steps):
            try:
                if isinstance(step, InitStep):
                    state[step.var] = (
                        float(step.value) if isinstance(step.value, (int, float)) else step.value
                    )
                    init_only_vars.add(step.var)

                elif isinstance(step, GivenStep):
                    for k, v in step.values.items():
                        state[k] = float(v)
                        init_only_vars.add(k)

                elif isinstance(step, ComputeStep):
                    args = [self.resolve(a, state) for a in step.args]
                    result = self._compute(step.compute_op, args)
                    if step.var is not None:
                        state[step.var] = result
                        init_only_vars.discard(step.var)

                elif isinstance(step, FormulaStep):
                    pass  # Informational only

                elif isinstance(step, QueryStep):
                    query_var = step.var
                    # Enforce: query must target a computed/modified variable
                    if query_var in init_only_vars:
                        return TraceResult(
                            success=False,
                            error=f"Step {i}: query targets init variable '{query_var}', not a computed result",
                            state=state,
                            expert=self.name,
                            steps_executed=steps_executed,
                        )

                elif isinstance(step, StateAssertStep):
                    for var, expected in step.assertions.items():
                        actual = state.get(var, 0)
                        if abs(float(actual) - float(expected)) > self.tolerance:
                            return TraceResult(
                                success=False,
                                error=f"Step {i}: state {var}={actual}, expected {expected}",
                                state=state,
                                expert=self.name,
                                steps_executed=steps_executed,
                            )

                else:
                    # Domain-specific step - delegate to subclass
                    prev_state = dict(state)
                    state = await self.execute_step(step, state)
                    # Any modified vars are no longer init-only
                    for var in list(init_only_vars):
                        if state.get(var) != prev_state.get(var):
                            init_only_vars.discard(var)

                steps_executed += 1

            except Exception as e:
                return TraceResult(
                    success=False,
                    error=f"Step {i}: {e}",
                    state=state,
                    expert=self.name,
                    steps_executed=steps_executed,
                )

        # Resolve query
        answer = self._resolve_query(query_var, state)

        return TraceResult(
            success=True,
            answer=answer,
            state=state,
            expert=self.name,
            steps_executed=steps_executed,
        )

    @abstractmethod
    async def execute_step(self, step: BaseTraceStep, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a domain-specific step.

        Args:
            step: A typed trace step (e.g., TransferStep, GetForecastStep)
            state: Current variable state

        Returns:
            Updated state dict

        Raises:
            ValueError: If step type is not recognized
        """
        ...

    def resolve(self, arg: Any, state: dict[str, Any]) -> float:
        """Resolve an argument - variable lookup or literal passthrough."""
        if isinstance(arg, (int, float)):
            return float(arg)
        elif isinstance(arg, str):
            if arg in state:
                return float(state[arg])
            try:
                return float(arg)
            except ValueError:
                raise KeyError(f"Variable not found: {arg}") from None
        return float(arg)

    def _compute(self, op: ComputeOp, args: list[float]) -> float:
        """Execute arithmetic operation using ComputeOp enum."""
        if op == ComputeOp.ADD:
            return sum(args)
        elif op == ComputeOp.SUB:
            return args[0] - sum(args[1:])
        elif op == ComputeOp.MUL:
            result = 1.0
            for a in args:
                result *= a
            return result
        elif op == ComputeOp.DIV:
            if args[1] == 0:
                return float("inf")
            return args[0] / args[1]
        elif op == ComputeOp.MOD:
            return args[0] % args[1]
        elif op == ComputeOp.POW:
            return float(args[0] ** args[1])
        elif op == ComputeOp.SQRT:
            return math.sqrt(args[0])
        elif op == ComputeOp.ABS:
            return abs(args[0])
        elif op == ComputeOp.MIN:
            return min(args)
        elif op == ComputeOp.MAX:
            return max(args)
        else:
            raise ValueError(f"Unknown compute op: {op}")

    def _resolve_query(self, query_var: str | None, state: dict[str, Any]) -> Any:
        """Resolve the query variable from state."""
        if query_var is None:
            return None
        if query_var in state:
            value = state[query_var]
            if isinstance(value, float) and abs(value - round(value)) < self.tolerance:
                return int(round(value))
            return value
        return None
