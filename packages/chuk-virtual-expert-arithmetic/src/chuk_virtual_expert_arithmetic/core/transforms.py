"""Pluggable transform registry for template variable transformations.

Transforms are applied to values using pipe syntax: "item|pluralize"

Usage:
    # Register a custom transform
    TransformRegistry.register("uppercase", str.upper)

    # Apply transforms
    result = TransformRegistry.apply("apple", "pluralize")  # "apples"
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

TransformFn = Callable[[Any], Any]


class TransformError(Exception):
    """Raised when transform application fails."""

    pass


class TransformRegistry:
    """Registry for value transformation functions.

    Provides a pluggable system for extending value transformations
    without modifying the core generator.
    """

    _transforms: dict[str, TransformFn] = {}

    @classmethod
    def register(cls, name: str, fn: TransformFn) -> None:
        """Register a new transform.

        Args:
            name: Transform name (used in pipe syntax)
            fn: Transform function
        """
        cls._transforms[name] = fn

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a transform.

        Args:
            name: Transform name to remove
        """
        cls._transforms.pop(name, None)

    @classmethod
    def apply(cls, value: Any, transform: str) -> Any:
        """Apply a transform to a value.

        Args:
            value: Value to transform
            transform: Transform name

        Returns:
            Transformed value

        Raises:
            TransformError: If transform not found
        """
        if transform not in cls._transforms:
            raise TransformError(f"Unknown transform: {transform}")

        try:
            return cls._transforms[transform](value)
        except Exception as e:
            raise TransformError(f"Transform '{transform}' failed: {e}") from e

    @classmethod
    def apply_chain(cls, value: Any, transforms: list[str]) -> Any:
        """Apply a chain of transforms to a value.

        Args:
            value: Initial value
            transforms: List of transform names

        Returns:
            Final transformed value
        """
        for transform in transforms:
            value = cls.apply(value, transform)
        return value

    @classmethod
    def get_all(cls) -> dict[str, TransformFn]:
        """Get all registered transforms."""
        return dict(cls._transforms)

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a transform is registered."""
        return name in cls._transforms

    @classmethod
    def clear(cls) -> None:
        """Clear all registered transforms."""
        cls._transforms.clear()


# Built-in transform functions


def pluralize(word: str | Any) -> str:
    """Pluralize a word correctly."""
    s = str(word)
    if s.endswith(("s", "x", "ch", "sh")):
        return s + "es"
    elif s.endswith("y") and len(s) > 1 and s[-2] not in "aeiou":
        return s[:-1] + "ies"
    else:
        return s + "s"


def singularize(word: str | Any) -> str:
    """Singularize a word (best effort)."""
    s = str(word)
    if s.endswith("ies"):
        return s[:-3] + "y"
    elif s.endswith("es") and len(s) > 2 and s[-3] in "sxh":
        return s[:-2]
    elif s.endswith("s") and not s.endswith("ss"):
        return s[:-1]
    return s


def capitalize(value: Any) -> str:
    """Capitalize the first letter."""
    return str(value).capitalize()


def lower(value: Any) -> str:
    """Convert to lowercase."""
    return str(value).lower()


def upper(value: Any) -> str:
    """Convert to uppercase."""
    return str(value).upper()


def with_article(word: str | Any) -> str:
    """Add article (a/an) to a word."""
    s = str(word)
    if not s:
        return s
    vowels = "aeiouAEIOU"
    article = "an" if s[0] in vowels else "a"
    return f"{article} {s}"


def has_have(value: Any) -> str:
    """Return 'has' for singular, 'have' for plural."""
    return "has" if value == "s" else "have"


def does_do(value: Any) -> str:
    """Return 'does' for singular, 'do' for plural."""
    return "does" if value == "s" else "do"


def ordinal(n: Any) -> str:
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)."""
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)

    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

    return f"{n}{suffix}"


# Register built-in transforms
def _register_builtins() -> None:
    """Register all built-in transforms."""
    TransformRegistry.register("pluralize", pluralize)
    TransformRegistry.register("singularize", singularize)
    TransformRegistry.register("capitalize", capitalize)
    TransformRegistry.register("lower", lower)
    TransformRegistry.register("upper", upper)
    TransformRegistry.register("with_article", with_article)
    TransformRegistry.register("has_have", has_have)
    TransformRegistry.register("does_do", does_do)
    TransformRegistry.register("ordinal", ordinal)


# Auto-register on import
_register_builtins()
