"""Additional tests for VariableGenerator - comprehensive coverage."""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.core.variables import (
    DifficultyProfile,
    VariableGenerator,
)
from chuk_virtual_expert_arithmetic.models.schema_spec import VariableSpec


class TestVariableGeneratorInit:
    """Tests for VariableGenerator initialization."""

    def test_init_without_seed(self) -> None:
        """Test initialization without seed."""
        gen = VariableGenerator()
        assert gen._rng is not None

    def test_init_with_seed(self) -> None:
        """Test initialization with seed."""
        gen = VariableGenerator(seed=42)
        assert gen._seed == 42


class TestGenerateMethod:
    """Tests for generate method."""

    def test_generate_multiple_specs(self) -> None:
        """Test generating multiple variables."""
        gen = VariableGenerator(seed=42)
        specs = {
            "a": VariableSpec(type="int", min=1, max=10),
            "b": VariableSpec(type="int", min=1, max=10),
        }
        result = gen.generate(specs)
        assert "a" in result
        assert "b" in result
        assert 1 <= result["a"] <= 10
        assert 1 <= result["b"] <= 10


class TestGenerateOneMethod:
    """Tests for generate_one method."""

    def test_generate_int(self) -> None:
        """Test generating integer."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=10, max=20)
        result = gen.generate_one(spec)
        assert isinstance(result, int)
        assert 10 <= result <= 20

    def test_generate_float(self) -> None:
        """Test generating float."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="float", min=1.0, max=5.0)
        result = gen.generate_one(spec)
        assert isinstance(result, float)
        assert 1.0 <= result <= 5.0

    def test_generate_bool(self) -> None:
        """Test generating boolean."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="bool")
        result = gen.generate_one(spec)
        assert isinstance(result, bool)

    def test_generate_choice(self) -> None:
        """Test generating choice."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="choice", options=["a", "b", "c"])
        result = gen.generate_one(spec)
        assert result in ["a", "b", "c"]

    def test_generate_unknown_type_defaults_to_int(self) -> None:
        """Test unknown type defaults to int."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="unknown_type", min=5, max=15)
        result = gen.generate_one(spec)
        assert isinstance(result, int)
        assert 5 <= result <= 15


class TestGenerateInt:
    """Tests for _generate_int method."""

    def test_int_with_defaults(self) -> None:
        """Test int with default min/max."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int")
        result = gen.generate_one(spec)
        assert isinstance(result, int)
        assert 1 <= result <= 100

    def test_int_with_multiple_of(self) -> None:
        """Test int with multiple_of constraint."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=1, max=100, multiple_of=5)
        result = gen.generate_one(spec)
        assert result % 5 == 0

    def test_int_multiple_of_adjustment(self) -> None:
        """Test multiple_of adjustment when below min."""
        gen = VariableGenerator(seed=42)
        # This may produce a value where adjustment is needed
        spec = VariableSpec(type="int", min=7, max=15, multiple_of=5)
        result = gen.generate_one(spec)
        assert result % 5 == 0
        assert result >= 7

    def test_int_with_avoid_round(self) -> None:
        """Test int with avoid_round constraint."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=1, max=100, avoid_round=True)
        # Generate multiple times to test
        for _ in range(20):
            result = gen.generate_one(spec)
            assert result % 10 != 0

    def test_int_with_easy_difficulty(self) -> None:
        """Test int with easy difficulty."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=1, max=50, difficulty="easy")
        result = gen.generate_one(spec)
        assert isinstance(result, int)

    def test_int_with_medium_difficulty(self) -> None:
        """Test int with medium difficulty."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=1, max=100, difficulty="medium")
        result = gen.generate_one(spec)
        assert 1 <= result <= 100

    def test_int_with_hard_difficulty(self) -> None:
        """Test int with hard difficulty."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="int", min=1, max=200, difficulty="hard")
        result = gen.generate_one(spec)
        assert isinstance(result, int)


class TestGenerateNonRound:
    """Tests for _generate_non_round method."""

    def test_non_round_basic(self) -> None:
        """Test basic non-round generation."""
        gen = VariableGenerator(seed=42)
        result = gen._generate_non_round(1, 100)
        assert result % 10 != 0

    def test_non_round_with_few_options(self) -> None:
        """Test non-round with limited range."""
        gen = VariableGenerator(seed=42)
        # Range where round numbers are possible
        result = gen._generate_non_round(8, 12)
        assert result % 10 != 0

    def test_non_round_fallback_logic(self) -> None:
        """Test non-round fallback when attempts exhausted."""
        # Use a seed that produces round numbers
        gen = VariableGenerator(seed=100)
        # With a wider range, should eventually get non-round
        result = gen._generate_non_round(1, 99, attempts=1)
        # Should still produce a valid result
        assert isinstance(result, int)


class TestGenerateByDifficulty:
    """Tests for _generate_by_difficulty method."""

    def test_easy_with_valid_options(self) -> None:
        """Test easy difficulty with valid options."""
        gen = VariableGenerator(seed=42)
        result = gen._generate_by_difficulty("easy", 1, 50)
        assert isinstance(result, int)
        # Easy options are 5, 10, 15, 20, 25, 30
        # Should be one of these if within range
        assert 1 <= result <= 50

    def test_easy_with_no_valid_options(self) -> None:
        """Test easy difficulty with no valid easy options."""
        gen = VariableGenerator(seed=42)
        # Range that doesn't include easy options (5, 10, 15...)
        # The fallback rounds to nearest 5, which may be outside the range
        result = gen._generate_by_difficulty("easy", 31, 34)
        # Result will be rounded to nearest 5 (e.g., 30 or 35)
        assert isinstance(result, int)
        assert result % 5 == 0 or result == 0  # Rounds to 5 or uses fallback

    def test_easy_fallback_zero_case(self) -> None:
        """Test easy fallback when result is 0."""
        gen = VariableGenerator(seed=42)
        # Very small range that might produce 0 after rounding
        result = gen._generate_by_difficulty("easy", 1, 4)
        assert isinstance(result, int)
        assert 1 <= result <= 4

    def test_hard_difficulty(self) -> None:
        """Test hard difficulty."""
        gen = VariableGenerator(seed=42)
        result = gen._generate_by_difficulty("hard", 10, 100)
        assert isinstance(result, int)

    def test_medium_difficulty(self) -> None:
        """Test medium difficulty (default)."""
        gen = VariableGenerator(seed=42)
        result = gen._generate_by_difficulty("medium", 1, 100)
        assert 1 <= result <= 100


class TestGenerateFloat:
    """Tests for _generate_float method."""

    def test_float_basic(self) -> None:
        """Test basic float generation."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="float", min=1.0, max=10.0)
        result = gen.generate_one(spec)
        assert isinstance(result, float)
        assert 1.0 <= result <= 10.0

    def test_float_with_precision(self) -> None:
        """Test float with custom precision."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="float", min=0.0, max=1.0, precision=3)
        result = gen.generate_one(spec)
        # Check precision (at most 3 decimal places)
        assert result == round(result, 3)

    def test_float_with_defaults(self) -> None:
        """Test float with default min/max/precision."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="float")
        result = gen.generate_one(spec)
        assert 0.0 <= result <= 10.0
        assert result == round(result, 2)  # default precision is 2


