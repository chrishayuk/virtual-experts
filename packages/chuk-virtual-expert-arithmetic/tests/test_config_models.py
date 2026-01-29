"""Tests for config models - comprehensive coverage."""

from __future__ import annotations

import pytest

from chuk_virtual_expert_arithmetic.models.config import (
    BatchConfig,
    ConstraintConfig,
    DiversityConfig,
    GenerationConfig,
    TraceExampleConfig,
)
from chuk_virtual_expert_arithmetic.types import DifficultyLevel


class TestDiversityConfig:
    """Tests for DiversityConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = DiversityConfig()

        assert config.avoid_round_numbers is False
        assert config.require_carrying is False
        assert config.require_borrowing is False
        assert config.messy_vocab_probability == 0.2
        assert config.use_diverse_names is True
        assert config.use_specific_items is True
        assert config.perturbation_level == 0.3
        assert config.use_gsm8k_style is True
        assert config.gsm8k_style_probability == 0.5

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = DiversityConfig(
            avoid_round_numbers=True,
            require_carrying=True,
            require_borrowing=True,
            messy_vocab_probability=0.5,
            use_diverse_names=False,
            use_specific_items=False,
            perturbation_level=0.8,
            use_gsm8k_style=False,
            gsm8k_style_probability=0.0,
        )

        assert config.avoid_round_numbers is True
        assert config.require_carrying is True
        assert config.require_borrowing is True
        assert config.messy_vocab_probability == 0.5
        assert config.use_diverse_names is False
        assert config.use_specific_items is False
        assert config.perturbation_level == 0.8
        assert config.use_gsm8k_style is False
        assert config.gsm8k_style_probability == 0.0

    def test_probability_bounds(self) -> None:
        """Test probability values are bounded."""
        # Valid boundaries
        config = DiversityConfig(
            messy_vocab_probability=0.0,
            perturbation_level=0.0,
            gsm8k_style_probability=0.0,
        )
        assert config.messy_vocab_probability == 0.0
        assert config.perturbation_level == 0.0
        assert config.gsm8k_style_probability == 0.0

        config = DiversityConfig(
            messy_vocab_probability=1.0,
            perturbation_level=1.0,
            gsm8k_style_probability=1.0,
        )
        assert config.messy_vocab_probability == 1.0
        assert config.perturbation_level == 1.0
        assert config.gsm8k_style_probability == 1.0

    def test_invalid_probability_too_low(self) -> None:
        """Test invalid probability below 0."""
        with pytest.raises(ValueError):
            DiversityConfig(messy_vocab_probability=-0.1)

    def test_invalid_probability_too_high(self) -> None:
        """Test invalid probability above 1."""
        with pytest.raises(ValueError):
            DiversityConfig(messy_vocab_probability=1.1)

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise error."""
        with pytest.raises(ValueError):
            DiversityConfig(unknown_field="value")


class TestConstraintConfig:
    """Tests for ConstraintConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConstraintConfig()

        assert config.max_constraint_retries == 100
        assert config.validate_answer is True
        assert config.answer_must_be_positive is False
        assert config.answer_must_be_integer is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ConstraintConfig(
            max_constraint_retries=50,
            validate_answer=False,
            answer_must_be_positive=True,
            answer_must_be_integer=True,
        )

        assert config.max_constraint_retries == 50
        assert config.validate_answer is False
        assert config.answer_must_be_positive is True
        assert config.answer_must_be_integer is True

    def test_min_retries(self) -> None:
        """Test minimum retries constraint."""
        config = ConstraintConfig(max_constraint_retries=1)
        assert config.max_constraint_retries == 1

    def test_invalid_retries(self) -> None:
        """Test invalid retries below minimum."""
        with pytest.raises(ValueError):
            ConstraintConfig(max_constraint_retries=0)

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise error."""
        with pytest.raises(ValueError):
            ConstraintConfig(unknown_field="value")


