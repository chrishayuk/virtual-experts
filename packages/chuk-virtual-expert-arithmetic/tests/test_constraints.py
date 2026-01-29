"""Tests for ConstraintValidator - comprehensive coverage."""

from __future__ import annotations

import logging

import pytest

from chuk_virtual_expert_arithmetic.core.constraints import ConstraintValidator
from chuk_virtual_expert_arithmetic.core.expression import SafeEvaluator


class TestConstraintValidatorInit:
    """Tests for ConstraintValidator initialization."""

    def test_init_default_evaluator(self) -> None:
        """Test default evaluator is created."""
        validator = ConstraintValidator()
        assert validator._evaluator is not None
        assert isinstance(validator._evaluator, SafeEvaluator)

    def test_init_custom_evaluator(self) -> None:
        """Test custom evaluator is used."""
        evaluator = SafeEvaluator()
        validator = ConstraintValidator(evaluator=evaluator)
        assert validator._evaluator is evaluator

    def test_init_default_max_attempts(self) -> None:
        """Test default max_attempts."""
        validator = ConstraintValidator()
        assert validator._max_attempts == 10

    def test_init_custom_max_attempts(self) -> None:
        """Test custom max_attempts."""
        validator = ConstraintValidator(max_attempts=50)
        assert validator._max_attempts == 50


class TestConstraintValidatorCheck:
    """Tests for check method."""

    @pytest.fixture
    def validator(self) -> ConstraintValidator:
        """Create validator instance."""
        return ConstraintValidator()

    def test_check_empty_constraints(self, validator: ConstraintValidator) -> None:
        """Test checking empty constraints."""
        satisfied, violated = validator.check({}, {"a": 5})
        assert satisfied is True
        assert violated == []

    def test_check_satisfied_single_constraint(self, validator: ConstraintValidator) -> None:
        """Test checking single satisfied constraint."""
        constraints = {"a": {"min": 0, "max": 10}}
        variables = {"a": 5}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
        assert violated == []

    def test_check_violated_min_constraint(self, validator: ConstraintValidator) -> None:
        """Test checking violated min constraint."""
        constraints = {"a": {"min": 10, "max": 20}}
        variables = {"a": 5}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is False
        assert "a" in violated

    def test_check_violated_max_constraint(self, validator: ConstraintValidator) -> None:
        """Test checking violated max constraint."""
        constraints = {"a": {"min": 0, "max": 10}}
        variables = {"a": 15}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is False
        assert "a" in violated

    def test_check_multiple_constraints(self, validator: ConstraintValidator) -> None:
        """Test checking multiple constraints."""
        constraints = {
            "a": {"min": 0, "max": 10},
            "b": {"min": 5, "max": 20},
            "a + b": {"min": 10, "max": 30},
        }
        variables = {"a": 5, "b": 10}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
        assert violated == []

    def test_check_complex_expression(self, validator: ConstraintValidator) -> None:
        """Test checking complex expression constraint."""
        constraints = {"a * b + c": {"min": 0, "max": 100}}
        variables = {"a": 5, "b": 10, "c": 3}  # 5*10+3 = 53

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
        assert violated == []

    def test_check_only_min_bound(self, validator: ConstraintValidator) -> None:
        """Test constraint with only min bound."""
        constraints = {"a": {"min": 5}}
        variables = {"a": 10}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
        assert violated == []

    def test_check_only_max_bound(self, validator: ConstraintValidator) -> None:
        """Test constraint with only max bound."""
        constraints = {"a": {"max": 20}}
        variables = {"a": 10}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
        assert violated == []

    def test_check_exact_boundary_min(self, validator: ConstraintValidator) -> None:
        """Test constraint at exact min boundary."""
        constraints = {"a": {"min": 5, "max": 10}}
        variables = {"a": 5}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_check_exact_boundary_max(self, validator: ConstraintValidator) -> None:
        """Test constraint at exact max boundary."""
        constraints = {"a": {"min": 5, "max": 10}}
        variables = {"a": 10}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_check_expression_error(self, validator: ConstraintValidator) -> None:
        """Test constraint with expression error."""
        constraints = {"undefined_var": {"min": 0, "max": 10}}
        variables = {"a": 5}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is False
        assert "undefined_var" in violated

    def test_check_division_expression(self, validator: ConstraintValidator) -> None:
        """Test constraint with division."""
        constraints = {"a / b": {"min": 0, "max": 5}}
        variables = {"a": 10, "b": 5}  # 10/5 = 2

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True


