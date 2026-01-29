"""Additional tests for Vocab - comprehensive coverage."""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.vocab import Vocab, get_vocab


class TestVocabSingleton:
    """Tests for Vocab singleton behavior."""

    def test_singleton_instance(self) -> None:
        """Test that Vocab is a singleton."""
        vocab1 = Vocab()
        vocab2 = Vocab()
        assert vocab1 is vocab2

    def test_get_vocab_returns_singleton(self) -> None:
        """Test get_vocab returns singleton."""
        vocab = get_vocab()
        assert vocab is Vocab()


class TestVocabGet:
    """Tests for get method."""

    def test_get_nonexistent_path(self) -> None:
        """Test get with nonexistent path."""
        vocab = Vocab()
        result = vocab.get("nonexistent.path.here")
        assert result is None

    def test_get_non_dict_traversal(self) -> None:
        """Test get when path tries to traverse non-dict."""
        vocab = Vocab()
        # Try to go through a list value (should return None)
        result = vocab.get("names.male.0")  # names.male is a list
        assert result is None


class TestVocabRandom:
    """Tests for random method."""

    def test_random_nonexistent_path(self) -> None:
        """Test random with nonexistent path."""
        vocab = Vocab()
        result = vocab.random("nonexistent.path")
        assert result is None

    def test_random_returns_item(self) -> None:
        """Test random returns an item."""
        vocab = Vocab()
        result = vocab.random("names.male")
        assert result is not None
        assert isinstance(result, str)


class TestVocabSample:
    """Tests for sample method."""

    def test_sample_returns_items(self) -> None:
        """Test sample returns correct number of items."""
        vocab = Vocab()
        result = vocab.sample("names.male", 3)
        assert len(result) <= 3
        assert all(isinstance(r, str) for r in result)

    def test_sample_nonexistent_path(self) -> None:
        """Test sample with nonexistent path."""
        vocab = Vocab()
        result = vocab.sample("nonexistent.path", 3)
        assert result == []


class TestVocabSubstitute:
    """Tests for substitute method."""

    def test_substitute_single_var(self) -> None:
        """Test substituting single variable."""
        vocab = Vocab()
        result = vocab.substitute("Hello ${name}!", name="World")
        assert result == "Hello World!"

    def test_substitute_multiple_vars(self) -> None:
        """Test substituting multiple variables."""
        vocab = Vocab()
        result = vocab.substitute("${a} and ${b}", a="X", b="Y")
        assert result == "X and Y"


class TestVocabPattern:
    """Tests for pattern method."""

    def test_pattern_nonexistent(self) -> None:
        """Test pattern with nonexistent pattern."""
        vocab = Vocab()
        result = vocab.pattern("nonexistent_pattern_xyz")
        assert result == ""

    def test_pattern_with_variant(self) -> None:
        """Test pattern with variant."""
        vocab = Vocab()
        # This test works with any pattern that has variants
        result = vocab.pattern("multiply_add")
        assert isinstance(result, str)

    def test_pattern_empty_templates(self) -> None:
        """Test pattern returns empty for empty templates."""
        vocab = Vocab()
        # Request a non-existent variant
        result = vocab.pattern("multiply_add", variant="nonexistent_variant_xyz")
        # Should return empty or the default templates
        assert isinstance(result, str)


class TestVocabSelectWeightedTemplate:
    """Tests for _select_weighted_template method."""

    def test_select_from_non_list(self) -> None:
        """Test selecting from non-list returns string."""
        vocab = Vocab()
        result = vocab._select_weighted_template("single template")
        assert result == "single template"

    def test_select_from_empty_list(self) -> None:
        """Test selecting from empty list returns empty."""
        vocab = Vocab()
        result = vocab._select_weighted_template([])
        assert result == ""

    def test_select_from_weighted_templates(self) -> None:
        """Test selecting from weighted templates."""
        vocab = Vocab()
        templates = [
            {"text": "template1", "weight": 10},
            {"text": "template2", "weight": 1},
        ]
        result = vocab._select_weighted_template(templates)
        assert result in ["template1", "template2"]


class TestVocabRandomPair:
    """Tests for random_pair method."""

    def test_random_pair_nonexistent(self) -> None:
        """Test random_pair with nonexistent path."""
        vocab = Vocab()
        first, second = vocab.random_pair("nonexistent.path")
        assert first is None
        assert second is None

    def test_random_pair_dict_item(self) -> None:
        """Test random_pair when item is dict with first/second keys."""
        vocab = Vocab()
        # Temporarily add test data with proper pair structure
        original = vocab._cache.copy()
        vocab._cache["test_pairs"] = [
            {"first": "value_a", "second": "value_b"},
            {"first": "value_x", "second": "value_y"},
        ]
        try:
            first, second = vocab.random_pair("test_pairs")
            assert first is not None
            assert second is not None
            assert first in ["value_a", "value_x"]
            assert second in ["value_b", "value_y"]
        finally:
            vocab._cache = original


