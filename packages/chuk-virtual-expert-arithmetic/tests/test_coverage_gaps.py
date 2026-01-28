"""Tests to improve coverage for vocab, schemas, and composition modules."""

from __future__ import annotations

import pytest

# =============================================================================
# SCHEMAS MODULE TESTS
# =============================================================================


class TestSchemasModule:
    """Tests for schemas/__init__.py."""

    def test_list_schemas_returns_list(self):
        from chuk_virtual_expert_arithmetic.schemas import list_schemas

        schemas = list_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0

    def test_list_schemas_contains_known_schemas(self):
        from chuk_virtual_expert_arithmetic.schemas import list_schemas

        schemas = list_schemas()
        # Should contain schemas from different expert types
        assert "price_chain" in schemas
        assert "entity_simple_transfer" in schemas

    def test_list_schemas_by_expert_returns_dict(self):
        from chuk_virtual_expert_arithmetic.schemas import list_schemas_by_expert

        by_expert = list_schemas_by_expert()
        assert isinstance(by_expert, dict)
        assert "arithmetic" in by_expert
        assert "entity_track" in by_expert
        assert "percentage" in by_expert

    def test_list_schemas_by_expert_has_schemas(self):
        from chuk_virtual_expert_arithmetic.schemas import list_schemas_by_expert

        by_expert = list_schemas_by_expert()
        for expert, schemas in by_expert.items():
            assert isinstance(schemas, list)
            assert len(schemas) > 0, f"Expert {expert} has no schemas"


# =============================================================================
# VOCAB MODULE TESTS
# =============================================================================


