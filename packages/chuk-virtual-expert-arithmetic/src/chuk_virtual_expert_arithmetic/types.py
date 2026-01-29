"""Type definitions, enums, and constants for virtual experts.

This module provides the canonical source of truth for:
- Expert type identifiers
- Trace operation types
- Compute operation types
- Vocabulary spec types
- Common constants and paths

Design: All enums use StrEnum for JSON serialization compatibility and
direct string comparison. This module should have NO dependencies on
other package modules to avoid circular imports.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

# =============================================================================
# EXPERT TYPES
# =============================================================================


class ExpertType(StrEnum):
    """Expert type identifiers for problem domains.

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
EXPERT_DIRS: Final[list[str]] = [e.value for e in ExpertType]

# Default expert type when not specified in schema
DEFAULT_EXPERT: Final[ExpertType] = ExpertType.ARITHMETIC


# =============================================================================
# TRACE OPERATION TYPES
# =============================================================================


class TraceOpType(StrEnum):
    """Trace operation types for step-by-step problem solving.

    Core operations:
        INIT: Initialize a variable with a value
        COMPUTE: Perform a mathematical computation
        QUERY: Mark the final answer variable

    Entity tracking:
        TRANSFER: Transfer items between entities
        CONSUME: Consume/use items from an entity
        ADD_ENTITY: Add a new entity to track

    Percentage operations:
        PERCENT_OFF: Calculate discount (base - base * rate)
        PERCENT_INCREASE: Calculate increase (base + base * rate)
        PERCENT_OF: Calculate percentage (base * rate)

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import TraceOpType
        >>> op = TraceOpType.COMPUTE
        >>> op == "compute"
        True
    """

    # Core operations
    INIT = "init"
    COMPUTE = "compute"
    QUERY = "query"

    # Entity tracking operations
    TRANSFER = "transfer"
    CONSUME = "consume"
    ADD_ENTITY = "add_entity"

    # Percentage operations
    PERCENT_OFF = "percent_off"
    PERCENT_INCREASE = "percent_increase"
    PERCENT_OF = "percent_of"


# =============================================================================
# COMPUTE OPERATION TYPES
# =============================================================================


class ComputeOpType(StrEnum):
    """Mathematical operation types for COMPUTE trace steps.

    These map to standard Python operator module functions.

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import ComputeOpType
        >>> op = ComputeOpType.ADD
        >>> op == "add"
        True
    """

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    FLOORDIV = "floordiv"
    MOD = "mod"
    POW = "pow"


# =============================================================================
# VOCABULARY SPEC TYPES
# =============================================================================


class VocabSpecType(StrEnum):
    """Vocabulary specification types for sampling.

    PATH: Sample from a vocab path (e.g., "items.countable_singular")
    CHOICE: Random selection from inline values list
    PERSON_WITH_PRONOUNS: Generate person with matching pronouns
    DOMAIN_CONTEXT: Sample semantically coherent vocab from a domain

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import VocabSpecType
        >>> spec_type = VocabSpecType.PERSON_WITH_PRONOUNS
    """

    PATH = "path"
    CHOICE = "choice"
    PERSON_WITH_PRONOUNS = "person_with_pronouns"
    DOMAIN_CONTEXT = "domain_context"


# =============================================================================
# VARIABLE TYPES
# =============================================================================


class VariableType(StrEnum):
    """Variable types for schema variable specifications."""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CHOICE = "choice"


# =============================================================================
# DIFFICULTY LEVELS
# =============================================================================


