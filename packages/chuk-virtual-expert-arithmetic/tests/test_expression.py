"""Tests for safe expression evaluator."""

import pytest

from chuk_virtual_expert_arithmetic.core.expression import (
    ExpressionError,
    SafeEvaluator,
    get_evaluator,
    safe_eval,
)


class TestSafeEvaluator:
    """Tests for SafeEvaluator class."""

    @pytest.fixture
    def evaluator(self) -> SafeEvaluator:
        """Create an evaluator instance."""
        return SafeEvaluator()

    # Basic arithmetic tests
    def test_addition(self, evaluator: SafeEvaluator) -> None:
        """Test basic addition."""
        assert evaluator.evaluate("1 + 2") == 3
        assert evaluator.evaluate("a + b", {"a": 10, "b": 5}) == 15

    def test_subtraction(self, evaluator: SafeEvaluator) -> None:
        """Test basic subtraction."""
        assert evaluator.evaluate("5 - 3") == 2
        assert evaluator.evaluate("a - b", {"a": 10, "b": 3}) == 7

    def test_multiplication(self, evaluator: SafeEvaluator) -> None:
        """Test basic multiplication."""
        assert evaluator.evaluate("2 * 3") == 6
        assert evaluator.evaluate("a * b", {"a": 4, "b": 5}) == 20

    def test_division(self, evaluator: SafeEvaluator) -> None:
        """Test basic division."""
        assert evaluator.evaluate("10 / 2") == 5.0
        assert evaluator.evaluate("a / b", {"a": 15, "b": 3}) == 5.0

    def test_floor_division(self, evaluator: SafeEvaluator) -> None:
        """Test floor division."""
        assert evaluator.evaluate("7 // 2") == 3
        assert evaluator.evaluate("a // b", {"a": 10, "b": 3}) == 3

    def test_modulo(self, evaluator: SafeEvaluator) -> None:
        """Test modulo operator."""
        assert evaluator.evaluate("7 % 3") == 1
        assert evaluator.evaluate("a % b", {"a": 10, "b": 4}) == 2

    def test_power(self, evaluator: SafeEvaluator) -> None:
        """Test exponentiation."""
        assert evaluator.evaluate("2 ** 3") == 8
        assert evaluator.evaluate("a ** b", {"a": 3, "b": 2}) == 9

    def test_unary_minus(self, evaluator: SafeEvaluator) -> None:
        """Test unary minus."""
        assert evaluator.evaluate("-5") == -5
        assert evaluator.evaluate("-a", {"a": 10}) == -10
        assert evaluator.evaluate("a + -b", {"a": 10, "b": 3}) == 7

    def test_unary_plus(self, evaluator: SafeEvaluator) -> None:
        """Test unary plus."""
        assert evaluator.evaluate("+5") == 5
        assert evaluator.evaluate("+a", {"a": 10}) == 10

    # Complex expressions
    def test_complex_expression(self, evaluator: SafeEvaluator) -> None:
        """Test complex arithmetic expressions."""
        assert evaluator.evaluate("a + b * c", {"a": 1, "b": 2, "c": 3}) == 7
        assert evaluator.evaluate("(a + b) * c", {"a": 1, "b": 2, "c": 3}) == 9
        assert evaluator.evaluate("a * b - c / d", {"a": 10, "b": 2, "c": 6, "d": 3}) == 18.0

    def test_nested_parentheses(self, evaluator: SafeEvaluator) -> None:
        """Test nested parentheses."""
        assert evaluator.evaluate("((a + b) * c) - d", {"a": 1, "b": 2, "c": 3, "d": 4}) == 5

    def test_float_values(self, evaluator: SafeEvaluator) -> None:
        """Test with float values."""
        assert evaluator.evaluate("a + b", {"a": 1.5, "b": 2.5}) == 4.0
        assert evaluator.evaluate("0.25 * 4") == 1.0

    # Comparison operations
    def test_less_than(self, evaluator: SafeEvaluator) -> None:
        """Test less than comparison."""
        assert evaluator.evaluate("a < b", {"a": 1, "b": 2}) is True
        assert evaluator.evaluate("a < b", {"a": 2, "b": 1}) is False

    def test_greater_than(self, evaluator: SafeEvaluator) -> None:
        """Test greater than comparison."""
        assert evaluator.evaluate("a > b", {"a": 5, "b": 3}) is True
        assert evaluator.evaluate("a > b", {"a": 1, "b": 3}) is False

    def test_equality(self, evaluator: SafeEvaluator) -> None:
        """Test equality comparison."""
        assert evaluator.evaluate("a == b", {"a": 5, "b": 5}) is True
        assert evaluator.evaluate("a == b", {"a": 5, "b": 3}) is False

    def test_not_equal(self, evaluator: SafeEvaluator) -> None:
        """Test not equal comparison."""
        assert evaluator.evaluate("a != b", {"a": 5, "b": 3}) is True
        assert evaluator.evaluate("a != b", {"a": 5, "b": 5}) is False

    def test_comparisons_disabled(self) -> None:
        """Test that comparisons can be disabled."""
        evaluator = SafeEvaluator(allow_comparisons=False)
        with pytest.raises(ExpressionError, match="Comparisons not allowed"):
            evaluator.evaluate("a < b", {"a": 1, "b": 2})

    # Boolean operations
    def test_boolean_and(self, evaluator: SafeEvaluator) -> None:
        """Test boolean AND."""
        assert evaluator.evaluate("a > 0 and b > 0", {"a": 1, "b": 2}) is True
        assert evaluator.evaluate("a > 0 and b > 0", {"a": 1, "b": -1}) is False

    def test_boolean_or(self, evaluator: SafeEvaluator) -> None:
        """Test boolean OR."""
        assert evaluator.evaluate("a > 0 or b > 0", {"a": -1, "b": 2}) is True
        assert evaluator.evaluate("a > 0 or b > 0", {"a": -1, "b": -1}) is False

    # Error handling
    def test_unknown_variable(self, evaluator: SafeEvaluator) -> None:
        """Test error on unknown variable."""
        with pytest.raises(ExpressionError, match="Unknown variable: x"):
            evaluator.evaluate("x + 1")

    def test_division_by_zero(self, evaluator: SafeEvaluator) -> None:
        """Test division by zero error."""
        with pytest.raises(ExpressionError, match="Division by zero"):
            evaluator.evaluate("a / 0", {"a": 10})

    def test_syntax_error(self, evaluator: SafeEvaluator) -> None:
        """Test syntax error handling."""
        with pytest.raises(ExpressionError, match="Invalid expression syntax"):
            evaluator.evaluate("a + * b", {"a": 1, "b": 2})

    def test_unsupported_function_call(self, evaluator: SafeEvaluator) -> None:
        """Test that function calls are blocked."""
        with pytest.raises(ExpressionError, match="Unsupported expression type"):
            evaluator.evaluate("print(a)", {"a": 1})

    def test_unsupported_attribute_access(self, evaluator: SafeEvaluator) -> None:
        """Test that attribute access is blocked."""
        with pytest.raises(ExpressionError, match="Unsupported expression type"):
            evaluator.evaluate("a.b", {"a": {"b": 1}})

    def test_unsupported_list_index(self, evaluator: SafeEvaluator) -> None:
        """Test that list indexing is blocked."""
        with pytest.raises(ExpressionError, match="Unsupported expression type"):
            evaluator.evaluate("a[0]", {"a": [1, 2, 3]})

    # Validation
    def test_validate_valid_expression(self, evaluator: SafeEvaluator) -> None:
        """Test validation of valid expression."""
        errors = evaluator.validate("a + b * c", {"a", "b", "c"})
        assert errors == []

    def test_validate_unknown_variable(self, evaluator: SafeEvaluator) -> None:
        """Test validation catches unknown variables."""
        errors = evaluator.validate("a + x", {"a", "b", "c"})
        assert len(errors) == 1
        assert "Unknown variables: x" in errors[0]

    def test_validate_syntax_error(self, evaluator: SafeEvaluator) -> None:
        """Test validation catches syntax errors."""
        errors = evaluator.validate("a + * b")
        assert len(errors) == 1
        assert "Syntax error" in errors[0]

    def test_validate_multiple_unknown(self, evaluator: SafeEvaluator) -> None:
        """Test validation lists all unknown variables."""
        errors = evaluator.validate("x + y + z", {"a"})
        assert len(errors) == 1
        assert "x" in errors[0] and "y" in errors[0] and "z" in errors[0]


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_evaluator(self) -> None:
        """Test getting default evaluator."""
        evaluator = get_evaluator()
        assert isinstance(evaluator, SafeEvaluator)

        # Should return same instance
        evaluator2 = get_evaluator()
        assert evaluator is evaluator2

    def test_safe_eval(self) -> None:
        """Test safe_eval convenience function."""
        result = safe_eval("a + b", {"a": 10, "b": 5})
        assert result == 15

    def test_safe_eval_no_context(self) -> None:
        """Test safe_eval with literals only."""
        result = safe_eval("2 + 3 * 4")
        assert result == 14


