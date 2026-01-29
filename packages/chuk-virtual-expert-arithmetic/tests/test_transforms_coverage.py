"""Additional tests for TransformRegistry - comprehensive coverage."""

from __future__ import annotations

from typing import Any

import pytest

from chuk_virtual_expert_arithmetic.core.transforms import (
    TransformError,
    TransformRegistry,
    capitalize,
    does_do,
    has_have,
    lower,
    ordinal,
    pluralize,
    singularize,
    upper,
    with_article,
)


class TestPluralizeFunction:
    """Tests for pluralize function."""

    def test_regular_plural(self) -> None:
        """Test regular pluralization."""
        assert pluralize("book") == "books"
        assert pluralize("car") == "cars"
        assert pluralize("pen") == "pens"

    def test_ending_s(self) -> None:
        """Test words ending in s."""
        assert pluralize("bus") == "buses"
        assert pluralize("class") == "classes"

    def test_ending_x(self) -> None:
        """Test words ending in x."""
        assert pluralize("box") == "boxes"
        assert pluralize("tax") == "taxes"

    def test_ending_ch(self) -> None:
        """Test words ending in ch."""
        assert pluralize("match") == "matches"
        assert pluralize("watch") == "watches"

    def test_ending_sh(self) -> None:
        """Test words ending in sh."""
        assert pluralize("dish") == "dishes"
        assert pluralize("brush") == "brushes"

    def test_ending_consonant_y(self) -> None:
        """Test words ending in consonant+y."""
        assert pluralize("baby") == "babies"
        assert pluralize("city") == "cities"
        assert pluralize("party") == "parties"

    def test_ending_vowel_y(self) -> None:
        """Test words ending in vowel+y."""
        assert pluralize("key") == "keys"
        assert pluralize("day") == "days"
        assert pluralize("toy") == "toys"

    def test_none_input(self) -> None:
        """Test with None input."""
        # pluralize converts to string first
        assert pluralize(None) == "Nones"

    def test_non_string_input(self) -> None:
        """Test with non-string input."""
        result = pluralize(123)
        assert result == "123s"


class TestSingularizeFunction:
    """Tests for singularize function."""

    def test_regular_singular(self) -> None:
        """Test regular singularization."""
        assert singularize("books") == "book"
        assert singularize("cars") == "car"

    def test_ending_ies(self) -> None:
        """Test words ending in ies."""
        assert singularize("babies") == "baby"
        assert singularize("cities") == "city"
        assert singularize("parties") == "party"

    def test_ending_es(self) -> None:
        """Test words ending in es."""
        assert singularize("boxes") == "box"
        assert singularize("buses") == "bus"
        assert singularize("matches") == "match"
        assert singularize("dishes") == "dish"

    def test_none_input(self) -> None:
        """Test with None input."""
        # singularize converts to string first
        assert singularize(None) == "None"

    def test_non_string_input(self) -> None:
        """Test with non-string input."""
        result = singularize(123)
        assert result == "123"


class TestCapitalizeFunction:
    """Tests for capitalize function."""

    def test_lowercase(self) -> None:
        """Test capitalizing lowercase."""
        assert capitalize("hello") == "Hello"

    def test_uppercase(self) -> None:
        """Test capitalizing uppercase."""
        assert capitalize("HELLO") == "Hello"

    def test_mixed_case(self) -> None:
        """Test capitalizing mixed case."""
        assert capitalize("hELLO") == "Hello"

    def test_non_string(self) -> None:
        """Test with non-string input."""
        assert capitalize(123) == "123"


class TestLowerUpperFunctions:
    """Tests for lower and upper functions."""

    def test_lower(self) -> None:
        """Test lower function."""
        assert lower("HELLO") == "hello"
        assert lower("HeLLo") == "hello"

    def test_upper(self) -> None:
        """Test upper function."""
        assert upper("hello") == "HELLO"
        assert upper("HeLLo") == "HELLO"

    def test_non_string(self) -> None:
        """Test with non-string input."""
        assert lower(123) == "123"
        assert upper(456) == "456"


class TestHasHaveDoesDoFunctions:
    """Tests for has_have and does_do functions."""

    def test_has_have_singular(self) -> None:
        """Test has_have with singular marker."""
        assert has_have("s") == "has"

    def test_has_have_plural(self) -> None:
        """Test has_have with plural/other values."""
        assert has_have("") == "have"
        assert has_have("pl") == "have"
        assert has_have(None) == "have"

    def test_does_do_singular(self) -> None:
        """Test does_do with singular marker."""
        assert does_do("s") == "does"

    def test_does_do_plural(self) -> None:
        """Test does_do with plural/other values."""
        assert does_do("") == "do"
        assert does_do("pl") == "do"
        assert does_do(None) == "do"


class TestWithArticleFunction:
    """Tests for with_article function."""

    def test_vowel_words(self) -> None:
        """Test with vowel-starting words."""
        assert with_article("apple") == "an apple"
        assert with_article("orange") == "an orange"

    def test_consonant_words(self) -> None:
        """Test with consonant-starting words."""
        assert with_article("book") == "a book"
        assert with_article("car") == "a car"

    def test_none_input(self) -> None:
        """Test with None input."""
        # with_article converts to string first
        assert with_article(None) == "a None"