class TestGenerateChoice:
    """Tests for _generate_choice method."""

    def test_choice_with_options(self) -> None:
        """Test choice with options."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="choice", options=[1, 2, 3])
        result = gen.generate_one(spec)
        assert result in [1, 2, 3]

    def test_choice_with_values(self) -> None:
        """Test choice with values (alternative to options)."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="choice", values=["x", "y", "z"])
        result = gen.generate_one(spec)
        assert result in ["x", "y", "z"]

    def test_choice_empty_returns_zero(self) -> None:
        """Test choice with empty options returns 0."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="choice", options=[])
        result = gen.generate_one(spec)
        assert result == 0

    def test_choice_none_options_returns_zero(self) -> None:
        """Test choice with None options returns 0."""
        gen = VariableGenerator(seed=42)
        spec = VariableSpec(type="choice")
        result = gen.generate_one(spec)
        assert result == 0


class TestReseed:
    """Tests for reseed method."""

    def test_reseed_with_new_seed(self) -> None:
        """Test reseeding with new seed."""
        gen = VariableGenerator(seed=42)
        gen.reseed(123)
        # After reseed, should produce different sequence
        spec = VariableSpec(type="int", min=1, max=100)
        result1 = gen.generate_one(spec)

        gen.reseed(123)
        result2 = gen.generate_one(spec)

        # Same seed should produce same result
        assert result1 == result2

    def test_reseed_with_none(self) -> None:
        """Test reseeding with None (random seed)."""
        gen = VariableGenerator(seed=42)
        gen.reseed(None)
        # Should still work
        spec = VariableSpec(type="int", min=1, max=100)
        result = gen.generate_one(spec)
        assert isinstance(result, int)


class TestDifficultyProfile:
    """Tests for DifficultyProfile class."""

    def test_easy_profile(self) -> None:
        """Test easy difficulty profile."""
        profile = DifficultyProfile.get("easy")
        assert profile["max_digits"] == 2
        assert profile["prefer_round"] is True
        assert profile["avoid_decimals"] is True

    def test_medium_profile(self) -> None:
        """Test medium difficulty profile."""
        profile = DifficultyProfile.get("medium")
        assert profile["max_digits"] == 3
        assert profile["prefer_round"] is False
        assert profile["allow_decimals"] is True

    def test_hard_profile(self) -> None:
        """Test hard difficulty profile."""
        profile = DifficultyProfile.get("hard")
        assert profile["max_digits"] == 4
        assert profile["avoid_round"] is True
        assert profile["allow_decimals"] is True

    def test_unknown_profile_defaults_to_medium(self) -> None:
        """Test unknown difficulty defaults to medium."""
        profile = DifficultyProfile.get("unknown")
        assert profile == DifficultyProfile.MEDIUM


class TestReproducibility:
    """Tests for reproducibility with seeds."""

    def test_same_seed_same_results(self) -> None:
        """Test that same seed produces same results."""
        gen1 = VariableGenerator(seed=42)
        gen2 = VariableGenerator(seed=42)

        specs = {
            "a": VariableSpec(type="int", min=1, max=100),
            "b": VariableSpec(type="float", min=0.0, max=1.0),
        }

        result1 = gen1.generate(specs)
        result2 = gen2.generate(specs)

        assert result1 == result2

    def test_different_seed_different_results(self) -> None:
        """Test that different seeds produce different results."""
        gen1 = VariableGenerator(seed=42)
        gen2 = VariableGenerator(seed=123)

        specs = {"a": VariableSpec(type="int", min=1, max=1000)}

        result1 = gen1.generate(specs)
        result2 = gen2.generate(specs)

        # Very unlikely to be the same with different seeds
        assert result1["a"] != result2["a"]
