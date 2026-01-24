"""
TraceVerifier - async verification of trace execution against expected answers.

Provides graduated reward scoring for training:
- 0.0: Failed to parse YAML
- 0.3: Parsed but wrong expert
- 0.5: Correct expert but trace execution failed
- 0.7: Trace executed but wrong answer
- 1.0: Correct answer
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import yaml
from pydantic import TypeAdapter

from chuk_virtual_expert.models import TraceResult, VerificationResult
from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_models import BaseTraceStep, TraceStep
from chuk_virtual_expert.trace_solver import TraceSolverExpert

# Type adapter for parsing raw dicts into typed TraceStep unions
_step_adapter: TypeAdapter[TraceStep] = TypeAdapter(TraceStep)


class TraceVerifier:
    """
    Verifies trace execution and computes graduated rewards.

    Uses an ExpertRegistry to dispatch traces to the appropriate expert.
    All methods are async.
    """

    def __init__(self, registry: ExpertRegistry) -> None:
        self._registry = registry

    async def execute_yaml(self, yaml_str: str) -> TraceResult:
        """Parse YAML and execute the trace."""
        expert_name, steps = self._parse_yaml(yaml_str)
        return await self._execute_steps(expert_name, steps)

    async def verify(
        self,
        yaml_str: str,
        expected_answer: Any = None,
        expected_expert: str | None = None,
        tolerance: float = 0.01,
    ) -> VerificationResult:
        """
        Verify a YAML trace output with graduated rewards.

        Reward scale:
        - 0.0: Failed to parse YAML
        - 0.3: Parsed but wrong expert
        - 0.5: Correct expert but trace execution failed
        - 0.7: Trace executed but wrong answer
        - 1.0: Correct answer
        """
        # Try to parse
        try:
            expert_name, steps = self._parse_yaml(yaml_str)
        except Exception as e:
            return VerificationResult(
                parsed=False,
                trace_error=f"YAML parse error: {e}",
                expected_answer=expected_answer,
                reward=0.0,
            )

        # Check expert name
        if expected_expert and expert_name != expected_expert:
            return VerificationResult(
                parsed=True,
                expert=expert_name,
                trace_error=f"Expected expert '{expected_expert}', got '{expert_name}'",
                expected_answer=expected_answer,
                reward=0.3,
            )

        # Execute trace
        result = await self._execute_steps(expert_name, steps)

        if not result.success:
            return VerificationResult(
                parsed=True,
                expert=expert_name,
                trace_valid=False,
                trace_error=result.error,
                final_state=result.state,
                expected_answer=expected_answer,
                reward=0.5,
            )

        # Trace executed successfully
        computed = result.answer

        # No expected answer to check - reward for valid execution
        if expected_answer is None:
            return VerificationResult(
                parsed=True,
                expert=expert_name,
                trace_valid=True,
                computed_answer=computed,
                final_state=result.state,
                reward=0.7,
            )

        # Check answer
        correct = self._check_answer(computed, expected_answer, tolerance)

        return VerificationResult(
            parsed=True,
            expert=expert_name,
            trace_valid=True,
            computed_answer=computed,
            expected_answer=expected_answer,
            answer_correct=correct,
            final_state=result.state,
            reward=1.0 if correct else 0.7,
        )

    def _parse_yaml(self, yaml_str: str) -> tuple[str, Sequence[BaseTraceStep]]:
        """Parse YAML string into expert name and typed steps."""
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML output is not a dict")
        expert_name = data.get("expert", "unknown")
        raw_steps = data.get("trace", [])
        if not isinstance(raw_steps, list):
            raise ValueError("Trace is not a list")
        steps = [_step_adapter.validate_python(s) for s in raw_steps]
        return expert_name, steps

    async def _execute_steps(self, expert_name: str, steps: Sequence[BaseTraceStep]) -> TraceResult:
        """Execute typed steps by dispatching to the appropriate expert."""
        expert = self._registry.get(expert_name)
        if expert is None:
            return TraceResult(
                success=False,
                error=f"Expert '{expert_name}' not found in registry",
                expert=expert_name,
            )

        if not isinstance(expert, TraceSolverExpert):
            return TraceResult(
                success=False,
                error=f"Expert '{expert_name}' is not a TraceSolverExpert",
                expert=expert_name,
            )

        return await expert.execute_trace(steps)

    def _check_answer(self, computed: Any, expected: Any, tolerance: float = 0.01) -> bool:
        """Check if computed answer matches expected."""
        if computed is None:
            return False

        # Numeric comparison with tolerance
        try:
            computed_f = float(computed)
            expected_f = float(expected)
            return abs(computed_f - expected_f) < tolerance
        except (TypeError, ValueError):
            pass

        # String comparison
        return str(computed).strip() == str(expected).strip()
