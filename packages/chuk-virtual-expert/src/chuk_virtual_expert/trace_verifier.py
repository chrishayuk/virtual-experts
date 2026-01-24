"""
TraceVerifier - verifies trace execution against expected answers.

Provides graduated reward scoring for training:
- 0.0: Failed to parse YAML
- 0.3: Parsed but wrong expert
- 0.5: Correct expert but trace execution failed
- 0.7: Trace executed but wrong answer
- 1.0: Correct answer
"""

from __future__ import annotations

from typing import Any

from chuk_virtual_expert.models import Trace, TraceResult, VerificationResult
from chuk_virtual_expert.registry_v2 import ExpertRegistry
from chuk_virtual_expert.trace_solver import TraceSolverExpert


class TraceVerifier:
    """
    Verifies trace execution and computes graduated rewards.

    Uses an ExpertRegistry to dispatch traces to the appropriate expert.
    """

    def __init__(self, registry: ExpertRegistry) -> None:
        self._registry = registry

    def execute_yaml(self, yaml_str: str) -> TraceResult:
        """Parse YAML and execute the trace."""
        trace = Trace.from_yaml(yaml_str)
        return self.execute_trace(trace)

    def execute_trace(self, trace: Trace) -> TraceResult:
        """Execute a parsed trace by dispatching to the appropriate expert."""
        expert = self._registry.get(trace.expert)
        if expert is None:
            return TraceResult(
                success=False,
                error=f"Expert '{trace.expert}' not found in registry",
                expert=trace.expert,
            )

        if not isinstance(expert, TraceSolverExpert):
            return TraceResult(
                success=False,
                error=f"Expert '{trace.expert}' is not a TraceSolverExpert",
                expert=trace.expert,
            )

        # Convert TraceStep models back to raw dicts for execution
        raw_steps = [step.raw for step in trace.steps]
        return expert.execute_trace(raw_steps)

    def verify(
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
            trace = Trace.from_yaml(yaml_str)
        except Exception as e:
            return VerificationResult(
                parsed=False,
                trace_error=f"YAML parse error: {e}",
                expected_answer=expected_answer,
                reward=0.0,
            )

        # Check expert name
        if expected_expert and trace.expert != expected_expert:
            return VerificationResult(
                parsed=True,
                expert=trace.expert,
                trace_error=f"Expected expert '{expected_expert}', got '{trace.expert}'",
                expected_answer=expected_answer,
                reward=0.3,
            )

        # Execute trace
        result = self.execute_trace(trace)

        if not result.success:
            return VerificationResult(
                parsed=True,
                expert=trace.expert,
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
                expert=trace.expert,
                trace_valid=True,
                computed_answer=computed,
                final_state=result.state,
                reward=0.7,
            )

        # Check answer
        correct = self._check_answer(computed, expected_answer, tolerance)

        return VerificationResult(
            parsed=True,
            expert=trace.expert,
            trace_valid=True,
            computed_answer=computed,
            expected_answer=expected_answer,
            answer_correct=correct,
            final_state=result.state,
            reward=1.0 if correct else 0.7,
        )

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
