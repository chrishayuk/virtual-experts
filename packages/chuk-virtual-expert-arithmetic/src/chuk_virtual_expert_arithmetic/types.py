"""Type definitions and constants for arithmetic experts.

This module provides the canonical source of truth for expert type identifiers
and other shared constants used throughout the package.
"""

from enum import StrEnum


class ExpertType(StrEnum):
    """Expert type identifiers for arithmetic problem domains.

    These values are used to route problems to the appropriate expert
    and to categorize generated examples.

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import ExpertType
        >>> expert = ExpertType.ARITHMETIC
        >>> expert == "arithmetic"  # StrEnum allows direct comparison
        True
    """

    ENTITY_TRACK = "entity_track"
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    PERCENTAGE = "percentage"
    RATE_EQUATION = "rate_equation"


# Convenience list of all expert directory names (for schema loading)
EXPERT_DIRS: list[str] = [e.value for e in ExpertType]

# Default expert type when not specified in schema
DEFAULT_EXPERT = ExpertType.ARITHMETIC