class DifficultyLevel(StrEnum):
    """Difficulty levels for problem generation."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# =============================================================================
# TEMPLATE VARIABLE KEYS (Constants for common template vars)
# =============================================================================


class TemplateVar(StrEnum):
    """Common template variable keys used in problem templates.

    Person-related:
        NAME, SUBJECT, SUBJ, HIS_HER, HIM_HER, REFLEXIVE, VERB_S

    Multiplier-related:
        MULT_WORD, GROWTH_WORD

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import TemplateVar
        >>> key = TemplateVar.NAME
        >>> template_vars[key] = "Alice"
    """

    # Person-related
    NAME = "name"
    SUBJECT = "subject"
    SUBJ = "subj"
    HIS_HER = "his_her"
    HIM_HER = "him_her"
    REFLEXIVE = "reflexive"
    VERB_S = "verb_s"

    # Multiplier-related
    MULT_WORD = "mult_word"
    GROWTH_WORD = "growth_word"


# =============================================================================
# VOCAB PATHS (Constants for common vocab paths)
# =============================================================================


class VocabPath(StrEnum):
    """Common vocabulary paths for sampling.

    Example:
        >>> from chuk_virtual_expert_arithmetic.types import VocabPath
        >>> vocab.random(VocabPath.NAMES_MALE)
    """

    # Name paths
    NAMES_MALE = "names.male"
    NAMES_FEMALE = "names.female"
    NAMES_NEUTRAL = "names.neutral"
    NAMES_PRONOUNS_MALE = "names.pronouns.male"
    NAMES_PRONOUNS_FEMALE = "names.pronouns.female"
    NAMES_PRONOUNS_NEUTRAL = "names.pronouns.neutral"

    # Messy vocab paths (for GSM-8K style diversity)
    MESSY_NAMES_DIVERSE_MALE = "messy.names_unusual.diverse_male"
    MESSY_NAMES_DIVERSE_FEMALE = "messy.names_unusual.diverse_female"
    MESSY_FILLER_STARTERS = "messy.filler_words.sentence_starters"

    # Item paths
    ITEMS_COUNTABLE_SINGULAR = "items.countable_singular"
    ITEMS_COUNTABLE_PLURAL = "items.countable_plural"

    # Phrase paths
    PHRASES_EXPENSE_CATEGORIES = "phrases.expense_categories"
    PHRASES_PRODUCTION = "phrases.production"
    PHRASES_CONSUMPTION = "phrases.consumption_personal"

    # Pattern paths
    PATTERNS = "patterns"
    DOMAINS = "domains"


# =============================================================================
# GSM-8K CONSTANTS
# =============================================================================

# Trace depth distribution matching GSM-8K benchmark
GSM8K_DEPTH_WEIGHTS: Final[dict[int, float]] = {
    1: 0.10,
    2: 0.25,
    3: 0.30,
    4: 0.20,
    5: 0.10,
    6: 0.05,
}


# =============================================================================
# WORD MAPPINGS
# =============================================================================

# Multiplier words for natural language generation
MULTIPLIER_WORDS: Final[dict[int, str]] = {
    2: "twice",
    3: "three times",
    4: "four times",
    5: "five times",
}

# Growth words for natural language generation
GROWTH_WORDS: Final[dict[int, str]] = {
    2: "doubled",
    3: "tripled",
    4: "quadrupled",
    5: "quintupled",
}

# Number to word mapping (1-50)
WORD_NUMBERS: Final[dict[int, str]] = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
    21: "twenty-one",
    22: "twenty-two",
    23: "twenty-three",
    24: "twenty-four",
    25: "twenty-five",
    30: "thirty",
    40: "forty",
    50: "fifty",
}


# =============================================================================
# TYPE ALIASES (for better type hints)
# =============================================================================

# Trace step type alias
TraceStep = dict[str, str | int | float | list[str | int | float] | None]

# Variable context type alias
VariableContext = dict[str, int | float | bool | str]

# Template variables type alias
TemplateVars = dict[str, str | int | float]


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Expert types
    "ExpertType",
    "EXPERT_DIRS",
    "DEFAULT_EXPERT",
    # Trace operations
    "TraceOpType",
    "ComputeOpType",
    # Vocab types
    "VocabSpecType",
    "VariableType",
    # Difficulty
    "DifficultyLevel",
    # Template constants
    "TemplateVar",
    "VocabPath",
    # GSM-8K constants
    "GSM8K_DEPTH_WEIGHTS",
    # Word mappings
    "MULTIPLIER_WORDS",
    "GROWTH_WORDS",
    "WORD_NUMBERS",
    # Type aliases
    "TraceStep",
    "VariableContext",
    "TemplateVars",
]