class TestOrdinalFunction:
    """Tests for ordinal function."""

    def test_1st_2nd_3rd(self) -> None:
        """Test 1st, 2nd, 3rd."""
        assert ordinal(1) == "1st"
        assert ordinal(2) == "2nd"
        assert ordinal(3) == "3rd"

    def test_11th_12th_13th(self) -> None:
        """Test 11th, 12th, 13th exceptions."""
        assert ordinal(11) == "11th"
        assert ordinal(12) == "12th"
        assert ordinal(13) == "13th"

    def test_21st_22nd_23rd(self) -> None:
        """Test 21st, 22nd, 23rd."""
        assert ordinal(21) == "21st"
        assert ordinal(22) == "22nd"
        assert ordinal(23) == "23rd"

    def test_4th_through_10th(self) -> None:
        """Test 4th through 10th."""
        assert ordinal(4) == "4th"
        assert ordinal(5) == "5th"
        assert ordinal(6) == "6th"
        assert ordinal(7) == "7th"
        assert ordinal(8) == "8th"
        assert ordinal(9) == "9th"
        assert ordinal(10) == "10th"

    def test_larger_numbers(self) -> None:
        """Test larger numbers."""
        assert ordinal(100) == "100th"
        assert ordinal(101) == "101st"
        assert ordinal(111) == "111th"
        assert ordinal(112) == "112th"
        assert ordinal(121) == "121st"

    def test_none_input(self) -> None:
        """Test with None input."""
        # ordinal returns string when can't convert to int
        assert ordinal(None) == "None"

    def test_non_integer_input(self) -> None:
        """Test with non-integer input."""
        result = ordinal("test")
        assert result == "test"

    def test_string_integer_input(self) -> None:
        """Test with string integer input."""
        assert ordinal("5") == "5th"
        assert ordinal("21") == "21st"


class TestTransformRegistry:
    """Tests for TransformRegistry class."""

    def test_apply_pluralize(self) -> None:
        """Test apply with pluralize transform."""
        assert TransformRegistry.apply("dog", "pluralize") == "dogs"

    def test_apply_singularize(self) -> None:
        """Test apply with singularize transform."""
        assert TransformRegistry.apply("dogs", "singularize") == "dog"

    def test_apply_capitalize(self) -> None:
        """Test apply with capitalize transform."""
        assert TransformRegistry.apply("hello", "capitalize") == "Hello"
        assert TransformRegistry.apply("HELLO", "capitalize") == "Hello"

    def test_apply_lower(self) -> None:
        """Test apply with lower transform."""
        assert TransformRegistry.apply("HELLO", "lower") == "hello"

    def test_apply_upper(self) -> None:
        """Test apply with upper transform."""
        assert TransformRegistry.apply("hello", "upper") == "HELLO"

    def test_apply_with_article(self) -> None:
        """Test apply with with_article transform."""
        assert TransformRegistry.apply("apple", "with_article") == "an apple"

    def test_apply_ordinal(self) -> None:
        """Test apply with ordinal transform."""
        assert TransformRegistry.apply(1, "ordinal") == "1st"

    def test_apply_has_have(self) -> None:
        """Test apply with has_have transform."""
        assert TransformRegistry.apply("s", "has_have") == "has"
        assert TransformRegistry.apply("", "has_have") == "have"
        assert TransformRegistry.apply("plural", "has_have") == "have"

    def test_apply_does_do(self) -> None:
        """Test apply with does_do transform."""
        assert TransformRegistry.apply("s", "does_do") == "does"
        assert TransformRegistry.apply("", "does_do") == "do"
        assert TransformRegistry.apply("plural", "does_do") == "do"

    def test_apply_unknown_transform(self) -> None:
        """Test apply with unknown transform raises TransformError."""
        with pytest.raises(TransformError, match="Unknown transform"):
            TransformRegistry.apply("test", "unknown_transform_xyz")

    def test_register_custom(self) -> None:
        """Test registering custom transform."""
        TransformRegistry.register("reverse", lambda x: x[::-1] if isinstance(x, str) else x)
        try:
            assert TransformRegistry.apply("hello", "reverse") == "olleh"
        finally:
            TransformRegistry.unregister("reverse")

    def test_unregister(self) -> None:
        """Test unregistering transform."""
        TransformRegistry.register("temp", lambda x: x)
        TransformRegistry.unregister("temp")
        # After unregister, should raise error
        with pytest.raises(TransformError, match="Unknown transform"):
            TransformRegistry.apply("test", "temp")

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering nonexistent transform doesn't error."""
        TransformRegistry.unregister("definitely_not_a_transform")

    def test_list_transforms(self) -> None:
        """Test listing available transforms via get_all."""
        transforms = TransformRegistry.get_all()
        assert "pluralize" in transforms
        assert "singularize" in transforms
        assert "capitalize" in transforms

    def test_apply_none_value(self) -> None:
        """Test apply with None value."""
        # Functions convert None to string
        assert TransformRegistry.apply(None, "pluralize") == "Nones"
        assert TransformRegistry.apply(None, "capitalize") == "None"

    def test_apply_chain(self) -> None:
        """Test apply_chain method."""
        result = TransformRegistry.apply_chain("apples", ["singularize", "capitalize"])
        assert result == "Apple"

    def test_get_all(self) -> None:
        """Test get_all method."""
        transforms = TransformRegistry.get_all()
        assert "pluralize" in transforms
        assert callable(transforms["pluralize"])

    def test_exists(self) -> None:
        """Test exists method."""
        assert TransformRegistry.exists("pluralize") is True
        assert TransformRegistry.exists("nonexistent_xyz") is False

    def test_transform_error(self) -> None:
        """Test transform that raises error."""
        def bad_transform(x: Any) -> Any:
            raise ValueError("Test error")

        TransformRegistry.register("bad", bad_transform)
        try:
            with pytest.raises(TransformError, match="Transform 'bad' failed"):
                TransformRegistry.apply("test", "bad")
        finally:
            TransformRegistry.unregister("bad")