class TestVocabModule:
    """Tests for vocab/__init__.py."""

    def test_vocab_singleton(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        v1 = Vocab()
        v2 = Vocab()
        assert v1 is v2  # Singleton pattern

    def test_get_vocab_convenience(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab, get_vocab

        vocab = get_vocab()
        assert isinstance(vocab, Vocab)

    def test_vocab_get_valid_path(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        names = vocab.get("names")
        assert names is not None
        assert isinstance(names, dict)

    def test_vocab_get_invalid_path(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.get("nonexistent.path.here")
        assert result is None

    def test_vocab_get_partial_path(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Test getting a nested path
        result = vocab.get("names.male")
        assert result is not None
        assert isinstance(result, list)

    def test_vocab_random_returns_item(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        name = vocab.random("names.male")
        assert name is not None
        assert isinstance(name, str)

    def test_vocab_random_invalid_path(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.random("nonexistent.path")
        assert result is None

    def test_vocab_sample_returns_list(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        samples = vocab.sample("names.male", k=3)
        assert isinstance(samples, list)
        assert len(samples) == 3

    def test_vocab_sample_invalid_path(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.sample("nonexistent.path", k=2)
        assert result == []

    def test_vocab_substitute(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.substitute("Hello ${name}, you have ${count} items", name="Alice", count=5)
        assert result == "Hello Alice, you have 5 items"

    def test_vocab_pattern_valid(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Pattern should return a filled template
        result = vocab.pattern("price_chain", count=3, item="apples", price=5)
        # Even if template vars don't all match, should return something
        assert isinstance(result, str)

    def test_vocab_pattern_invalid(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.pattern("nonexistent_pattern")
        assert result == ""

    def test_vocab_pattern_with_variant(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Test pattern with variant - may return empty if variant doesn't exist
        result = vocab.pattern("price_chain", variant="default")
        assert isinstance(result, str)

    def test_vocab_random_pair_valid(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Test with containers.paired if it exists
        first, second = vocab.random_pair("containers.paired")
        # May be None if path doesn't exist
        assert first is None or isinstance(first, str)

    def test_vocab_random_pair_invalid(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        first, second = vocab.random_pair("nonexistent.path")
        assert first is None
        assert second is None

    def test_vocab_all_keys(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        keys = vocab.all_keys()
        assert isinstance(keys, list)
        assert "names" in keys
        assert "items" in keys

    def test_vocab_list_paths_no_prefix(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        paths = vocab.list_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0

    def test_vocab_list_paths_with_prefix(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        paths = vocab.list_paths("names")
        assert isinstance(paths, list)
        # Should have paths like "names.male", "names.female", etc.
        assert any("names." in p for p in paths)

    def test_vocab_list_paths_invalid_prefix(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        paths = vocab.list_paths("nonexistent")
        assert paths == []

    def test_vocab_colored_material(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.colored_material("fabrics")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_vocab_colored_material_fallback(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Test with invalid material type - should return fallback
        result = vocab.colored_material("nonexistent_type")
        assert isinstance(result, str)

    def test_vocab_labeled_container_letters(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.labeled_container(use_words=False)
        assert isinstance(result, str)
        # Should be something like "Tank A"

    def test_vocab_labeled_container_words(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.labeled_container(use_words=True)
        assert isinstance(result, str)
        # Should be something like "the first tank"

    def test_vocab_container_pair_letters(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        first, second = vocab.container_pair(use_words=False)
        assert isinstance(first, str)
        assert isinstance(second, str)
        assert first != second

    def test_vocab_container_pair_words(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        first, second = vocab.container_pair(use_words=True)
        assert isinstance(first, str)
        assert isinstance(second, str)

    def test_vocab_container_pair_random(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # use_words=None should randomly choose
        first, second = vocab.container_pair(use_words=None)
        assert isinstance(first, str)
        assert isinstance(second, str)

    def test_vocab_material_pair(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        first, second = vocab.material_pair("fabrics")
        assert isinstance(first, str)
        assert isinstance(second, str)

    def test_vocab_farm_animal_context(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        context = vocab.farm_animal_context()
        assert isinstance(context, dict)
        assert "name" in context or "singular" in context

    def test_vocab_conjugate(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        verb_data = {"base": "eat", "s": "eats", "rest": "for ${meal}"}
        result = vocab.conjugate(verb_data, use_singular=True, meal="breakfast")
        assert "eats" in result
        assert "breakfast" in result

    def test_vocab_conjugate_plural(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        verb_data = {"base": "eat", "s": "eats", "rest": "daily"}
        result = vocab.conjugate(verb_data, use_singular=False)
        assert "eat" in result

    def test_vocab_conjugate_no_rest(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        verb_data = {"base": "run", "s": "runs"}
        result = vocab.conjugate(verb_data, use_singular=True)
        assert result == "runs"

    def test_vocab_conjugate_invalid(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        result = vocab.conjugate(None, use_singular=True)
        assert result == "does"

    def test_vocab_person_with_pronouns(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        person = vocab.person_with_pronouns()
        assert isinstance(person, dict)
        assert "name" in person
        assert "subject" in person
        assert "object" in person
        assert "possessive" in person

    def test_vocab_activity_context(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        activity = vocab.activity_context()
        assert isinstance(activity, dict)

    def test_vocab_a_an_vowel(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        assert vocab.a_an("apple") == "an"
        assert vocab.a_an("orange") == "an"
        assert vocab.a_an("egg") == "an"

    def test_vocab_a_an_consonant(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        assert vocab.a_an("book") == "a"
        assert vocab.a_an("cat") == "a"
        assert vocab.a_an("dog") == "a"

    def test_vocab_a_an_empty(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        assert vocab.a_an("") == "a"

    def test_vocab_with_article(self):
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        assert vocab.with_article("apple") == "an apple"
        assert vocab.with_article("book") == "a book"

    def test_vocab_get_non_dict_intermediate(self):
        """Test get() when path traverses through a non-dict."""
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Try to get a path that goes through a list (should return None)
        # names.male is a list, so names.male.something should return None
        result = vocab.get("names.male.nonexistent")
        assert result is None

    def test_vocab_pattern_non_templates_dict(self):
        """Test pattern() with a pattern that has variants but no templates key."""
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Try various patterns to exercise branches
        # Some patterns may have different structures
        result1 = vocab.pattern("price_chain", variant="nonexistent_variant")
        assert isinstance(result1, str)

    def test_vocab_list_paths_with_list_data(self):
        """Test list_paths when the prefix points to a list, not a dict."""
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # If we get paths for something that resolves to a list
        # This should return an empty list since lists don't have .keys()
        # First, find something that's a list in the cache
        paths = vocab.list_paths("colors")  # colors should have nested structure
        assert isinstance(paths, list)

    def test_vocab_random_returns_dict(self):
        """Test random() on a path that returns dicts (like farm_animals)."""
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # animals.farm_animals contains dicts
        animal = vocab.random("animals.farm_animals")
        if animal:
            assert isinstance(animal, dict)

    def test_vocab_sample_larger_than_list(self):
        """Test sample() when k is larger than list size."""
        from chuk_virtual_expert_arithmetic.vocab import Vocab

        vocab = Vocab()
        # Sample more items than exist - should return all available
        samples = vocab.sample("colors.basic", k=100)
        assert len(samples) <= 100
        assert len(samples) > 0


# =============================================================================
# COMPOSITION MODULE TESTS
# =============================================================================


class TestCompositionModule:
    """Tests for composition.py - ensure all generators are covered."""

    def test_generate_percent_off_plus_extra(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_percent_off_plus_extra,
        )

        result = generate_percent_off_plus_extra()
        assert result["composed"] is True
        assert "query" in result
        assert "steps" in result
        assert "answer" in result
        assert len(result["steps"]) == 2
        assert result["steps"][0]["expert"] == "percentage"
        assert result["steps"][1]["expert"] == "arithmetic"

    def test_generate_percent_increase_minus_cost(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_percent_increase_minus_cost,
        )

        result = generate_percent_increase_minus_cost()
        assert result["composed"] is True
        assert len(result["steps"]) == 2

    def test_generate_percent_of_then_multiply(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_percent_of_then_multiply,
        )

        result = generate_percent_of_then_multiply()
        assert result["composed"] is True
        assert len(result["steps"]) == 2

    def test_generate_rate_then_subtract(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_rate_then_subtract,
        )

        result = generate_rate_then_subtract()
        assert result["composed"] is True
        assert result["steps"][0]["expert"] == "rate_equation"

    def test_generate_value_increase_profit(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_value_increase_profit,
        )

        result = generate_value_increase_profit()
        assert result["composed"] is True
        assert len(result["steps"]) == 2

    def test_generate_paired_discount(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_paired_discount,
        )

        result = generate_paired_discount()
        assert result["composed"] is True

    def test_generate_interrupted_rate(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_interrupted_rate,
        )

        result = generate_interrupted_rate()
        assert result["composed"] is True

    def test_generate_consume_then_sell(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_consume_then_sell,
        )

        result = generate_consume_then_sell()
        assert result["composed"] is True
        assert result["steps"][0]["expert"] == "entity_track"
        assert result["steps"][1]["expert"] == "arithmetic"

    def test_generate_cost_increase_profit(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_cost_increase_profit,
        )

        result = generate_cost_increase_profit()
        assert result["composed"] is True
        assert len(result["steps"]) == 3  # 3-expert chain

    def test_generate_comparison_then_total(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_comparison_then_total,
        )

        result = generate_comparison_then_total()
        assert result["composed"] is True
        assert len(result["steps"]) == 3

    def test_generate_rate_comparison_total(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_rate_comparison_total,
        )

        result = generate_rate_comparison_total()
        assert result["composed"] is True
        assert len(result["steps"]) == 3

    def test_generate_discount_tax_total(self):
        from chuk_virtual_expert_arithmetic.generators.composition import (
            generate_discount_tax_total,
        )

        result = generate_discount_tax_total()
        assert result["composed"] is True
        assert len(result["steps"]) == 3

    def test_generate_function(self):
        from chuk_virtual_expert_arithmetic.generators.composition import generate

        results = generate(n=20)
        assert len(results) == 20
        for result in results:
            assert result["composed"] is True
            assert "query" in result
            assert "answer" in result

    def test_generators_list_complete(self):
        from chuk_virtual_expert_arithmetic.generators.composition import GENERATORS

        # Ensure all generators are in the list
        assert len(GENERATORS) == 12


# =============================================================================
# GENERATORS __init__.py ADDITIONAL TESTS
# =============================================================================


class TestGeneratorsInit:
    """Additional tests for generators/__init__.py."""

    def test_generate_from_schemas_default(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_from_schemas(n=10)
        assert len(examples) == 10

    def test_generate_from_schemas_specific(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_from_schemas(n=5, schema_names=["price_chain"])
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "arithmetic"

    def test_generate_comparison(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_comparison(n=5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "comparison"

    def test_generate_percentage(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_percentage(n=5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "percentage"

    def test_generate_all(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_all(n_per_type=3)
        # 5 expert types × 3 = 15 examples
        assert len(examples) == 15

    def test_generate_composition(self):
        from chuk_virtual_expert_arithmetic.generators import TraceGenerator

        gen = TraceGenerator(seed=42)
        examples = gen.generate_composition(n=5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["composed"] is True


# =============================================================================
# SCHEMA_GENERATOR ADDITIONAL TESTS
# =============================================================================


class TestSchemaGeneratorCoverage:
    """Additional tests for schema_generator.py edge cases."""

    def test_generate_batch_empty_schemas(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Empty schema list raises IndexError from random.choice
        with pytest.raises(IndexError):
            gen.generate_batch([], n=5)

    def test_schema_names_property(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        names = gen.schema_names
        assert isinstance(names, list)
        assert len(names) > 0

    def test_generate_single_schema(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        example = gen.generate("price_chain")
        assert example is not None
        assert example.expert == "arithmetic"

    def test_generate_invalid_schema(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Invalid schema raises ValueError
        with pytest.raises(ValueError, match="Unknown schema"):
            gen.generate("nonexistent_schema_xyz")

    def test_generate_batch_default(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Generate batch with default (all schemas)
        examples = gen.generate_batch(n=5)
        assert len(examples) == 5

    def test_word_number_conversion(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator(word_number_prob=1.0)  # 100% conversion
        # Generate a lot to exercise word number conversion
        for _ in range(20):
            ex = gen.generate("price_chain")
            assert ex.query  # Just ensure no errors

    def test_word_number_disabled(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator(word_number_prob=0.0)  # No conversion
        for _ in range(10):
            ex = gen.generate("price_chain")
            assert ex.query

    def test_generate_with_float_variable(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # price_chain has float tax
        ex = gen.generate("price_chain")
        assert ex.answer is not None

    def test_generate_with_choice_variable(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # percent_off has choice type for percent
        ex = gen.generate("percent_off")
        assert ex.answer is not None

    def test_generate_with_derived_variables(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # comparison_sum_diff has derived variables
        ex = gen.generate("comparison_sum_diff")
        assert ex.answer is not None

    def test_generate_with_constraints(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # entity_simple_transfer has constraints
        ex = gen.generate("entity_simple_transfer")
        assert ex.answer is not None

    def test_generate_entity_track_schemas(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        for schema in [
            "entity_simple_transfer",
            "entity_consume_sequence",
            "entity_consume_multiply",
        ]:
            ex = gen.generate(schema)
            assert ex.expert == "entity_track"

    def test_generate_rate_equation_schemas(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        for schema in ["rate_distance", "rate_earning"]:
            ex = gen.generate(schema)
            assert ex.expert == "rate_equation"

    def test_generate_comparison_schemas(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        for schema in ["comparison_times_more", "comparison_sum_diff"]:
            ex = gen.generate(schema)
            assert ex.expert == "comparison"

    def test_generate_percentage_schemas(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        for schema in ["percent_off", "percent_increase", "percent_simple"]:
            ex = gen.generate(schema)
            assert ex.expert == "percentage"


class TestSchemaGeneratorConvenienceFunctions:
    """Test convenience functions in schema_generator."""

    def test_generate_from_schema_function(self):
        from chuk_virtual_expert_arithmetic.generators.schema_generator import generate_from_schema

        ex = generate_from_schema("price_chain")
        assert ex is not None
        assert ex.expert == "arithmetic"

    def test_generate_batch_from_schemas_function(self):
        from chuk_virtual_expert_arithmetic.generators.schema_generator import (
            generate_batch_from_schemas,
        )

        examples = generate_batch_from_schemas(n=5)
        assert len(examples) == 5


class TestSchemaGeneratorTransforms:
    """Test transform operations in schema_generator."""

    def test_pluralize_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test pluralize via _apply_transform
        assert gen._apply_transform("dog", "pluralize") == "dogs"
        assert gen._apply_transform("box", "pluralize") == "boxes"
        assert gen._apply_transform("match", "pluralize") == "matches"
        assert gen._apply_transform("dish", "pluralize") == "dishes"
        assert gen._apply_transform("baby", "pluralize") == "babies"
        assert gen._apply_transform("key", "pluralize") == "keys"

    def test_singularize_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        assert gen._apply_transform("babies", "singularize") == "baby"
        assert gen._apply_transform("boxes", "singularize") == "box"
        assert gen._apply_transform("dogs", "singularize") == "dog"

    def test_capitalize_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        assert gen._apply_transform("hello", "capitalize") == "Hello"

    def test_with_article_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        result = gen._apply_transform("apple", "with_article")
        assert result == "an apple"
        result = gen._apply_transform("book", "with_article")
        assert result == "a book"

    def test_has_have_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        assert gen._apply_transform("s", "has_have") == "has"
        assert gen._apply_transform("", "has_have") == "have"

    def test_does_do_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        assert gen._apply_transform("s", "does_do") == "does"
        assert gen._apply_transform("", "does_do") == "do"

    def test_none_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        assert gen._apply_transform(None, "pluralize") is None

    def test_unknown_transform(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Unknown transform returns value unchanged
        assert gen._apply_transform("test", "unknown_transform") == "test"


class TestSchemaGeneratorInternals:
    """Test internal methods of SchemaGenerator."""

    def test_compute_derived_with_exception(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test derived with expression that causes exception
        derived = gen._compute_derived({"bad": "undefined_var + 1"}, {"x": 10})
        assert derived["bad"] == 0  # Falls back to 0

    def test_generate_variables_multiple_of(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test variable with multiple_of constraint
        for _ in range(10):
            vars = gen._generate_variables(
                {"n": {"type": "int", "min": 1, "max": 20, "multiple_of": 5}}
            )
            assert vars["n"] % 5 == 0

    def test_sample_vocab_choice_type(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test vocab with choice type
        items = gen._sample_vocab({"word": {"type": "choice", "values": ["one", "two", "three"]}})
        assert items["word"] in ["one", "two", "three"]

    def test_sample_vocab_empty_choice(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        items = gen._sample_vocab({"word": {"type": "choice", "values": []}})
        assert items["word"] == ""

    def test_build_template_vars_list_index(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test resolving list index in template spec
        result = gen._resolve_template_spec("items.0", {}, {"items": ["first", "second", "third"]})
        assert result == "first"

    def test_build_template_vars_invalid_list_index(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        # Test resolving invalid list index
        result = gen._resolve_template_spec("items.99", {}, {"items": ["first", "second"]})
        assert result is None

    def test_resolve_template_spec_with_pipe(self):
        from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

        gen = SchemaGenerator()
        result = gen._resolve_template_spec("word|capitalize", {"word": "hello"}, {})
        assert result == "Hello"