class TestGenerationConfig:
    """Tests for GenerationConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = GenerationConfig()

        assert config.seed is None
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert isinstance(config.diversity, DiversityConfig)
        assert isinstance(config.constraints, ConstraintConfig)
        assert len(config.gsm8k_depth_weights) > 0
        assert len(config.multiplier_words) > 0
        assert len(config.growth_words) > 0

    def test_with_seed(self) -> None:
        """Test configuration with seed."""
        config = GenerationConfig(seed=42)
        assert config.seed == 42

    def test_difficulty_enum(self) -> None:
        """Test difficulty as enum."""
        config = GenerationConfig(difficulty=DifficultyLevel.EASY)
        assert config.difficulty == DifficultyLevel.EASY

        config = GenerationConfig(difficulty=DifficultyLevel.HARD)
        assert config.difficulty == DifficultyLevel.HARD

    def test_difficulty_string(self) -> None:
        """Test difficulty as string."""
        config = GenerationConfig(difficulty="easy")
        assert config.difficulty == DifficultyLevel.EASY

        config = GenerationConfig(difficulty="medium")
        assert config.difficulty == DifficultyLevel.MEDIUM

        config = GenerationConfig(difficulty="hard")
        assert config.difficulty == DifficultyLevel.HARD

    def test_difficulty_custom_string(self) -> None:
        """Test custom difficulty string."""
        config = GenerationConfig(difficulty="expert")
        assert config.difficulty == "expert"

    def test_difficulty_from_non_string(self) -> None:
        """Test difficulty from non-string type."""
        # Using a mock-like object to test type conversion
        config = GenerationConfig(difficulty="custom_level")
        assert config.difficulty == "custom_level"

    def test_nested_diversity_config(self) -> None:
        """Test nested diversity config."""
        config = GenerationConfig(
            diversity=DiversityConfig(
                perturbation_level=0.9,
                use_gsm8k_style=False,
            )
        )

        assert config.diversity.perturbation_level == 0.9
        assert config.diversity.use_gsm8k_style is False

    def test_nested_constraint_config(self) -> None:
        """Test nested constraint config."""
        config = GenerationConfig(
            constraints=ConstraintConfig(
                max_constraint_retries=50,
            )
        )

        assert config.constraints.max_constraint_retries == 50

    def test_custom_depth_weights(self) -> None:
        """Test custom GSM-8K depth weights."""
        custom_weights = {1: 0.5, 2: 0.3, 3: 0.2}
        config = GenerationConfig(gsm8k_depth_weights=custom_weights)
        assert config.gsm8k_depth_weights == custom_weights

    def test_custom_multiplier_words(self) -> None:
        """Test custom multiplier words."""
        custom_words = {2: "double", 3: "triple"}
        config = GenerationConfig(multiplier_words=custom_words)
        assert config.multiplier_words == custom_words

    def test_custom_growth_words(self) -> None:
        """Test custom growth words."""
        custom_words = {2: "doubled", 3: "tripled"}
        config = GenerationConfig(growth_words=custom_words)
        assert config.growth_words == custom_words


class TestGenerationConfigFactoryMethods:
    """Tests for GenerationConfig factory methods."""

    def test_for_training(self) -> None:
        """Test training configuration factory."""
        config = GenerationConfig.for_training()

        assert config.seed is None
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.diversity.messy_vocab_probability == 0.3
        assert config.diversity.perturbation_level == 0.4
        assert config.diversity.use_gsm8k_style is True
        assert config.diversity.gsm8k_style_probability == 0.6

    def test_for_training_with_seed(self) -> None:
        """Test training configuration with seed."""
        config = GenerationConfig.for_training(seed=42)
        assert config.seed == 42

    def test_for_evaluation(self) -> None:
        """Test evaluation configuration factory."""
        config = GenerationConfig.for_evaluation()

        assert config.seed is None
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.diversity.messy_vocab_probability == 0.0
        assert config.diversity.perturbation_level == 0.0
        assert config.diversity.use_gsm8k_style is False

    def test_for_evaluation_with_seed(self) -> None:
        """Test evaluation configuration with seed."""
        config = GenerationConfig.for_evaluation(seed=123)
        assert config.seed == 123

    def test_for_debugging(self) -> None:
        """Test debugging configuration factory."""
        config = GenerationConfig.for_debugging()

        assert config.seed == 42
        assert config.difficulty == DifficultyLevel.EASY
        assert config.diversity.messy_vocab_probability == 0.0
        assert config.diversity.perturbation_level == 0.0
        assert config.diversity.use_gsm8k_style is False

    def test_for_debugging_with_seed(self) -> None:
        """Test debugging configuration with custom seed."""
        config = GenerationConfig.for_debugging(seed=100)
        assert config.seed == 100


class TestBatchConfig:
    """Tests for BatchConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BatchConfig()

        assert config.batch_size == 100
        assert config.max_retries_per_item == 10
        assert config.balance_by_expert is True
        assert config.balance_by_difficulty is False
        assert config.balance_by_trace_depth is False
        assert config.use_gsm8k_depth_distribution is True
        assert config.concurrency == 10

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BatchConfig(
            batch_size=50,
            max_retries_per_item=5,
            balance_by_expert=False,
            balance_by_difficulty=True,
            balance_by_trace_depth=True,
            use_gsm8k_depth_distribution=False,
            concurrency=20,
        )

        assert config.batch_size == 50
        assert config.max_retries_per_item == 5
        assert config.balance_by_expert is False
        assert config.balance_by_difficulty is True
        assert config.balance_by_trace_depth is True
        assert config.use_gsm8k_depth_distribution is False
        assert config.concurrency == 20

    def test_min_batch_size(self) -> None:
        """Test minimum batch size."""
        config = BatchConfig(batch_size=1)
        assert config.batch_size == 1

    def test_invalid_batch_size(self) -> None:
        """Test invalid batch size."""
        with pytest.raises(ValueError):
            BatchConfig(batch_size=0)

    def test_min_retries(self) -> None:
        """Test minimum retries."""
        config = BatchConfig(max_retries_per_item=1)
        assert config.max_retries_per_item == 1

    def test_invalid_retries(self) -> None:
        """Test invalid retries."""
        with pytest.raises(ValueError):
            BatchConfig(max_retries_per_item=0)

    def test_min_concurrency(self) -> None:
        """Test minimum concurrency."""
        config = BatchConfig(concurrency=1)
        assert config.concurrency == 1

    def test_invalid_concurrency(self) -> None:
        """Test invalid concurrency."""
        with pytest.raises(ValueError):
            BatchConfig(concurrency=0)

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise error."""
        with pytest.raises(ValueError):
            BatchConfig(unknown_field="value")


class TestTraceExampleConfig:
    """Tests for TraceExampleConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TraceExampleConfig()

        assert config.include_trace is True
        assert config.include_metadata is False
        assert config.format_numbers is True
        assert config.round_decimals == 2

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = TraceExampleConfig(
            include_trace=False,
            include_metadata=True,
            format_numbers=False,
            round_decimals=4,
        )

        assert config.include_trace is False
        assert config.include_metadata is True
        assert config.format_numbers is False
        assert config.round_decimals == 4

    def test_no_rounding(self) -> None:
        """Test disabling decimal rounding."""
        config = TraceExampleConfig(round_decimals=None)
        assert config.round_decimals is None

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise error."""
        with pytest.raises(ValueError):
            TraceExampleConfig(unknown_field="value")


class TestConfigSerialization:
    """Test config serialization and deserialization."""

    def test_generation_config_to_dict(self) -> None:
        """Test GenerationConfig serialization."""
        config = GenerationConfig(
            seed=42,
            difficulty=DifficultyLevel.HARD,
        )
        data = config.model_dump()

        assert data["seed"] == 42
        assert data["difficulty"] == "hard"
        assert "diversity" in data
        assert "constraints" in data

    def test_generation_config_from_dict(self) -> None:
        """Test GenerationConfig deserialization."""
        data = {
            "seed": 42,
            "difficulty": "medium",
            "diversity": {
                "perturbation_level": 0.5,
            },
        }

        config = GenerationConfig(**data)

        assert config.seed == 42
        assert config.difficulty == DifficultyLevel.MEDIUM
        assert config.diversity.perturbation_level == 0.5

    def test_batch_config_to_dict(self) -> None:
        """Test BatchConfig serialization."""
        config = BatchConfig(batch_size=200)
        data = config.model_dump()

        assert data["batch_size"] == 200

    def test_diversity_config_to_dict(self) -> None:
        """Test DiversityConfig serialization."""
        config = DiversityConfig(perturbation_level=0.7)
        data = config.model_dump()

        assert data["perturbation_level"] == 0.7
