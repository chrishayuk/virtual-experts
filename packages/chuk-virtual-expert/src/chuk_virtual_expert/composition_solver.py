"""
CompositionSolver - executes composed multi-expert traces in sequence.

Handles traces where the model emits a list of sub-traces, each handled
by a different expert, with outputs wired forward via source references.

Format:
    [
        {"expert": "percentage", "trace": [...]},
        {"expert": "arithmetic", "trace": [...]},
    ]

Wiring: InitStep with source field gets a previous sub-trace's result:
  - "prev.result": The immediately previous sub-trace's query result
  - "sub0.result", "sub1.result", etc.: Specific sub-trace by index
"""

from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter

from chuk_virtual_expert.models import TraceResult
from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_models import InitStep, TraceStep
from chuk_virtual_expert.trace_solver import TraceSolverExpert

_step_adapter: TypeAdapter[TraceStep] = TypeAdapter(TraceStep)


class CompositionSolver:
    """Executes composed multi-expert traces in sequence."""

    def __init__(self, registry: ExpertRegistry) -> None:
        self._registry = registry

    async def execute(self, sub_traces: list[dict[str, Any]]) -> TraceResult:
        """Execute sub-traces in order, piping results forward."""
        if not sub_traces:
            return TraceResult(
                success=False,
                error="Empty composition (no sub-traces)",
                expert="composed",
            )

        # Track all sub-trace results for multi-value wiring
        all_results: list[Any] = []

        for i, sub in enumerate(sub_traces):
            expert_name = sub.get("expert", "unknown")
            raw_steps = sub.get("trace", [])

            if not isinstance(raw_steps, list):
                return TraceResult(
                    success=False,
                    error=f"Sub-trace {i} ({expert_name}): trace is not a list",
                    expert="composed",
                    steps_executed=i,
                )

            # Parse raw dicts into typed steps
            try:
                steps = [_step_adapter.validate_python(s) for s in raw_steps]
            except Exception as e:
                return TraceResult(
                    success=False,
                    error=f"Sub-trace {i} ({expert_name}): step parse error: {e}",
                    expert="composed",
                    steps_executed=i,
                )

            # Resolve source references (prev.result, sub0.result, sub1.result, etc.)
            steps = self._resolve_sources(steps, all_results)

            # Get expert
            expert = self._registry.get(expert_name)
            if expert is None:
                return TraceResult(
                    success=False,
                    error=f"Sub-trace {i}: expert '{expert_name}' not found",
                    expert="composed",
                    steps_executed=i,
                )

            if not isinstance(expert, TraceSolverExpert):
                return TraceResult(
                    success=False,
                    error=f"Sub-trace {i}: '{expert_name}' is not a TraceSolverExpert",
                    expert="composed",
                    steps_executed=i,
                )

            # Execute
            result = await expert.execute_trace(steps)
            if not result.success:
                return TraceResult(
                    success=False,
                    error=f"Sub-trace {i} ({expert_name}): {result.error}",
                    expert="composed",
                    steps_executed=i,
                )

            all_results.append(result.answer)

        return TraceResult(
            success=True,
            answer=all_results[-1] if all_results else None,
            expert="composed",
            steps_executed=len(sub_traces),
        )

    def _resolve_sources(self, steps: list, all_results: list[Any]) -> list:
        """Replace source references with resolved values.

        Supports:
          - "prev.result": The immediately previous sub-trace's result
          - "sub0.result", "sub1.result", etc.: Specific sub-trace by index
        """
        import re

        resolved = []
        for step in steps:
            if isinstance(step, InitStep) and step.source:
                value = 0  # Default if source can't be resolved

                if step.source == "prev.result":
                    # Previous sub-trace result
                    if all_results:
                        value = all_results[-1]
                elif m := re.match(r"sub(\d+)\.result", step.source):
                    # Specific sub-trace by index (sub0.result, sub1.result, etc.)
                    idx = int(m.group(1))
                    if 0 <= idx < len(all_results):
                        value = all_results[idx]

                resolved.append(InitStep(var=step.var, value=value))
            else:
                resolved.append(step)
        return resolved
