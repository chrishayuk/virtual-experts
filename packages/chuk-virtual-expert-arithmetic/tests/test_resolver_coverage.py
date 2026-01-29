"""Additional tests for TemplateResolver - comprehensive coverage."""

from __future__ import annotations

from typing import Any

from chuk_virtual_expert_arithmetic.core.resolver import TemplateResolver


class TestResolveAll:
    """Tests for resolve_all method."""

    def test_empty_specs(self) -> None:
        """Test with empty specs."""
        resolver = TemplateResolver()
        result = resolver.resolve_all({}, {}, {})
        assert result == {}

    def test_multiple_specs(self) -> None:
        """Test resolving multiple specs."""
        resolver = TemplateResolver()
        specs = {"x": "count", "y": "price"}
        variables = {"count": 10, "price": 5}
        result = resolver.resolve_all(specs, variables, {})
        assert result == {"x": 10, "y": 5}


class TestResolveWithTransforms:
    """Tests for resolve with pipe transforms."""

    def test_single_transform(self) -> None:
        """Test single transform."""
        resolver = TemplateResolver()
        result = resolver.resolve("item|pluralize", {"item": "apple"}, {"item": "apple"})
        assert result == "apples"

    def test_chained_transforms(self) -> None:
        """Test chained transforms."""
        resolver = TemplateResolver()
        result = resolver.resolve("item|capitalize", {}, {"item": "book"})
        assert result == "Book"

    def test_unknown_transform_logs_warning(self) -> None:
        """Test unknown transform logs warning and returns value unchanged."""
        resolver = TemplateResolver()
        result = resolver.resolve("item|nonexistent_transform", {}, {"item": "test"})
        # Value should be returned unchanged
        assert result == "test"

    def test_multiple_unknown_transforms(self) -> None:
        """Test multiple unknown transforms."""
        resolver = TemplateResolver()
        result = resolver.resolve("item|bad1|bad2", {}, {"item": "value"})
        assert result == "value"


class TestResolveDotNotation:
    """Tests for resolve with dot notation."""

    def test_simple_dot_notation(self) -> None:
        """Test simple dot notation."""
        resolver = TemplateResolver()
        vocab = {"person": {"name": "Alice", "age": 30}}
        result = resolver.resolve("person.name", {}, vocab)
        assert result == "Alice"

    def test_deep_dot_notation(self) -> None:
        """Test deep dot notation."""
        resolver = TemplateResolver()
        vocab = {"data": {"level1": {"level2": "deep_value"}}}
        result = resolver.resolve("data.level1.level2", {}, vocab)
        assert result == "deep_value"

    def test_dot_notation_list_index(self) -> None:
        """Test dot notation with list index."""
        resolver = TemplateResolver()
        vocab = {"items": ["first", "second", "third"]}
        result = resolver.resolve("items.0", {}, vocab)
        assert result == "first"

    def test_dot_notation_list_index_middle(self) -> None:
        """Test dot notation with middle list index."""
        resolver = TemplateResolver()
        vocab = {"items": ["a", "b", "c"]}
        result = resolver.resolve("items.1", {}, vocab)
        assert result == "b"

    def test_dot_notation_list_index_out_of_bounds(self) -> None:
        """Test dot notation with out of bounds index."""
        resolver = TemplateResolver()
        vocab = {"items": ["only"]}
        result = resolver.resolve("items.99", {}, vocab)
        assert result is None

    def test_dot_notation_on_non_dict_non_list(self) -> None:
        """Test dot notation on non-dict, non-list object."""
        resolver = TemplateResolver()
        vocab = {"value": "string_value"}
        result = resolver.resolve("value.something", {}, vocab)
        assert result is None

    def test_dot_notation_not_found(self) -> None:
        """Test dot notation with missing key."""
        resolver = TemplateResolver()
        vocab = {"person": {"name": "Bob"}}
        result = resolver.resolve("person.missing", {}, vocab)
        assert result is None

    def test_dot_notation_from_variables(self) -> None:
        """Test dot notation from variables."""
        resolver = TemplateResolver()
        variables = {"data": {"value": 42}}
        result = resolver.resolve("data.value", variables, {})
        assert result == 42


class TestResolveLiterals:
    """Tests for resolve with literals."""

    def test_literal_string(self) -> None:
        """Test literal string when not found."""
        resolver = TemplateResolver()
        result = resolver.resolve("literal_value", {}, {})
        assert result == "literal_value"

    def test_lookup_in_vocab(self) -> None:
        """Test direct lookup in vocab."""
        resolver = TemplateResolver()
        result = resolver.resolve("item", {}, {"item": "book"})
        assert result == "book"

    def test_lookup_in_variables(self) -> None:
        """Test direct lookup in variables."""
        resolver = TemplateResolver()
        result = resolver.resolve("count", {"count": 5}, {})
        assert result == 5


