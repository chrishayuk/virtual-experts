"""Tests for perturbation and numeric diversity."""

import pytest

from chuk_virtual_expert_arithmetic.core import NumericDiversifier, TemplatePerturbator


class TestTemplatePerturbator:
    """Tests for TemplatePerturbator."""

    @pytest.fixture
    def perturbator(self) -> TemplatePerturbator:
        """Create a perturbator instance."""
        return TemplatePerturbator(seed=42)

    def test_no_perturbation_at_zero_level(self, perturbator: TemplatePerturbator) -> None:
        """Test that level=0 returns original text."""
        original = "Alice has 5 apples."
        result = perturbator.perturb(original, level=0)
        assert result == original

    def test_perturbation_modifies_text(self, perturbator: TemplatePerturbator) -> None:
        """Test that high perturbation level modifies text."""
        original = "How many apples does Alice have?"

        # Run multiple times - at least some should be modified
        modified_count = 0
        for _ in range(20):
            result = perturbator.perturb(original, level=0.8)
            if result != original:
                modified_count += 1

        assert modified_count > 0, "Expected some perturbations at level=0.8"

    def test_question_form_variation(self, perturbator: TemplatePerturbator) -> None:
        """Test that question forms can be varied."""
        original = "How many cookies are left?"

        variations = set()
        for _ in range(50):
            result = perturbator._vary_question_form(original)
            variations.add(result)

        # Should have at least 2 variations
        assert len(variations) >= 2

    def test_filler_phrases(self, perturbator: TemplatePerturbator) -> None:
        """Test adding filler phrases."""
        original = "Alice has 5 apples."

        results = set()
        for _ in range(50):
            result = perturbator._add_filler_phrase(original)
            results.add(result)

        # Should have variations (some with fillers, some without)
        assert len(results) >= 2

    def test_synonym_substitution(self, perturbator: TemplatePerturbator) -> None:
        """Test synonym substitution."""
        original = "She has 5 apples and gets 3 more."

        # Run multiple times
        variations = set()
        for _ in range(50):
            result = perturbator._synonym_substitution(original)
            variations.add(result)

        # Should have at least some variations
        assert len(variations) >= 1

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed gives same results."""
        p1 = TemplatePerturbator(seed=123)
        p2 = TemplatePerturbator(seed=123)

        original = "How many apples does Alice have total?"

        results1 = [p1.perturb(original, level=0.5) for _ in range(10)]
        results2 = [p2.perturb(original, level=0.5) for _ in range(10)]

        assert results1 == results2

    def test_preserves_numbers(self, perturbator: TemplatePerturbator) -> None:
        """Test that numbers in text are preserved."""
        original = "Alice has 5 apples and buys 3 more for $2 each."
        result = perturbator.perturb(original, level=0.5)

        assert "5" in result
        assert "3" in result
        assert "2" in result


class TestNumericDiversifier:
    """Tests for NumericDiversifier."""

    @pytest.fixture
    def diversifier(self) -> NumericDiversifier:
        """Create a diversifier instance."""
        return NumericDiversifier(seed=42)

    def test_carrying_pair(self, diversifier: NumericDiversifier) -> None:
        """Test generating pairs that require carrying."""
        for _ in range(20):
            a, b = diversifier.generate_carrying_pair()

            # Ones digits should sum to >= 10
            ones_sum = (a % 10) + (b % 10)
            assert ones_sum >= 10, f"Expected carrying: {a} + {b} (ones sum: {ones_sum})"

    def test_borrowing_pair(self, diversifier: NumericDiversifier) -> None:
        """Test generating pairs that require borrowing."""
        for _ in range(20):
            larger, smaller = diversifier.generate_borrowing_pair()

            assert larger > smaller

            # Smaller's ones digit should be larger than larger's
            ones_larger = larger % 10
            ones_smaller = smaller % 10
            assert ones_smaller > ones_larger, (
                f"Expected borrowing: {larger} - {smaller} (ones: {ones_larger} vs {ones_smaller})"
            )

    def test_avoid_round_number(self, diversifier: NumericDiversifier) -> None:
        """Test generating non-round numbers."""
        for _ in range(20):
            value = diversifier.avoid_round_number(1, 100)
            assert value % 10 != 0, f"Expected non-round: {value}"

    def test_difficulty_easy(self, diversifier: NumericDiversifier) -> None:
        """Test easy difficulty generates small/round numbers."""
        values = [diversifier.generate_by_difficulty("easy") for _ in range(20)]

        # All should be <= 30 and round
        for v in values:
            assert v <= 30
            assert v % 5 == 0  # Multiple of 5

    def test_difficulty_hard(self, diversifier: NumericDiversifier) -> None:
        """Test hard difficulty generates larger non-round numbers."""
        non_round_count = 0
        for _ in range(20):
            value = diversifier.generate_by_difficulty("hard")
            if value % 10 != 0:
                non_round_count += 1

        # Most should be non-round
        assert non_round_count > 10

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed gives same results."""
        d1 = NumericDiversifier(seed=123)
        d2 = NumericDiversifier(seed=123)

        pairs1 = [d1.generate_carrying_pair() for _ in range(10)]
        pairs2 = [d2.generate_carrying_pair() for _ in range(10)]

        assert pairs1 == pairs2