class TestRealWorldExpressions:
    """Test expressions from actual schemas."""

    @pytest.fixture
    def evaluator(self) -> SafeEvaluator:
        """Create an evaluator instance."""
        return SafeEvaluator()

    def test_shopping_constraint(self, evaluator: SafeEvaluator) -> None:
        """Test shopping spree constraint expression."""
        expr = "start - cost1 - cost2 - cost3"
        context = {"start": 200, "cost1": 30, "cost2": 40, "cost3": 25}
        result = evaluator.evaluate(expr, context)
        assert result == 105

    def test_feed_remainder(self, evaluator: SafeEvaluator) -> None:
        """Test feed remainder constraint."""
        expr = "cups_per * count - morning - afternoon"
        context = {"cups_per": 3, "count": 20, "morning": 15, "afternoon": 20}
        result = evaluator.evaluate(expr, context)
        assert result == 25

    def test_derived_calculation(self, evaluator: SafeEvaluator) -> None:
        """Test derived variable calculation."""
        context = {"count": 10, "rate_decimal": 0.5}
        daily = evaluator.evaluate("count * rate_decimal", context)
        assert daily == 5.0

        context["daily"] = daily
        total = evaluator.evaluate("daily * days", {**context, "days": 7})
        assert total == 35.0

    def test_constraint_check(self, evaluator: SafeEvaluator) -> None:
        """Test constraint min/max check."""
        context = {"a": 10, "b": 5}
        value = evaluator.evaluate("a * b", context)
        min_val = 10
        max_val = 100
        assert min_val <= value <= max_val
