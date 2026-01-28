"""Constraint validation and retry logic.

Validates that generated variables satisfy constraints,
and regenerates if needed.

Usage:
    validator = ConstraintValidator()
    variables = validator.apply(constraints, variables, regenerate_fn)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from chuk_virtual_expert_arithmetic.core.expression import ExpressionError, SafeEvaluator

logger = logging.getLogger(__name__)


class ConstraintValidator:
    """Validates and enforces constraints on generated variables.

    Constraints are expressions that must evaluate to values within bounds.
    If constraints are violated, variables are regenerated up to max_attempts.
    """

    def __init__(
        self,
        evaluator: SafeEvaluator | None = None,
        max_attempts: int = 10,
    ) -> None:
        """Initialize the validator.

        Args:
            evaluator: Expression evaluator to use
            max_attempts: Maximum regeneration attempts
        """
        self._evaluator = evaluator or SafeEvaluator()
        self._max_attempts = max_attempts

    def check(
        self,
        constraints: dict[str, dict[str, Any]],
        variables: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Check if all constraints are satisfied.

        Args:
            constraints: Dict of expression -> {"min": ..., "max": ...}
            variables: Current variable values

        Returns:
            Tuple of (all_satisfied, list of violated constraint expressions)
        """
        violated = []

        for expr, bounds in constraints.items():
            try:
                value = self._evaluator.evaluate(expr, variables)
                min_val = bounds.get("min", float("-inf"))
                max_val = bounds.get("max", float("inf"))

                if not (min_val <= value <= max_val):
                    violated.append(expr)

            except ExpressionError:
                # Expression error = constraint violated
                violated.append(expr)

        return len(violated) == 0, violated

    def apply(
        self,
        constraints: dict[str, dict[str, Any]],
        variables: dict[str, Any],
        regenerate: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        """Apply constraints, regenerating variables if needed.

        Args:
            constraints: Dict of expression -> bounds
            variables: Initial variable values
            regenerate: Function to call to regenerate variables

        Returns:
            Variables that satisfy all constraints (or best effort after max_attempts)
        """
        if not constraints:
            return variables

        for _attempt in range(self._max_attempts):
            satisfied, violated = self.check(constraints, variables)
            if satisfied:
                return variables

            # Regenerate and try again
            variables = regenerate()

        # Log warning and return best effort
        _, still_violated = self.check(constraints, variables)
        if still_violated:
            logger.warning(
                "Constraint validation failed after %d attempts. "
                "Violated constraints: %s. Returning best effort.",
                self._max_attempts,
                still_violated,
            )
        return variables

    def validate_expressions(
        self,
        constraints: dict[str, dict[str, Any]],
        available_vars: set[str],
    ) -> list[str]:
        """Validate constraint expressions before use.

        Args:
            constraints: Dict of expression -> bounds
            available_vars: Set of variable names that will be available

        Returns:
            List of error messages (empty if all valid)
        """
        errors: list[str] = []

        for expr in constraints.keys():
            expr_errors = self._evaluator.validate(expr, available_vars)
            if expr_errors:
                errors.extend(f"Constraint '{expr}': {e}" for e in expr_errors)

        return errors
