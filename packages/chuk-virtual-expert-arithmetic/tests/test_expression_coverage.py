"""Additional tests for SafeEvaluator - comprehensive coverage."""

from __future__ import annotations

import pytest

from chuk_virtual_expert_arithmetic.core.expression import (
    ExpressionError,
    SafeEvaluator,
    get_evaluator,
    safe_eval,
)


class TestSafeEvaluatorBasics:
    """Basic tests for SafeEvaluator."""

    def test_simple_addition(self) -> None:
        """Test simple addition."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("1 + 2")
        assert result == 3

    def test_empty_context(self) -> None:
        """Test with empty context (None)."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("5 + 3", None)
        assert result == 8

    def test_all_binary_ops(self) -> None:
        """Test all binary operators."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("10 + 5") == 15
        assert evaluator.evaluate("10 - 5") == 5
        assert evaluator.evaluate("10 * 5") == 50
        assert evaluator.evaluate("10 / 5") == 2.0
        assert evaluator.evaluate("10 // 3") == 3
        assert evaluator.evaluate("10 % 3") == 1
        assert evaluator.evaluate("2 ** 3") == 8


class TestSafeEvaluatorUnary:
    """Tests for unary operators."""

    def test_unary_minus(self) -> None:
        """Test unary minus."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("-5")
        assert result == -5

    def test_unary_plus(self) -> None:
        """Test unary plus."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("+5")
        assert result == 5

    def test_unary_in_expression(self) -> None:
        """Test unary in complex expression."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("10 + -3")
        assert result == 7


class TestSafeEvaluatorComparisons:
    """Tests for comparison operators."""

    def test_less_than(self) -> None:
        """Test less than."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("3 < 5") is True
        assert evaluator.evaluate("5 < 3") is False

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("3 <= 5") is True
        assert evaluator.evaluate("5 <= 5") is True
        assert evaluator.evaluate("6 <= 5") is False

    def test_greater_than(self) -> None:
        """Test greater than."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("5 > 3") is True
        assert evaluator.evaluate("3 > 5") is False

    def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("5 >= 3") is True
        assert evaluator.evaluate("5 >= 5") is True
        assert evaluator.evaluate("4 >= 5") is False

    def test_equal(self) -> None:
        """Test equality."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("5 == 5") is True
        assert evaluator.evaluate("5 == 3") is False

    def test_not_equal(self) -> None:
        """Test not equal."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("5 != 3") is True
        assert evaluator.evaluate("5 != 5") is False

    def test_comparisons_disabled(self) -> None:
        """Test comparisons when disabled."""
        evaluator = SafeEvaluator(allow_comparisons=False)
        with pytest.raises(ExpressionError, match="Comparisons not allowed"):
            evaluator.evaluate("5 < 10")

    def test_chained_comparison(self) -> None:
        """Test chained comparison like 1 < 2 < 3."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("1 < 2 < 3") is True
        assert evaluator.evaluate("1 < 3 < 2") is False

    def test_chained_comparison_with_variables(self) -> None:
        """Test chained comparison with variables."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("a < b < c", {"a": 1, "b": 2, "c": 3}) is True
        assert evaluator.evaluate("a < b < c", {"a": 1, "b": 5, "c": 3}) is False


