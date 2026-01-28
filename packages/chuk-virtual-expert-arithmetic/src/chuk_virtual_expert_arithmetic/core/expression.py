"""Safe expression evaluator using AST parsing.

Replaces eval() with a secure, whitelist-based expression evaluator
that only allows arithmetic operations on known variables.

Usage:
    evaluator = SafeEvaluator()
    result = evaluator.evaluate("a + b * 2", {"a": 10, "b": 5})
    # result = 20
"""

from __future__ import annotations

import ast
import operator
from typing import Any


class ExpressionError(Exception):
    """Raised when expression evaluation fails."""

    pass


class SafeEvaluator:
    """Evaluate arithmetic expressions safely without eval().

    Supports:
    - Basic arithmetic: +, -, *, /, //, %, **
    - Unary minus: -x
    - Parentheses for grouping
    - Variable references from provided context
    - Numeric literals (int, float)

    Does NOT support:
    - Function calls
    - Attribute access
    - List/dict operations
    - String operations
    - Any imports or builtins

    Note on division behavior:
        The `/` operator (true division) always returns a float, even for
        integer operands. For example: 10 / 2 returns 5.0, not 5.

        Use `//` (floor division) for integer division: 10 // 2 returns 5.

        If you need integer results from true division, convert the result:
            result = int(evaluator.evaluate("a / b", context))
    """

    # Mapping of AST node types to operators
    BINARY_OPS: dict[type, Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    UNARY_OPS: dict[type, Any] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    COMPARE_OPS: dict[type, Any] = {
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
    }

    def __init__(self, allow_comparisons: bool = True) -> None:
        """Initialize the evaluator.

        Args:
            allow_comparisons: Whether to allow comparison operators (<, >, ==, etc.)
        """
        self._allow_comparisons = allow_comparisons

    def evaluate(self, expr: str, context: dict[str, Any] | None = None) -> float | int | bool:
        """Safely evaluate an arithmetic expression.

        Args:
            expr: The expression to evaluate (e.g., "a + b * 2")
            context: Variable bindings (e.g., {"a": 10, "b": 5})

        Returns:
            The result of the expression

        Raises:
            ExpressionError: If the expression is invalid or uses unsupported operations
        """
        if context is None:
            context = {}

        try:
            tree = ast.parse(expr.strip(), mode="eval")
            result: float | int | bool = self._eval_node(tree.body, context)
            return result
        except SyntaxError as e:
            raise ExpressionError(f"Invalid expression syntax: {expr}") from e
        except ExpressionError:
            raise
        except Exception as e:
            raise ExpressionError(f"Error evaluating expression '{expr}': {e}") from e

    def _eval_node(self, node: ast.AST, context: dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        # Numeric literals
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, bool)):
                return node.value
            raise ExpressionError(f"Unsupported constant type: {type(node.value)}")

        # Variable references
        if isinstance(node, ast.Name):
            name = node.id
            if name not in context:
                raise ExpressionError(f"Unknown variable: {name}")
            return context[name]

        # Binary operations (+, -, *, /, etc.)
        if isinstance(node, ast.BinOp):
            bin_op_type = type(node.op)
            if bin_op_type not in self.BINARY_OPS:
                raise ExpressionError(f"Unsupported binary operator: {bin_op_type.__name__}")

            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_func = self.BINARY_OPS[bin_op_type]

            try:
                return op_func(left, right)
            except ZeroDivisionError as e:
                raise ExpressionError("Division by zero") from e

        # Unary operations (-, +)
        if isinstance(node, ast.UnaryOp):
            unary_op_type = type(node.op)
            if unary_op_type not in self.UNARY_OPS:
                raise ExpressionError(f"Unsupported unary operator: {unary_op_type.__name__}")

            operand = self._eval_node(node.operand, context)
            return self.UNARY_OPS[unary_op_type](operand)

        # Comparisons (<, >, ==, etc.)
        if isinstance(node, ast.Compare):
            if not self._allow_comparisons:
                raise ExpressionError("Comparisons not allowed")

            left = self._eval_node(node.left, context)
            result = True

            for op, comparator in zip(node.ops, node.comparators, strict=True):
                cmp_op_type = type(op)
                if cmp_op_type not in self.COMPARE_OPS:
                    raise ExpressionError(f"Unsupported comparison: {cmp_op_type.__name__}")

                right = self._eval_node(comparator, context)
                if not self.COMPARE_OPS[cmp_op_type](left, right):
                    result = False
                    break
                left = right

            return result

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self._eval_node(v, context) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(self._eval_node(v, context) for v in node.values)
            else:
                raise ExpressionError(f"Unsupported boolean operator: {type(node.op).__name__}")

        # Parenthesized expressions (handled automatically by BinOp)
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body, context)

        # Anything else is not allowed
        raise ExpressionError(f"Unsupported expression type: {type(node).__name__}")

    def validate(self, expr: str, available_vars: set[str] | None = None) -> list[str]:
        """Validate an expression without evaluating it.

        Args:
            expr: The expression to validate
            available_vars: Set of variable names that should be available

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []

        try:
            tree = ast.parse(expr.strip(), mode="eval")
            referenced_vars = self._extract_variables(tree.body)

            if available_vars is not None:
                unknown = referenced_vars - available_vars
                if unknown:
                    errors.append(f"Unknown variables: {', '.join(sorted(unknown))}")

        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg}")

        return errors

    def _extract_variables(self, node: ast.AST) -> set[str]:
        """Extract all variable names referenced in an expression."""
        variables: set[str] = set()

        if isinstance(node, ast.Name):
            variables.add(node.id)
        elif isinstance(node, ast.BinOp):
            variables.update(self._extract_variables(node.left))
            variables.update(self._extract_variables(node.right))
        elif isinstance(node, ast.UnaryOp):
            variables.update(self._extract_variables(node.operand))
        elif isinstance(node, ast.Compare):
            variables.update(self._extract_variables(node.left))
            for comp in node.comparators:
                variables.update(self._extract_variables(comp))
        elif isinstance(node, ast.BoolOp):
            for value in node.values:
                variables.update(self._extract_variables(value))

        return variables


# Module-level convenience instance
_default_evaluator: SafeEvaluator | None = None


def get_evaluator() -> SafeEvaluator:
    """Get the default evaluator instance."""
    global _default_evaluator
    if _default_evaluator is None:
        _default_evaluator = SafeEvaluator()
    return _default_evaluator


def safe_eval(expr: str, context: dict[str, Any] | None = None) -> float | int | bool:
    """Convenience function for safe expression evaluation.

    Args:
        expr: The expression to evaluate
        context: Variable bindings

    Returns:
        The result of the expression
    """
    return get_evaluator().evaluate(expr, context)
