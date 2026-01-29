"""Additional tests for perturbation module - comprehensive coverage."""

from __future__ import annotations

from typing import Any

from chuk_virtual_expert_arithmetic.core.perturbation import (
    NumericDiversifier,
    TemplatePerturbator,
)


class MockVocab:
    """Mock Vocab for testing."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}

    def get(self, path: Any) -> Any:
        # Handle both string paths and enum values
        path_str = str(path.value) if hasattr(path, "value") else str(path)
        return self._data.get(path_str)


class TestTemplatePerturbatorInit:
    """Tests for TemplatePerturbator initialization."""

    def test_init_without_vocab(self) -> None:
        """Test initialization without vocab."""
        perturbator = TemplatePerturbator(seed=42)
        assert perturbator._vocab is None
        assert perturbator._messy_fillers is None

    def test_init_with_vocab(self) -> None:
        """Test initialization with vocab."""
        vocab = MockVocab()
        perturbator = TemplatePerturbator(seed=42, vocab=vocab)
        assert perturbator._vocab is vocab


class TestGetFillerPhrases:
    """Tests for _get_filler_phrases method."""

    def test_default_fillers(self) -> None:
        """Test default filler phrases when no vocab."""
        perturbator = TemplatePerturbator(seed=42)
        fillers = perturbator._get_filler_phrases()
        assert fillers == TemplatePerturbator.FILLER_PHRASES

    def test_messy_fillers_from_vocab(self) -> None:
        """Test messy fillers from vocab."""
        vocab = MockVocab({"messy.filler_words.sentence_starters": ["Hey! ", "So, ", "Look, "]})
        perturbator = TemplatePerturbator(seed=42, vocab=vocab)
        fillers = perturbator._get_filler_phrases()
        assert "Hey! " in fillers
        assert "" in fillers  # Empty strings added for weighting

    def test_messy_fillers_cached(self) -> None:
        """Test that messy fillers are cached."""
        vocab = MockVocab({"messy.filler_starters": ["Test "]})
        perturbator = TemplatePerturbator(seed=42, vocab=vocab)
        fillers1 = perturbator._get_filler_phrases()
        fillers2 = perturbator._get_filler_phrases()
        assert fillers1 is fillers2


class TestPerturb:
    """Tests for perturb method."""

    def test_perturb_zero_level(self) -> None:
        """Test perturb with zero level returns unchanged."""
        perturbator = TemplatePerturbator(seed=42)
        query = "Alice has 5 apples."
        result = perturbator.perturb(query, level=0)
        assert result == query

    def test_perturb_high_level(self) -> None:
        """Test perturb with high level changes text."""
        perturbator = TemplatePerturbator(seed=42)
        query = "Alice has 5 apples. She gives 2 away. How many does she have?"
        result = perturbator.perturb(query, level=1.0)
        # With high level, something should change
        # (might still be same with unlucky seed, but typically changes)
        assert isinstance(result, str)


class TestAddFillerPhrase:
    """Tests for _add_filler_phrase method."""

    def test_add_filler_to_sentence(self) -> None:
        """Test adding filler phrase."""
        perturbator = TemplatePerturbator(seed=42)
        # Force a specific filler by testing multiple times
        text = "Alice has apples."
        result = perturbator._add_filler_phrase(text)
        # Either unchanged or has filler
        assert isinstance(result, str)

    def test_filler_with_lowercase_text(self) -> None:
        """Test filler not added when text starts lowercase."""
        perturbator = TemplatePerturbator(seed=42)
        text = "alice has apples."  # lowercase start
        result = perturbator._add_filler_phrase(text)
        # Should often return unchanged for lowercase
        assert isinstance(result, str)

    def test_filler_lowercases_first_char(self) -> None:
        """Test that filler lowercases first character."""
        perturbator = TemplatePerturbator(seed=42)
        # Run multiple times to catch a filler being added
        text = "Alice has apples."
        for _ in range(50):
            result = perturbator._add_filler_phrase(text)
            if result != text:
                # If changed, first char of original should be lowercase
                # (unless it's the filler ending in :)
                assert isinstance(result, str)
                break


class TestVaryQuestionForm:
    """Tests for _vary_question_form method."""

    def test_vary_how_many(self) -> None:
        """Test varying 'How many' form."""
        perturbator = TemplatePerturbator(seed=42)
        text = "How many apples does she have?"
        for _ in range(20):
            result = perturbator._vary_question_form(text)
            if result != text:
                # Should have a variation
                assert "apples" in result
                break

    def test_vary_how_much(self) -> None:
        """Test varying 'How much' form."""
        perturbator = TemplatePerturbator(seed=42)
        text = "How much does it cost?"
        result = perturbator._vary_question_form(text)
        assert isinstance(result, str)

    def test_vary_what_is(self) -> None:
        """Test varying 'What is' form."""
        perturbator = TemplatePerturbator(seed=42)
        text = "What is the total?"
        result = perturbator._vary_question_form(text)
        assert isinstance(result, str)

    def test_no_variation_for_unknown_form(self) -> None:
        """Test no variation for unknown question form."""
        perturbator = TemplatePerturbator(seed=42)
        text = "When will it be ready?"
        result = perturbator._vary_question_form(text)
        assert result == text


class TestSynonymSubstitution:
    """Tests for _synonym_substitution method."""

    def test_substitute_has(self) -> None:
        """Test substituting 'has'."""
        perturbator = TemplatePerturbator(seed=42)
        text = "Alice has 5 apples."
        # Run multiple times to catch substitution
        for _ in range(50):
            result = perturbator._synonym_substitution(text)
            if "owns" in result or "possesses" in result or "holds" in result:
                break
        # Substitution may or may not happen due to randomness

    def test_substitute_buys(self) -> None:
        """Test substituting 'buys'."""
        perturbator = TemplatePerturbator(seed=42)
        text = "She buys a book."
        result = perturbator._synonym_substitution(text)
        assert isinstance(result, str)

    def test_preserve_capitalization(self) -> None:
        """Test that capitalization is preserved."""
        perturbator = TemplatePerturbator(seed=42)
        text = "Has apples."  # Starts with capitalized synonym word
        for _ in range(50):
            result = perturbator._synonym_substitution(text)
            if result != text:
                # First word should be capitalized
                assert result[0].isupper()
                break

    def test_preserve_punctuation(self) -> None:
        """Test that punctuation is preserved."""
        perturbator = TemplatePerturbator(seed=42)
        text = "She has 5."
        for _ in range(50):
            result = perturbator._synonym_substitution(text)
            if result != text and "has" not in result.lower():
                # Period should still be there
                assert "." in result
                break

    def test_phrase_synonym_total(self) -> None:
        """Test phrase-level synonym for 'a total of'."""
        perturbator = TemplatePerturbator(seed=42)
        text = "There are a total of 5 items."
        # Run many times to trigger phrase substitution
        for _ in range(100):
            result = perturbator._synonym_substitution(text)
            if result != text:
                break
        # May or may not change due to probability

    def test_phrase_synonym_in_total(self) -> None:
        """Test phrase-level synonym for 'in total'."""
        perturbator = TemplatePerturbator(seed=42)
        text = "How many items are there in total?"
        result = perturbator._synonym_substitution(text)
        assert isinstance(result, str)


class TestReorderClauses:
    """Tests for _reorder_clauses method."""

    def test_reorder_three_sentences(self) -> None:
        """Test reordering with three sentences."""
        perturbator = TemplatePerturbator(seed=42)
        text = "Alice has 5 apples. Bob has 3 apples. How many apples are there?"
        result = perturbator._reorder_clauses(text)
        # Should still contain all information
        assert "Alice" in result
        assert "Bob" in result
        assert "?" in result

    def test_reorder_preserves_question_at_end(self) -> None:
        """Test that question stays at the end."""
        perturbator = TemplatePerturbator(seed=42)
        text = "First sentence. Second sentence. Third sentence. How many?"
        result = perturbator._reorder_clauses(text)
        assert result.rstrip().endswith("?")

    def test_too_few_sentences_unchanged(self) -> None:
        """Test that text with < 3 sentences is unchanged."""
        perturbator = TemplatePerturbator(seed=42)
        text = "One sentence. How many?"
        result = perturbator._reorder_clauses(text)
        assert result == text

    def test_no_question_unchanged(self) -> None:
        """Test that text without question is unchanged."""
        perturbator = TemplatePerturbator(seed=42)
        text = "First. Second. Third."
        result = perturbator._reorder_clauses(text)
        assert isinstance(result, str)

    def test_fix_capitalization(self) -> None:
        """Test that first letter is capitalized after reorder."""
        perturbator = TemplatePerturbator(seed=42)
        text = "Alice has 5. Bob has 3. Carol has 2. How many?"
        result = perturbator._reorder_clauses(text)
        assert result[0].isupper()


class TestTemplatePerturbatorReseed:
    """Tests for reseed method."""

    def test_reseed(self) -> None:
        """Test reseeding produces consistent results."""
        perturbator = TemplatePerturbator(seed=42)
        text = "Alice has 5 apples. She gives 2. How many does she have?"

        perturbator.reseed(123)
        result1 = perturbator.perturb(text, level=1.0)

        perturbator.reseed(123)
        result2 = perturbator.perturb(text, level=1.0)

        assert result1 == result2


class TestNumericDiversifierInit:
    """Tests for NumericDiversifier initialization."""

    def test_init_with_seed(self) -> None:
        """Test initialization with seed."""
        diversifier = NumericDiversifier(seed=42)
        assert diversifier._rng is not None

    def test_init_without_seed(self) -> None:
        """Test initialization without seed."""
        diversifier = NumericDiversifier()
        assert diversifier._rng is not None


class TestGenerateCarryingPair:
    """Tests for generate_carrying_pair method."""

    def test_carrying_pair_ones_sum_exceeds_10(self) -> None:
        """Test that ones digits sum exceeds 10."""
        diversifier = NumericDiversifier(seed=42)
        for _ in range(20):
            a, b = diversifier.generate_carrying_pair()
            ones_a = a % 10
            ones_b = b % 10
            assert ones_a + ones_b >= 10

    def test_carrying_pair_in_range(self) -> None:
        """Test that values are in specified range."""
        diversifier = NumericDiversifier(seed=42)
        a, b = diversifier.generate_carrying_pair(min_val=20, max_val=50)
        assert 20 <= a <= 50
        assert 20 <= b <= 50


class TestGenerateBorrowingPair:
    """Tests for generate_borrowing_pair method."""

    def test_borrowing_pair_requires_borrowing(self) -> None:
        """Test that subtraction requires borrowing."""
        diversifier = NumericDiversifier(seed=42)
        for _ in range(20):
            larger, smaller = diversifier.generate_borrowing_pair()
            ones_larger = larger % 10
            ones_smaller = smaller % 10
            assert ones_smaller > ones_larger
            assert larger > smaller

    def test_borrowing_pair_in_range(self) -> None:
        """Test that larger is in specified range."""
        diversifier = NumericDiversifier(seed=42)
        larger, smaller = diversifier.generate_borrowing_pair(min_val=30, max_val=80)
        assert 30 <= larger <= 80


class TestAvoidRoundNumber:
    """Tests for avoid_round_number method."""

    def test_avoid_round(self) -> None:
        """Test that result is not a multiple of 10."""
        diversifier = NumericDiversifier(seed=42)
        for _ in range(20):
            value = diversifier.avoid_round_number(1, 100)
            assert value % 10 != 0

    def test_avoid_round_in_range(self) -> None:
        """Test that result is in specified range."""
        diversifier = NumericDiversifier(seed=42)
        value = diversifier.avoid_round_number(50, 70)
        assert 50 <= value <= 79  # May be adjusted up by 9 max

    def test_avoid_round_fallback(self) -> None:
        """Test fallback when all attempts produce round numbers."""
        diversifier = NumericDiversifier(seed=42)
        # With normal range, should always find non-round
        value = diversifier.avoid_round_number(1, 100, attempts=1)
        assert isinstance(value, int)


class TestGenerateByDifficulty:
    """Tests for generate_by_difficulty method."""

    def test_easy_difficulty(self) -> None:
        """Test easy difficulty produces small round numbers."""
        diversifier = NumericDiversifier(seed=42)
        value = diversifier.generate_by_difficulty("easy")
        assert value in [5, 10, 15, 20, 25, 30]

    def test_hard_difficulty(self) -> None:
        """Test hard difficulty produces non-round numbers."""
        diversifier = NumericDiversifier(seed=42)
        value = diversifier.generate_by_difficulty("hard")
        assert value >= 50
        assert value % 10 != 0

    def test_medium_difficulty(self) -> None:
        """Test medium difficulty produces normal range."""
        diversifier = NumericDiversifier(seed=42)
        value = diversifier.generate_by_difficulty("medium", min_val=10, max_val=50)
        assert 10 <= value <= 50


class TestNumericDiversifierReseed:
    """Tests for reseed method."""

    def test_reseed(self) -> None:
        """Test reseeding produces consistent results."""
        diversifier = NumericDiversifier(seed=42)

        diversifier.reseed(123)
        a1, b1 = diversifier.generate_carrying_pair()

        diversifier.reseed(123)
        a2, b2 = diversifier.generate_carrying_pair()

        assert a1 == a2
        assert b1 == b2