class TestSafeEvaluatorBoolOps:
    """Tests for boolean operators."""

    def test_and_operator(self) -> None:
        """Test and operator."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("True and True") is True
        assert evaluator.evaluate("True and False") is False
        assert evaluator.evaluate("False and True") is False

    def test_or_operator(self) -> None:
        """Test or operator."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("True or False") is True
        assert evaluator.evaluate("False or True") is True
        assert evaluator.evaluate("False or False") is False

    def test_combined_bool_ops(self) -> None:
        """Test combined boolean operations."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("True and True or False") is True
        assert evaluator.evaluate("False or True and True") is True


class TestSafeEvaluatorErrors:
    """Tests for error handling."""

    def test_syntax_error(self) -> None:
        """Test syntax error handling."""
        evaluator = SafeEvaluator()
        with pytest.raises(ExpressionError, match="Invalid expression syntax"):
            evaluator.evaluate("1 +")

    def test_unknown_variable(self) -> None:
        """Test unknown variable error."""
        evaluator = SafeEvaluator()
        with pytest.raises(ExpressionError, match="Unknown variable"):
            evaluator.evaluate("x + 1")

    def test_division_by_zero(self) -> None:
        """Test division by zero error."""
        evaluator = SafeEvaluator()
        with pytest.raises(ExpressionError, match="Division by zero"):
            evaluator.evaluate("10 / 0")

    def test_unsupported_constant_type(self) -> None:
        """Test unsupported constant type error."""
        evaluator = SafeEvaluator()
        with pytest.raises(ExpressionError, match="Unsupported constant type"):
            evaluator.evaluate("'string'")

    def test_unsupported_expression_type(self) -> None:
        """Test unsupported expression type error."""
        evaluator = SafeEvaluator()
        # Function calls are not supported
        with pytest.raises(ExpressionError, match="Unsupported expression type"):
            evaluator.evaluate("print(5)")

    def test_unsupported_expression_attribute(self) -> None:
        """Test unsupported expression type for attribute access."""
        evaluator = SafeEvaluator()
        with pytest.raises(ExpressionError, match="Unsupported expression type"):
            evaluator.evaluate("x.attr", {"x": 5})

    def test_generic_exception_handling(self) -> None:
        """Test generic exception handling."""
        evaluator = SafeEvaluator()
        # Create a scenario that raises an unexpected error
        # This is difficult to trigger, but we can test the re-raise of ExpressionError
        with pytest.raises(ExpressionError):
            evaluator.evaluate("[][0]")  # List subscript not supported


class TestSafeEvaluatorValidate:
    """Tests for validate method."""

    def test_valid_expression(self) -> None:
        """Test valid expression validation."""
        evaluator = SafeEvaluator()
        errors = evaluator.validate("a + b")
        assert errors == []

    def test_valid_expression_with_known_vars(self) -> None:
        """Test validation with known variables."""
        evaluator = SafeEvaluator()
        errors = evaluator.validate("a + b", {"a", "b"})
        assert errors == []

    def test_unknown_variables(self) -> None:
        """Test validation with unknown variables."""
        evaluator = SafeEvaluator()
        errors = evaluator.validate("x + y", {"a", "b"})
        assert len(errors) == 1
        assert "Unknown variables" in errors[0]
        assert "x" in errors[0]
        assert "y" in errors[0]

    def test_syntax_error_in_validation(self) -> None:
        """Test syntax error in validation."""
        evaluator = SafeEvaluator()
        # Use an actual syntax error - unclosed parenthesis
        errors = evaluator.validate("(1 + 2")
        assert len(errors) == 1
        assert "Syntax error" in errors[0]

    def test_validate_complex_expression(self) -> None:
        """Test validation of complex expression."""
        evaluator = SafeEvaluator()
        errors = evaluator.validate("a * b + c - d", {"a", "b", "c", "d"})
        assert errors == []

    def test_validate_comparison(self) -> None:
        """Test validation of comparison expression."""
        evaluator = SafeEvaluator()
        errors = evaluator.validate("a < b", {"a", "b"})
        assert errors == []


class TestExtractVariables:
    """Tests for _extract_variables method."""

    def test_extract_from_name(self) -> None:
        """Test extracting variable from Name node."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("x", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == {"x"}

    def test_extract_from_binop(self) -> None:
        """Test extracting variables from BinOp."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("a + b", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == {"a", "b"}

    def test_extract_from_unaryop(self) -> None:
        """Test extracting variables from UnaryOp."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("-x", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == {"x"}

    def test_extract_from_compare(self) -> None:
        """Test extracting variables from Compare."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("a < b < c", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == {"a", "b", "c"}

    def test_extract_from_boolop(self) -> None:
        """Test extracting variables from BoolOp."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("a and b or c", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == {"a", "b", "c"}

    def test_extract_from_constant(self) -> None:
        """Test extracting from constant (returns empty)."""
        evaluator = SafeEvaluator()
        import ast

        node = ast.parse("5", mode="eval").body
        vars = evaluator._extract_variables(node)
        assert vars == set()


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_evaluator_singleton(self) -> None:
        """Test get_evaluator returns singleton."""
        evaluator1 = get_evaluator()
        evaluator2 = get_evaluator()
        assert evaluator1 is evaluator2

    def test_safe_eval(self) -> None:
        """Test safe_eval convenience function."""
        result = safe_eval("10 + 5")
        assert result == 15

    def test_safe_eval_with_context(self) -> None:
        """Test safe_eval with context."""
        result = safe_eval("a * b", {"a": 3, "b": 4})
        assert result == 12


class TestConstantTypes:
    """Tests for constant type handling."""

    def test_int_constant(self) -> None:
        """Test integer constant."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("42") == 42

    def test_float_constant(self) -> None:
        """Test float constant."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("3.14") == 3.14

    def test_bool_constant_true(self) -> None:
        """Test boolean constant True."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("True") is True

    def test_bool_constant_false(self) -> None:
        """Test boolean constant False."""
        evaluator = SafeEvaluator()
        assert evaluator.evaluate("False") is False


class TestParentheses:
    """Tests for parentheses handling."""

    def test_simple_parentheses(self) -> None:
        """Test simple parentheses."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("(1 + 2) * 3")
        assert result == 9

    def test_nested_parentheses(self) -> None:
        """Test nested parentheses."""
        evaluator = SafeEvaluator()
        result = evaluator.evaluate("((1 + 2) * 3) + 4")
        assert result == 13