class TestConstraintValidatorApply:
    """Tests for apply method."""

    @pytest.fixture
    def validator(self) -> ConstraintValidator:
        """Create validator instance."""
        return ConstraintValidator(max_attempts=5)

    def test_apply_empty_constraints(self, validator: ConstraintValidator) -> None:
        """Test apply with empty constraints returns original."""
        variables = {"a": 5}
        result = validator.apply({}, variables, lambda: {"a": 999})
        assert result == variables

    def test_apply_already_satisfied(self, validator: ConstraintValidator) -> None:
        """Test apply when constraints already satisfied."""
        constraints = {"a": {"min": 0, "max": 10}}
        variables = {"a": 5}
        regenerate_called = [False]

        def regenerate() -> dict:
            regenerate_called[0] = True
            return {"a": 0}

        result = validator.apply(constraints, variables, regenerate)

        assert result == variables
        assert regenerate_called[0] is False

    def test_apply_needs_regeneration(self, validator: ConstraintValidator) -> None:
        """Test apply when regeneration is needed."""
        constraints = {"a": {"min": 10, "max": 20}}
        initial = {"a": 5}  # Violates min

        def regenerate() -> dict:
            return {"a": 15}  # Satisfies

        result = validator.apply(constraints, initial, regenerate)

        assert result["a"] == 15

    def test_apply_multiple_regenerations(self, validator: ConstraintValidator) -> None:
        """Test apply with multiple regeneration attempts."""
        constraints = {"a": {"min": 90, "max": 100}}
        initial = {"a": 5}

        attempt = [0]

        def regenerate() -> dict:
            attempt[0] += 1
            if attempt[0] < 3:
                return {"a": 50}  # Still violates
            return {"a": 95}  # Satisfies

        result = validator.apply(constraints, initial, regenerate)

        assert result["a"] == 95
        assert attempt[0] == 3

    def test_apply_max_attempts_exceeded(self, validator: ConstraintValidator, caplog) -> None:
        """Test apply when max attempts exceeded."""
        constraints = {"a": {"min": 100, "max": 200}}
        initial = {"a": 5}

        def regenerate() -> dict:
            return {"a": 10}  # Never satisfies

        with caplog.at_level(logging.WARNING):
            result = validator.apply(constraints, initial, regenerate)

        # Should return best effort (last generated value)
        assert result["a"] == 10
        assert any("Constraint validation failed" in record.message for record in caplog.records)

    def test_apply_preserves_other_variables(self, validator: ConstraintValidator) -> None:
        """Test apply preserves variables not in constraint."""
        constraints = {"a": {"min": 10, "max": 20}}
        initial = {"a": 5, "b": 100, "c": "hello"}

        def regenerate() -> dict:
            return {"a": 15, "b": 100, "c": "hello"}

        result = validator.apply(constraints, initial, regenerate)

        assert result["a"] == 15
        assert result["b"] == 100
        assert result["c"] == "hello"


class TestConstraintValidatorValidateExpressions:
    """Tests for validate_expressions method."""

    @pytest.fixture
    def validator(self) -> ConstraintValidator:
        """Create validator instance."""
        return ConstraintValidator()

    def test_validate_valid_expressions(self, validator: ConstraintValidator) -> None:
        """Test validating valid expressions."""
        constraints = {
            "a": {"min": 0, "max": 10},
            "a + b": {"min": 0, "max": 20},
        }
        available_vars = {"a", "b"}

        errors = validator.validate_expressions(constraints, available_vars)

        assert errors == []

    def test_validate_missing_variable(self, validator: ConstraintValidator) -> None:
        """Test validating expression with missing variable."""
        constraints = {
            "a + c": {"min": 0, "max": 10},
        }
        available_vars = {"a", "b"}

        errors = validator.validate_expressions(constraints, available_vars)

        assert len(errors) > 0
        assert any("c" in error for error in errors)

    def test_validate_invalid_syntax(self, validator: ConstraintValidator) -> None:
        """Test validating expression with invalid syntax."""
        constraints = {
            "a +": {"min": 0, "max": 10},  # Invalid syntax
        }
        available_vars = {"a", "b"}

        errors = validator.validate_expressions(constraints, available_vars)

        assert len(errors) > 0

    def test_validate_multiple_errors(self, validator: ConstraintValidator) -> None:
        """Test validating multiple expressions with errors."""
        constraints = {
            "a + unknown1": {"min": 0, "max": 10},
            "b * unknown2": {"min": 0, "max": 10},
        }
        available_vars = {"a", "b"}

        errors = validator.validate_expressions(constraints, available_vars)

        assert len(errors) == 2

    def test_validate_empty_constraints(self, validator: ConstraintValidator) -> None:
        """Test validating empty constraints."""
        errors = validator.validate_expressions({}, {"a", "b"})
        assert errors == []


class TestConstraintValidatorEdgeCases:
    """Edge case tests for ConstraintValidator."""

    def test_negative_constraint_values(self) -> None:
        """Test constraints with negative values."""
        validator = ConstraintValidator()
        constraints = {"a": {"min": -10, "max": -5}}
        variables = {"a": -7}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_floating_point_constraints(self) -> None:
        """Test constraints with floating point values."""
        validator = ConstraintValidator()
        constraints = {"a": {"min": 0.5, "max": 1.5}}
        variables = {"a": 1.0}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_very_large_numbers(self) -> None:
        """Test constraints with very large numbers."""
        validator = ConstraintValidator()
        constraints = {"a * b": {"min": 0, "max": 1e100}}
        variables = {"a": 1e50, "b": 1e49}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_zero_constraints(self) -> None:
        """Test constraints involving zero."""
        validator = ConstraintValidator()
        constraints = {"a": {"min": 0, "max": 0}}
        variables = {"a": 0}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_single_attempt_validator(self) -> None:
        """Test validator with single attempt."""
        validator = ConstraintValidator(max_attempts=1)
        constraints = {"a": {"min": 100, "max": 200}}
        initial = {"a": 5}

        def regenerate() -> dict:
            return {"a": 150}

        result = validator.apply(constraints, initial, regenerate)

        assert result["a"] == 150

    def test_constraint_with_modulo(self) -> None:
        """Test constraint with modulo operation."""
        validator = ConstraintValidator()
        constraints = {"a % 5": {"min": 0, "max": 0}}  # Must be divisible by 5
        variables = {"a": 10}

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True

    def test_constraint_with_power(self) -> None:
        """Test constraint with power operation."""
        validator = ConstraintValidator()
        constraints = {"a ** 2": {"min": 0, "max": 100}}
        variables = {"a": 5}  # 5^2 = 25

        satisfied, violated = validator.check(constraints, variables)

        assert satisfied is True
