"""Pydantic configuration models for generation.

These models provide type-safe, validated configuration for:
- Problem generation settings
- Perturbation levels
- Diversity options
- GSM-8K style settings
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from chuk_virtual_expert_arithmetic.types import (
    GROWTH_WORDS,
    GSM8K_DEPTH_WEIGHTS,
    MULTIPLIER_WORDS,
    DifficultyLevel,
)


class DiversityConfig(BaseModel):
    """Configuration for output diversity.

    Controls how varied the generated problems are.
    """

    model_config = ConfigDict(extra="forbid")

    # Numeric diversity
    avoid_round_numbers: bool = False
    require_carrying: bool = False
    require_borrowing: bool = False

    # Vocabulary diversity
    messy_vocab_probability: float = Field(default=0.2, ge=0.0, le=1.0)
    use_diverse_names: bool = True
    use_specific_items: bool = True

    # Template diversity
    perturbation_level: float = Field(default=0.3, ge=0.0, le=1.0)
    use_gsm8k_style: bool = True
    gsm8k_style_probability: float = Field(default=0.5, ge=0.0, le=1.0)


class ConstraintConfig(BaseModel):
    """Configuration for constraint handling during generation."""

    model_config = ConfigDict(extra="forbid")

    max_constraint_retries: int = Field(default=100, ge=1)
    validate_answer: bool = True
    answer_must_be_positive: bool = False
    answer_must_be_integer: bool = False


class GenerationConfig(BaseModel):
    """Complete configuration for problem generation.

    This is the main configuration model that controls all aspects
    of problem generation.

    Example:
        >>> config = GenerationConfig(
        ...     seed=42,
        ...     difficulty=DifficultyLevel.MEDIUM,
        ...     diversity=DiversityConfig(perturbation_level=0.5),
        ... )
        >>> generator = SchemaGenerator(config=config)
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    # Core settings
    seed: int | None = None
    difficulty: DifficultyLevel | str = DifficultyLevel.MEDIUM

    # Sub-configurations
    diversity: DiversityConfig = Field(default_factory=DiversityConfig)
    constraints: ConstraintConfig = Field(default_factory=ConstraintConfig)

    # GSM-8K distribution settings
    gsm8k_depth_weights: dict[int, float] = Field(
        default_factory=lambda: dict(GSM8K_DEPTH_WEIGHTS)
    )

    # Word mappings (can be customized)
    multiplier_words: dict[int, str] = Field(
        default_factory=lambda: dict(MULTIPLIER_WORDS)
    )
    growth_words: dict[int, str] = Field(
        default_factory=lambda: dict(GROWTH_WORDS)
    )

    @field_validator("difficulty", mode="before")
    @classmethod
    def validate_difficulty(cls, v: Any) -> DifficultyLevel | str:
        """Allow both enum and string for difficulty."""
        if isinstance(v, str):
            try:
                return DifficultyLevel(v)
            except ValueError:
                return str(v)  # Allow custom difficulty strings
        if isinstance(v, DifficultyLevel):
            return v
        return str(v)

    @classmethod
    def for_training(cls, seed: int | None = None) -> GenerationConfig:
        """Create config optimized for training data generation.

        Higher diversity, GSM-8K style enabled.
        """
        return cls(
            seed=seed,
            difficulty=DifficultyLevel.MEDIUM,
            diversity=DiversityConfig(
                messy_vocab_probability=0.3,
                perturbation_level=0.4,
                use_gsm8k_style=True,
                gsm8k_style_probability=0.6,
            ),
        )

    @classmethod
    def for_evaluation(cls, seed: int | None = None) -> GenerationConfig:
        """Create config optimized for evaluation data generation.

        Lower diversity, more consistent output.
        """
        return cls(
            seed=seed,
            difficulty=DifficultyLevel.MEDIUM,
            diversity=DiversityConfig(
                messy_vocab_probability=0.0,
                perturbation_level=0.0,
                use_gsm8k_style=False,
            ),
        )

    @classmethod
    def for_debugging(cls, seed: int = 42) -> GenerationConfig:
        """Create config for debugging with reproducible output."""
        return cls(
            seed=seed,
            difficulty=DifficultyLevel.EASY,
            diversity=DiversityConfig(
                messy_vocab_probability=0.0,
                perturbation_level=0.0,
                use_gsm8k_style=False,
            ),
        )


class BatchConfig(BaseModel):
    """Configuration for batch generation.

    Controls how batches of problems are generated.
    """

    model_config = ConfigDict(extra="forbid")

    # Batch size settings
    batch_size: int = Field(default=100, ge=1)
    max_retries_per_item: int = Field(default=10, ge=1)

    # Balance settings
    balance_by_expert: bool = True
    balance_by_difficulty: bool = False
    balance_by_trace_depth: bool = False

    # GSM-8K distribution
    use_gsm8k_depth_distribution: bool = True

    # Async settings
    concurrency: int = Field(default=10, ge=1)


class TraceExampleConfig(BaseModel):
    """Configuration for TraceExample output format."""

    model_config = ConfigDict(extra="forbid")

    include_trace: bool = True
    include_metadata: bool = False
    format_numbers: bool = True  # Format large numbers with commas
    round_decimals: int | None = 2  # Round to N decimal places, None = no rounding
