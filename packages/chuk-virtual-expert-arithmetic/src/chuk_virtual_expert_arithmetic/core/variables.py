"""Variable generation from schema specifications.

Generates random values for problem variables based on type and constraints.

Usage:
    generator = VariableGenerator()
    variables = generator.generate(schema.variables)
"""

from __future__ import annotations

import logging
import random
from typing import Any

from chuk_virtual_expert_arithmetic.models.schema_spec import VariableSpec

logger = logging.getLogger(__name__)


class VariableGenerator:
    """Generates random values for problem variables.

    Supports:
    - Integer ranges with optional multiple_of constraint
    - Float ranges with precision
    - Boolean values
    - Choice from list of options
    - Difficulty-based generation (easy/medium/hard)
    - Numeric diversity (avoid_round numbers)
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._rng = random.Random(seed)
        self._seed = seed

    def generate(self, specs: dict[str, VariableSpec]) -> dict[str, Any]:
        """Generate values for all variables.

        Args:
            specs: Dict of variable name -> VariableSpec

        Returns:
            Dict of variable name -> generated value
        """
        variables = {}
        for name, spec in specs.items():
            variables[name] = self.generate_one(spec)
        return variables

    def generate_one(self, spec: VariableSpec) -> Any:
        """Generate a single variable value.

        Args:
            spec: Variable specification

        Returns:
            Generated value
        """
        if spec.type == "int":
            return self._generate_int(spec)
        elif spec.type == "float":
            return self._generate_float(spec)
        elif spec.type == "bool":
            return self._rng.choice([True, False])
        elif spec.type == "choice":
            return self._generate_choice(spec)
        else:
            # Default to int
            return self._generate_int(spec)

    def _generate_int(self, spec: VariableSpec) -> int:
        """Generate an integer value.

        Supports:
        - Basic range (min/max)
        - multiple_of constraint
        - avoid_round: avoids multiples of 10
        - difficulty: easy/medium/hard profiles
        """
        min_val = int(spec.min) if spec.min is not None else 1
        max_val = int(spec.max) if spec.max is not None else 100

        # Handle difficulty-based generation
        if spec.difficulty:
            value = self._generate_by_difficulty(spec.difficulty, min_val, max_val)
        # Handle avoid_round constraint
        elif spec.avoid_round:
            value = self._generate_non_round(min_val, max_val)
        else:
            value = self._rng.randint(min_val, max_val)

        # Handle multiple_of constraint
        if spec.multiple_of:
            mult = spec.multiple_of
            value = (value // mult) * mult
            if value < min_val:
                value += mult

        return value

    def _generate_non_round(self, min_val: int, max_val: int, attempts: int = 10) -> int:
        """Generate a number that's not a multiple of 10.

        Args:
            min_val: Minimum value
            max_val: Maximum value
            attempts: Max attempts before fallback

        Returns:
            A non-round number
        """
        for _ in range(attempts):
            value = self._rng.randint(min_val, max_val)
            if value % 10 != 0:
                return value

        # Fallback: adjust if we got a round number
        value = self._rng.randint(min_val, max_val)
        if value % 10 == 0:
            adjustment = self._rng.randint(1, 9)
            value = min(value + adjustment, max_val)
            if value % 10 == 0:  # Still round after adjustment
                value = max(value - 1, min_val)
        return value

    def _generate_by_difficulty(self, difficulty: str, min_val: int, max_val: int) -> int:
        """Generate a number based on difficulty level.

        Args:
            difficulty: "easy", "medium", or "hard"
            min_val: Base minimum
            max_val: Base maximum

        Returns:
            Generated number appropriate for difficulty
        """
        if difficulty == "easy":
            # Small, often round numbers (multiples of 5)
            easy_options = [5, 10, 15, 20, 25, 30]
            valid_options = [v for v in easy_options if min_val <= v <= max_val]
            if valid_options:
                return self._rng.choice(valid_options)
            # Fallback to min/max range with preference for round
            value = self._rng.randint(min_val, max_val)
            return (value // 5) * 5 or value

        elif difficulty == "hard":
            # Larger, non-round numbers
            hard_min = max(min_val, 50)
            hard_max = max(max_val, 200)
            return self._generate_non_round(hard_min, hard_max)

        else:  # medium (default)
            return self._rng.randint(min_val, max_val)

    def _generate_float(self, spec: VariableSpec) -> float:
        """Generate a float value."""
        min_val = float(spec.min) if spec.min is not None else 0.0
        max_val = float(spec.max) if spec.max is not None else 10.0
        precision = spec.precision if spec.precision is not None else 2

        value = self._rng.uniform(min_val, max_val)
        return round(value, precision)

    def _generate_choice(self, spec: VariableSpec) -> Any:
        """Generate a choice value."""
        # Support both "options" and "values" for choice type
        options = spec.options or spec.values or []
        if not options:
            return 0
        return self._rng.choice(options)

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator.

        Args:
            seed: New seed value, or None for random
        """
        self._rng = random.Random(seed)


class DifficultyProfile:
    """Configuration for difficulty-based number generation.

    Defines characteristics of numbers at each difficulty level:
    - EASY: Small numbers, multiples of 5, no decimals
    - MEDIUM: Standard range, any numbers
    - HARD: Larger numbers, avoid round numbers, may require regrouping
    """

    EASY = {
        "max_digits": 2,
        "prefer_round": True,
        "avoid_decimals": True,
        "typical_range": (5, 30),
    }

    MEDIUM = {
        "max_digits": 3,
        "prefer_round": False,
        "allow_decimals": True,
        "typical_range": (1, 100),
    }

    HARD = {
        "max_digits": 4,
        "avoid_round": True,
        "allow_decimals": True,
        "typical_range": (50, 200),
    }

    @classmethod
    def get(cls, difficulty: str) -> dict[str, Any]:
        """Get the profile for a difficulty level."""
        profiles = {
            "easy": cls.EASY,
            "medium": cls.MEDIUM,
            "hard": cls.HARD,
        }
        return profiles.get(difficulty, cls.MEDIUM)