class TestVocabAllKeys:
    """Tests for all_keys method."""

    def test_all_keys_returns_list(self) -> None:
        """Test all_keys returns list of keys."""
        vocab = Vocab()
        keys = vocab.all_keys()
        assert isinstance(keys, list)
        # Should have at least names, items, patterns
        assert "names" in keys


class TestVocabListPaths:
    """Tests for list_paths method."""

    def test_list_paths_no_prefix(self) -> None:
        """Test list_paths without prefix returns all keys."""
        vocab = Vocab()
        paths = vocab.list_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0

    def test_list_paths_with_prefix(self) -> None:
        """Test list_paths with prefix."""
        vocab = Vocab()
        paths = vocab.list_paths("names")
        assert isinstance(paths, list)
        assert all(p.startswith("names.") for p in paths)

    def test_list_paths_nonexistent_prefix(self) -> None:
        """Test list_paths with nonexistent prefix."""
        vocab = Vocab()
        paths = vocab.list_paths("nonexistent_prefix")
        assert paths == []


class TestVocabColoredMaterial:
    """Tests for colored_material method."""

    def test_colored_material_default(self) -> None:
        """Test colored_material with default type."""
        vocab = Vocab()
        result = vocab.colored_material()
        assert isinstance(result, str)

    def test_colored_material_fallback(self) -> None:
        """Test colored_material with nonexistent type falls back."""
        vocab = Vocab()
        result = vocab.colored_material("nonexistent_type")
        # Should fallback to "material"
        assert isinstance(result, str)


class TestVocabLabeledContainer:
    """Tests for labeled_container method."""

    def test_labeled_container_words(self) -> None:
        """Test labeled_container with word ordinals."""
        vocab = Vocab()
        result = vocab.labeled_container(use_words=True)
        assert "the" in result.lower()

    def test_labeled_container_letters(self) -> None:
        """Test labeled_container with letter ordinals."""
        vocab = Vocab()
        result = vocab.labeled_container(use_words=False)
        assert isinstance(result, str)


class TestVocabContainerPair:
    """Tests for container_pair method."""

    def test_container_pair_random(self) -> None:
        """Test container_pair with random selection."""
        vocab = Vocab()
        first, second = vocab.container_pair()
        assert isinstance(first, str)
        assert isinstance(second, str)
        assert first != second

    def test_container_pair_words(self) -> None:
        """Test container_pair with word ordinals."""
        vocab = Vocab()
        first, second = vocab.container_pair(use_words=True)
        assert "the" in first.lower()
        assert "the" in second.lower()

    def test_container_pair_letters(self) -> None:
        """Test container_pair with letter ordinals."""
        vocab = Vocab()
        first, second = vocab.container_pair(use_words=False)
        assert isinstance(first, str)
        assert isinstance(second, str)


class TestVocabMaterialPair:
    """Tests for material_pair method."""

    def test_material_pair(self) -> None:
        """Test material_pair returns two materials."""
        vocab = Vocab()
        first, second = vocab.material_pair()
        assert isinstance(first, str)
        assert isinstance(second, str)


class TestVocabFarmAnimalContext:
    """Tests for farm_animal_context method."""

    def test_farm_animal_context(self) -> None:
        """Test farm_animal_context returns dict."""
        vocab = Vocab()
        result = vocab.farm_animal_context()
        assert isinstance(result, dict)
        assert "name" in result or "singular" in result


class TestVocabConjugate:
    """Tests for conjugate method."""

    def test_conjugate_singular(self) -> None:
        """Test conjugate with singular."""
        vocab = Vocab()
        verb_data = {"base": "eat", "s": "eats", "rest": "for ${meal}"}
        result = vocab.conjugate(verb_data, use_singular=True, meal="breakfast")
        assert "eats" in result
        assert "breakfast" in result

    def test_conjugate_plural(self) -> None:
        """Test conjugate with plural."""
        vocab = Vocab()
        verb_data = {"base": "eat", "s": "eats", "rest": ""}
        result = vocab.conjugate(verb_data, use_singular=False)
        assert result == "eat"

    def test_conjugate_none(self) -> None:
        """Test conjugate with None verb_data."""
        vocab = Vocab()
        result = vocab.conjugate(None, use_singular=True)
        assert result == "does"


