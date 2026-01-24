"""
TraceSolverExpert - base class for trace-executing virtual experts.

Provides common trace operations (init, given, compute, formula, query)
and dispatches domain-specific operations to subclass execute_step().
"""

from __future__ import annotations

import math
from abc import abstractmethod
from typing import Any, ClassVar

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import TraceResult


class TraceSolverExpert(VirtualExpert):
    """
    Base class for experts that execute symbolic traces.

    Handles common operations:
    - init: Initialize a variable
    - given: Initialize multiple variables (rate problems)
    - compute: Arithmetic operations with variable references
    - formula: Informational annotation (no-op)
    - query: Specify which variable to return as answer

    Subclasses implement execute_step() for domain-specific operations.
    """

    # Subclasses must override
    name: ClassVar[str] = "trace_solver"
    description: ClassVar[str] = "Base trace solver expert"

    # Numeric tolerance for comparisons
    tolerance: ClassVar[float] = 0.01

    def get_operations(self) -> list[str]:
        """Return available operations."""
        return ["execute_trace"]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation - dispatches execute_trace."""
        if operation == "execute_trace":
            trace_steps = parameters.get("trace", [])
            result = self.execute_trace(trace_steps)
            return {
                "success": result.success,
                "answer": result.answer,
                "state": result.state,
                "error": result.error,
                "steps_executed": result.steps_executed,
                "formatted": str(result.answer) if result.answer is not None else "",
            }
        raise ValueError(f"Unknown operation: {operation}")

    def execute_trace(self, steps: list[dict[str, Any]]) -> TraceResult:
        """
        Execute a sequence of trace steps.

        Handles common operations internally, delegates domain ops to execute_step().
        """
        state: dict[str, Any] = {}
        query_var: str | None = None
        steps_executed = 0

        for i, step in enumerate(steps):
            try:
                # Determine operation type
                op = self._get_step_op(step)

                if op == "init":
                    var = str(step["init"])
                    value = step["value"]
                    state[var] = float(value)

                elif op == "given":
                    g = step["given"]
                    for k, v in g.items():
                        if isinstance(v, (int, float)):
                            state[str(k)] = float(v)

                elif op == "compute":
                    c = step["compute"]
                    op_name = c["op"]
                    args = [self.resolve(a, state) for a in c["args"]]
                    result = self._compute(op_name, args)
                    if "var" in c:
                        state[str(c["var"])] = result

                elif op == "formula":
                    # Informational only
                    pass

                elif op == "query":
                    query_var = str(step["query"])

                elif op == "state":
                    # State assertion
                    for var, expected in step["state"].items():
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
                    # Domain-specific operation - delegate to subclass
                    state = self.execute_step(step, state)

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
    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a domain-specific step.

        Args:
            step: The step dict (e.g., {"transfer": {...}})
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
            # Try parsing as number
            try:
                return float(arg)
            except ValueError:
                raise KeyError(f"Variable not found: {arg}") from None
        return float(arg)

    def _compute(self, op: str, args: list[float]) -> float:
        """Execute arithmetic operation."""
        if op == "add":
            return sum(args)
        elif op == "sub":
            return args[0] - sum(args[1:])
        elif op == "mul":
            result = 1.0
            for a in args:
                result *= a
            return result
        elif op == "div":
            if args[1] == 0:
                return float("inf")
            return args[0] / args[1]
        elif op == "mod":
            return args[0] % args[1]
        elif op == "pow":
            return args[0] ** args[1]
        elif op == "sqrt":
            return math.sqrt(args[0])
        elif op == "abs":
            return abs(args[0])
        elif op == "min":
            return min(args)
        elif op == "max":
            return max(args)
        else:
            raise ValueError(f"Unknown compute op: {op}")

    def _get_step_op(self, step: dict[str, Any]) -> str:
        """Get the operation name from a step dict."""
        for key in step:
            return key
        return "unknown"

    def _resolve_query(self, query_var: str | None, state: dict[str, Any]) -> Any:
        """Resolve the query variable from state."""
        if query_var is None:
            return None
        if query_var in state:
            value = state[query_var]
            # Return as int if close to a whole number (within tolerance)
            if isinstance(value, float) and abs(value - round(value)) < self.tolerance:
                return int(round(value))
            return value
        # Try complex query (e.g., "total - discount")
        return self._resolve_complex_query(query_var, state)

    def _resolve_complex_query(self, query_var: str, state: dict[str, Any]) -> Any:
        """Attempt to resolve a complex query expression."""
        # Simple variable reference that doesn't exist
        return None