class TestBuildTemplateVars:
    """Tests for build_template_vars method."""

    def test_empty_specs(self) -> None:
        """Test with no specs."""
        resolver = TemplateResolver()
        result = resolver.build_template_vars(None, {}, {})
        assert result == {}

    def test_with_specs(self) -> None:
        """Test with specs."""
        resolver = TemplateResolver()
        specs = {"name": "person.name"}
        vocab = {"person": {"name": "Alice"}}
        result = resolver.build_template_vars(specs, {}, vocab)
        assert result["name"] == "Alice"

    def test_adds_numeric_variables(self) -> None:
        """Test that numeric variables are added."""
        resolver = TemplateResolver()
        variables = {"count": 10, "price": 5}
        result = resolver.build_template_vars(None, variables, {})
        assert result["count"] == 10
        assert result["price"] == 5

    def test_multiplier_words_twice(self) -> None:
        """Test multiplier word for 2 (twice)."""
        resolver = TemplateResolver()
        variables = {"multiplier": 2}
        result = resolver.build_template_vars(None, variables, {})
        assert result["mult_word"] == "twice"
        assert result["growth_word"] == "doubled"

    def test_multiplier_words_three_times(self) -> None:
        """Test multiplier word for 3."""
        resolver = TemplateResolver()
        variables = {"multiplier": 3}
        result = resolver.build_template_vars(None, variables, {})
        assert result["mult_word"] == "three times"
        assert result["growth_word"] == "tripled"

    def test_multiplier_words_four_times(self) -> None:
        """Test multiplier word for 4."""
        resolver = TemplateResolver()
        variables = {"multiplier": 4}
        result = resolver.build_template_vars(None, variables, {})
        assert result["mult_word"] == "four times"
        assert result["growth_word"] == "quadrupled"

    def test_multiplier_words_five_times(self) -> None:
        """Test multiplier word for 5."""
        resolver = TemplateResolver()
        variables = {"multiplier": 5}
        result = resolver.build_template_vars(None, variables, {})
        assert result["mult_word"] == "five times"
        assert result["growth_word"] == "quintupled"

    def test_multiplier_words_fallback(self) -> None:
        """Test multiplier word fallback for unsupported values."""
        resolver = TemplateResolver()
        variables = {"multiplier": 7}
        result = resolver.build_template_vars(None, variables, {})
        assert result["mult_word"] == "7 times"
        assert result["growth_word"] == "multiplied by 7"


class TestExpandVocabItems:
    """Tests for _expand_vocab_items method."""

    def test_expand_dict_vocab(self) -> None:
        """Test expanding dict-type vocab."""
        resolver = TemplateResolver()
        vocab = {"person": {"name": "Bob", "age": 30}}
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["person_name"] == "Bob"
        assert result["person_age"] == 30

    def test_expand_person_with_pronouns(self) -> None:
        """Test expanding person with pronouns."""
        resolver = TemplateResolver()
        vocab = {
            "person": {
                "name": "Alice",
                "subject": "she",
                "object": "her",
                "possessive": "her",
                "reflexive": "herself",
                "verb_s": "s",
            }
        }
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["name"] == "Alice"
        assert result["subject"] == "she"
        assert result["subj"] == "She"
        assert result["his_her"] == "her"
        assert result["him_her"] == "her"
        assert result["reflexive"] == "herself"
        assert result["verb_s"] == "s"

    def test_expand_person_numbered(self) -> None:
        """Test expanding numbered person (person1, person2)."""
        resolver = TemplateResolver()
        vocab = {
            "person1": {
                "name": "Bob",
                "subject": "he",
                "possessive": "his",
            }
        }
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["name1"] == "Bob"
        assert result["subject1"] == "he"
        assert result["subj1"] == "He"
        assert result["his_her1"] == "his"

    def test_expand_person2(self) -> None:
        """Test expanding person2."""
        resolver = TemplateResolver()
        vocab = {
            "person2": {
                "name": "Carol",
                "subject": "she",
                "possessive": "her",
            }
        }
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["name2"] == "Carol"
        assert result["subject2"] == "she"
        assert result["subj2"] == "She"
        assert result["his_her2"] == "her"

    def test_expand_list_vocab(self) -> None:
        """Test expanding list-type vocab."""
        resolver = TemplateResolver()
        vocab = {"items": ["apple", "banana", "cherry"]}
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["items_0"] == "apple"
        assert result["items_1"] == "banana"
        assert result["items_2"] == "cherry"

    def test_expand_scalar_vocab(self) -> None:
        """Test expanding scalar vocab."""
        resolver = TemplateResolver()
        vocab = {"item": "book", "count": 5}
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["item"] == "book"
        assert result["count"] == 5

    def test_expand_dict_without_person_keys(self) -> None:
        """Test expanding dict without name/subject keys."""
        resolver = TemplateResolver()
        vocab = {"config": {"key1": "value1", "key2": "value2"}}
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["config_key1"] == "value1"
        assert result["config_key2"] == "value2"
        # Should not have person shortcuts
        assert "name" not in result
        assert "subject" not in result

    def test_expand_person_without_verb_s(self) -> None:
        """Test expanding person without verb_s key."""
        resolver = TemplateResolver()
        vocab = {
            "person": {
                "name": "Alex",
                "subject": "they",
                "object": "them",
                "possessive": "their",
                "reflexive": "themselves",
            }
        }
        result: dict[str, Any] = {}
        resolver._expand_vocab_items(result, vocab)
        assert result["name"] == "Alex"
        assert result["verb_s"] == "s"  # default from .get()