class TestVocabPersonWithPronouns:
    """Tests for person_with_pronouns method."""

    def test_person_with_pronouns_returns_dict(self) -> None:
        """Test person_with_pronouns returns proper dict."""
        vocab = Vocab()
        result = vocab.person_with_pronouns()
        assert isinstance(result, dict)
        assert "name" in result
        assert "subject" in result
        assert "object" in result
        assert "possessive" in result
        assert "reflexive" in result
        assert "verb_s" in result


class TestVocabActivityContext:
    """Tests for activity_context method."""

    def test_activity_context_returns_dict(self) -> None:
        """Test activity_context returns dict with expected keys."""
        vocab = Vocab()
        result = vocab.activity_context()
        assert isinstance(result, dict)


class TestVocabArticles:
    """Tests for a_an and with_article methods."""

    def test_a_an_vowel(self) -> None:
        """Test a_an with vowel."""
        vocab = Vocab()
        assert vocab.a_an("apple") == "an"
        assert vocab.a_an("elephant") == "an"

    def test_a_an_consonant(self) -> None:
        """Test a_an with consonant."""
        vocab = Vocab()
        assert vocab.a_an("book") == "a"
        assert vocab.a_an("car") == "a"

    def test_a_an_empty(self) -> None:
        """Test a_an with empty string."""
        vocab = Vocab()
        assert vocab.a_an("") == "a"

    def test_with_article(self) -> None:
        """Test with_article."""
        vocab = Vocab()
        assert vocab.with_article("apple") == "an apple"
        assert vocab.with_article("book") == "a book"


class TestVocabPatternEdgeCases:
    """Tests for pattern method edge cases."""

    def test_pattern_dict_without_templates_key(self) -> None:
        """Test pattern that is dict but has no templates key and no matching variant."""
        vocab = Vocab()
        # Temporarily add a pattern with variants but no "templates" key
        original = vocab._cache.get("patterns", {}).copy()
        vocab._cache["patterns"] = vocab._cache.get("patterns", {}).copy()
        vocab._cache["patterns"]["test_pattern"] = {
            "variant_a": ["Template A ${var}"],
            "variant_b": ["Template B ${var}"],
        }
        try:
            # Request non-existent variant with no "templates" fallback
            result = vocab.pattern("test_pattern", variant="nonexistent")
            assert result == ""

            # Request variant that exists
            result = vocab.pattern("test_pattern", variant="variant_a", var="test")
            assert "Template A test" in result
        finally:
            vocab._cache["patterns"] = original

    def test_pattern_direct_list(self) -> None:
        """Test pattern that is directly a list, not a dict."""
        vocab = Vocab()
        original = vocab._cache.get("patterns", {}).copy()
        vocab._cache["patterns"] = vocab._cache.get("patterns", {}).copy()
        vocab._cache["patterns"]["direct_list_pattern"] = [
            "Template 1 with ${x}",
            "Template 2 with ${x}",
        ]
        try:
            result = vocab.pattern("direct_list_pattern", x="value")
            assert "value" in result
        finally:
            vocab._cache["patterns"] = original


class TestVocabFallbackPaths:
    """Tests for fallback paths in Vocab methods."""

    def test_random_pair_non_dict_item(self) -> None:
        """Test random_pair when item is not a dict."""
        vocab = Vocab()
        # Temporarily add test data
        original = vocab._cache.copy()
        vocab._cache["test_items"] = ["string_item1", "string_item2"]
        try:
            first, second = vocab.random_pair("test_items")
            # When item is not a dict, should return None, None
            assert first is None
            assert second is None
        finally:
            vocab._cache = original

    def test_list_paths_non_dict_data(self) -> None:
        """Test list_paths when prefix data is not a dict."""
        vocab = Vocab()
        # Temporarily add a list at top level
        original = vocab._cache.copy()
        vocab._cache["list_data"] = ["item1", "item2", "item3"]
        try:
            paths = vocab.list_paths("list_data")
            assert paths == []
        finally:
            vocab._cache = original

    def test_labeled_container_missing_container(self) -> None:
        """Test labeled_container when containers.types is missing."""
        vocab = Vocab()
        original_containers = vocab._cache.get("containers", {}).copy()
        vocab._cache["containers"] = {}
        try:
            result = vocab.labeled_container(use_words=False)
            # Should use fallback "container"
            assert "container" in result.lower()
        finally:
            vocab._cache["containers"] = original_containers

    def test_container_pair_missing_pair_data_words(self) -> None:
        """Test container_pair fallback when ordinals.word_pairs returns None."""
        vocab = Vocab()
        original_ordinals = vocab._cache.get("ordinals", {}).copy()
        vocab._cache["ordinals"] = {}
        try:
            first, second = vocab.container_pair(use_words=True)
            # Should use fallback values
            assert "first" in first.lower()
            assert "second" in second.lower()
        finally:
            vocab._cache["ordinals"] = original_ordinals

    def test_container_pair_missing_pair_data_letters(self) -> None:
        """Test container_pair fallback when ordinals.letter_pairs returns None."""
        vocab = Vocab()
        original_ordinals = vocab._cache.get("ordinals", {}).copy()
        vocab._cache["ordinals"] = {}
        try:
            first, second = vocab.container_pair(use_words=False)
            # Should use fallback A/B values
            assert "A" in first or "B" in first
        finally:
            vocab._cache["ordinals"] = original_ordinals

    def test_material_pair_few_colors(self) -> None:
        """Test material_pair when sample returns fewer than 2 colors."""
        vocab = Vocab()
        original_colors = vocab._cache.get("colors", {}).copy()
        vocab._cache["colors"] = {"basic": ["red"]}  # Only one color
        try:
            first, second = vocab.material_pair()
            # Should use fallback "type A/B"
            assert "type A" in first or "red" in first
            assert "type B" in second or "red" in second
        finally:
            vocab._cache["colors"] = original_colors

    def test_farm_animal_context_missing_data(self) -> None:
        """Test farm_animal_context when data is missing."""
        vocab = Vocab()
        original_animals = vocab._cache.get("animals", {}).copy()
        vocab._cache["animals"] = {}
        try:
            result = vocab.farm_animal_context()
            # Should return fallback dict
            assert result["name"] == "chickens"
            assert result["singular"] == "chicken"
            assert result["produces"] == "eggs"
        finally:
            vocab._cache["animals"] = original_animals

    def test_farm_animal_context_string_data(self) -> None:
        """Test farm_animal_context when animal is a string, not dict."""
        vocab = Vocab()
        original_animals = vocab._cache.get("animals", {}).copy()
        vocab._cache["animals"] = {"farm_animals": ["chicken", "cow"]}
        try:
            result = vocab.farm_animal_context()
            # Should return fallback dict since items are strings
            assert result["name"] == "chickens"
        finally:
            vocab._cache["animals"] = original_animals

    def test_person_with_pronouns_missing_data(self) -> None:
        """Test person_with_pronouns when data is missing."""
        vocab = Vocab()
        original_names = vocab._cache.get("names", {}).copy()
        vocab._cache["names"] = {}
        try:
            result = vocab.person_with_pronouns()
            # Should return fallback
            assert result["name"] == "Alex"
            assert result["subject"] == "they"
            assert result["verb_s"] == ""
        finally:
            vocab._cache["names"] = original_names

    def test_activity_context_string_data(self) -> None:
        """Test activity_context when activity is a string, not dict."""
        vocab = Vocab()
        original_phrases = vocab._cache.get("phrases", {}).copy()
        vocab._cache["phrases"] = {"activities": ["run", "walk"]}
        try:
            result = vocab.activity_context()
            # Should return fallback dict since items are strings
            assert result["verb"] == "run"
            assert result["noun"] == "laps"
        finally:
            vocab._cache["phrases"] = original_phrases

    def test_activity_context_missing_data(self) -> None:
        """Test activity_context when data is missing."""
        vocab = Vocab()
        original_phrases = vocab._cache.get("phrases", {}).copy()
        vocab._cache["phrases"] = {}
        try:
            result = vocab.activity_context()
            # Should return fallback dict
            assert result["verb"] == "run"
        finally:
            vocab._cache["phrases"] = original_phrases

    def test_conjugate_with_non_dict(self) -> None:
        """Test conjugate with non-dict verb_data."""
        vocab = Vocab()
        result = vocab.conjugate("not a dict", use_singular=True)
        assert result == "does"

    def test_conjugate_missing_rest(self) -> None:
        """Test conjugate when rest is empty and no kwargs."""
        vocab = Vocab()
        verb_data = {"base": "eat", "s": "eats"}  # No "rest" key
        result = vocab.conjugate(verb_data, use_singular=True)
        assert result == "eats"

    def test_colored_material_no_color_no_material(self) -> None:
        """Test colored_material when both color and material are missing."""
        vocab = Vocab()
        original_colors = vocab._cache.get("colors", {}).copy()
        original_materials = vocab._cache.get("materials", {}).copy()
        vocab._cache["colors"] = {}
        vocab._cache["materials"] = {}
        try:
            result = vocab.colored_material()
            # Should return "material" as fallback
            assert result == "material"
        finally:
            vocab._cache["colors"] = original_colors
            vocab._cache["materials"] = original_materials
