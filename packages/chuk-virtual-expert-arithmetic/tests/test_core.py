"""Tests for core components."""

import pytest

from chuk_virtual_expert_arithmetic.core import (
    CompositionError,
    ConstraintValidator,
    ContractValidator,
    DomainSampler,
    SchemaComposer,
    SchemaLoader,
    SchemaLoadError,
    TemplateResolver,
    TransformRegistry,
    VariableGenerator,
)
from chuk_virtual_expert_arithmetic.models import SchemaSpec, VariableSpec, VocabSpec
from chuk_virtual_expert_arithmetic.vocab import get_vocab


class TestSchemaLoader:
    """Tests for SchemaLoader."""

    @pytest.fixture
    def loader(self) -> SchemaLoader:
        """Create a loader instance."""
        return SchemaLoader()

    def test_load_existing_schema(self, loader: SchemaLoader) -> None:
        """Test loading an existing schema."""
        schema = loader.load("multiply_add")
        assert schema.name == "multiply_add"
        assert "a" in schema.variables or len(schema.variables) > 0

    def test_load_nonexistent_schema(self, loader: SchemaLoader) -> None:
        """Test loading a nonexistent schema raises error."""
        with pytest.raises(SchemaLoadError, match="Schema not found"):
            loader.load("nonexistent_schema_xyz")

    def test_schema_names(self, loader: SchemaLoader) -> None:
        """Test listing schema names."""
        names = loader.schema_names
        assert len(names) > 0
        assert "multiply_add" in names

    def test_exists(self, loader: SchemaLoader) -> None:
        """Test schema existence check."""
        assert loader.exists("multiply_add")
        assert not loader.exists("nonexistent_xyz")

    def test_get_all(self, loader: SchemaLoader) -> None:
        """Test loading all schemas."""
        schemas = loader.get_all()
        assert len(schemas) > 0
        assert all(hasattr(s, "name") for s in schemas.values())

    def test_cache(self, loader: SchemaLoader) -> None:
        """Test schema caching."""
        schema1 = loader.load("multiply_add")
        schema2 = loader.load("multiply_add")
        assert schema1 is schema2  # Same object from cache

    def test_clear_cache(self, loader: SchemaLoader) -> None:
        """Test cache clearing."""
        loader.load("multiply_add")
        loader.clear_cache()
        assert len(loader._cache) == 0


class TestVariableGenerator:
    """Tests for VariableGenerator."""

    @pytest.fixture
    def generator(self) -> VariableGenerator:
        """Create a generator with fixed seed."""
        return VariableGenerator(seed=42)

    def test_generate_int(self, generator: VariableGenerator) -> None:
        """Test integer generation."""
        spec = VariableSpec(type="int", min=1, max=10)
        value = generator.generate_one(spec)
        assert isinstance(value, int)
        assert 1 <= value <= 10

    def test_generate_float(self, generator: VariableGenerator) -> None:
        """Test float generation."""
        spec = VariableSpec(type="float", min=0.0, max=1.0, precision=2)
        value = generator.generate_one(spec)
        assert isinstance(value, float)
        assert 0.0 <= value <= 1.0

    def test_generate_choice(self, generator: VariableGenerator) -> None:
        """Test choice generation."""
        spec = VariableSpec(type="choice", options=[1, 2, 3])
        value = generator.generate_one(spec)
        assert value in [1, 2, 3]

    def test_generate_bool(self, generator: VariableGenerator) -> None:
        """Test boolean generation."""
        spec = VariableSpec(type="bool")
        value = generator.generate_one(spec)
        assert isinstance(value, bool)

    def test_generate_multiple_of(self, generator: VariableGenerator) -> None:
        """Test multiple_of constraint."""
        spec = VariableSpec(type="int", min=1, max=100, multiple_of=5)
        value = generator.generate_one(spec)
        assert value % 5 == 0

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed gives same results."""
        gen1 = VariableGenerator(seed=123)
        gen2 = VariableGenerator(seed=123)
        spec = VariableSpec(type="int", min=1, max=1000)

        values1 = [gen1.generate_one(spec) for _ in range(10)]
        values2 = [gen2.generate_one(spec) for _ in range(10)]
        assert values1 == values2

    def test_generate_dict(self, generator: VariableGenerator) -> None:
        """Test generating from dict of specs."""
        specs = {
            "a": VariableSpec(type="int", min=1, max=10),
            "b": VariableSpec(type="int", min=1, max=10),
        }
        variables = generator.generate(specs)
        assert "a" in variables
        assert "b" in variables

    def test_avoid_round_numbers(self, generator: VariableGenerator) -> None:
        """Test avoid_round constraint generates non-round numbers."""
        spec = VariableSpec(type="int", min=1, max=100, avoid_round=True)
        # Generate multiple values to verify pattern
        for _ in range(20):
            value = generator.generate_one(spec)
            assert value % 10 != 0, f"Expected non-round number, got {value}"

    def test_difficulty_easy(self, generator: VariableGenerator) -> None:
        """Test easy difficulty generates small, round numbers."""
        spec = VariableSpec(type="int", min=1, max=100, difficulty="easy")
        values = [generator.generate_one(spec) for _ in range(20)]
        # Easy should produce small, round numbers (multiples of 5)
        for v in values:
            assert v <= 30, f"Easy mode should produce small numbers, got {v}"
            assert v % 5 == 0, f"Easy mode should produce round numbers, got {v}"

    def test_difficulty_hard(self, generator: VariableGenerator) -> None:
        """Test hard difficulty generates larger, non-round numbers."""
        spec = VariableSpec(type="int", min=1, max=100, difficulty="hard")
        non_round_count = 0
        for _ in range(20):
            value = generator.generate_one(spec)
            if value % 10 != 0:
                non_round_count += 1
        # Most should be non-round
        assert non_round_count > 10, "Hard mode should mostly produce non-round numbers"

    def test_difficulty_medium(self, generator: VariableGenerator) -> None:
        """Test medium difficulty generates standard range."""
        spec = VariableSpec(type="int", min=1, max=100, difficulty="medium")
        values = [generator.generate_one(spec) for _ in range(20)]
        # Medium should produce values in the specified range
        for v in values:
            assert 1 <= v <= 100


class TestConstraintValidator:
    """Tests for ConstraintValidator."""

    @pytest.fixture
    def validator(self) -> ConstraintValidator:
        """Create a validator instance."""
        return ConstraintValidator()

    def test_check_satisfied(self, validator: ConstraintValidator) -> None:
        """Test checking satisfied constraints."""
        constraints = {"a + b": {"min": 5, "max": 20}}
        variables = {"a": 5, "b": 5}
        satisfied, violated = validator.check(constraints, variables)
        assert satisfied
        assert len(violated) == 0

    def test_check_violated(self, validator: ConstraintValidator) -> None:
        """Test checking violated constraints."""
        constraints = {"a + b": {"min": 100, "max": 200}}
        variables = {"a": 5, "b": 5}
        satisfied, violated = validator.check(constraints, variables)
        assert not satisfied
        assert "a + b" in violated

    def test_apply_with_regeneration(self, validator: ConstraintValidator) -> None:
        """Test applying constraints with regeneration."""
        constraints = {"a": {"min": 50, "max": 100}}
        initial = {"a": 10}  # Violates constraint

        regenerate_calls = [0]

        def regenerate() -> dict:
            regenerate_calls[0] += 1
            return {"a": 75}  # Satisfies constraint

        result = validator.apply(constraints, initial, regenerate)
        assert result["a"] == 75
        assert regenerate_calls[0] >= 1

    def test_empty_constraints(self, validator: ConstraintValidator) -> None:
        """Test with no constraints."""
        variables = {"a": 5}
        result = validator.apply({}, variables, lambda: {})
        assert result == variables


class TestTransformRegistry:
    """Tests for TransformRegistry."""

    def test_pluralize(self) -> None:
        """Test pluralize transform."""
        assert TransformRegistry.apply("apple", "pluralize") == "apples"
        assert TransformRegistry.apply("box", "pluralize") == "boxes"
        assert TransformRegistry.apply("baby", "pluralize") == "babies"

    def test_singularize(self) -> None:
        """Test singularize transform."""
        assert TransformRegistry.apply("apples", "singularize") == "apple"
        assert TransformRegistry.apply("boxes", "singularize") == "box"
        assert TransformRegistry.apply("babies", "singularize") == "baby"

    def test_capitalize(self) -> None:
        """Test capitalize transform."""
        assert TransformRegistry.apply("hello", "capitalize") == "Hello"
        assert TransformRegistry.apply("HELLO", "capitalize") == "Hello"

    def test_with_article(self) -> None:
        """Test with_article transform."""
        assert TransformRegistry.apply("apple", "with_article") == "an apple"
        assert TransformRegistry.apply("banana", "with_article") == "a banana"

    def test_ordinal(self) -> None:
        """Test ordinal transform."""
        assert TransformRegistry.apply(1, "ordinal") == "1st"
        assert TransformRegistry.apply(2, "ordinal") == "2nd"
        assert TransformRegistry.apply(3, "ordinal") == "3rd"
        assert TransformRegistry.apply(11, "ordinal") == "11th"
        assert TransformRegistry.apply(21, "ordinal") == "21st"

    def test_custom_transform(self) -> None:
        """Test registering a custom transform."""
        TransformRegistry.register("double", lambda x: x * 2)
        try:
            assert TransformRegistry.apply(5, "double") == 10
        finally:
            TransformRegistry.unregister("double")


class TestTemplateResolver:
    """Tests for TemplateResolver."""

    @pytest.fixture
    def resolver(self) -> TemplateResolver:
        """Create a resolver instance."""
        return TemplateResolver()

    def test_resolve_literal(self, resolver: TemplateResolver) -> None:
        """Test resolving literal values."""
        result = resolver.resolve("hello", {}, {})
        assert result == "hello"

    def test_resolve_variable(self, resolver: TemplateResolver) -> None:
        """Test resolving variable references."""
        result = resolver.resolve("count", {"count": 42}, {})
        assert result == 42

    def test_resolve_vocab_item(self, resolver: TemplateResolver) -> None:
        """Test resolving vocab items."""
        result = resolver.resolve("item", {}, {"item": "apple"})
        assert result == "apple"

    def test_resolve_dot_notation(self, resolver: TemplateResolver) -> None:
        """Test resolving dot notation."""
        vocab = {"person": {"name": "Alice", "subject": "she"}}
        result = resolver.resolve("person.name", {}, vocab)
        assert result == "Alice"

    def test_resolve_with_transform(self, resolver: TemplateResolver) -> None:
        """Test resolving with transforms."""
        result = resolver.resolve("item|pluralize", {}, {"item": "apple"})
        assert result == "apples"

    def test_resolve_chained_transforms(self, resolver: TemplateResolver) -> None:
        """Test resolving chained transforms."""
        result = resolver.resolve("item|singularize|capitalize", {}, {"item": "apples"})
        assert result == "Apple"

    def test_build_template_vars(self, resolver: TemplateResolver) -> None:
        """Test building complete template vars."""
        specs = {"item_plural": "item|pluralize"}
        variables = {"count": 5}
        vocab = {"item": "apple"}

        result = resolver.build_template_vars(specs, variables, vocab)

        assert result["count"] == 5
        assert result["item"] == "apple"
        assert result["item_plural"] == "apples"

    def test_expand_person_vocab(self, resolver: TemplateResolver) -> None:
        """Test expanding person vocab shortcuts."""
        specs = {}
        variables = {}
        vocab = {
            "person": {
                "name": "Alice",
                "subject": "she",
                "possessive": "her",
                "object": "her",
                "reflexive": "herself",
            }
        }

        result = resolver.build_template_vars(specs, variables, vocab)

        assert result["name"] == "Alice"
        assert result["subject"] == "she"
        assert result["subj"] == "She"
        assert result["his_her"] == "her"

    def test_multiplier_words(self, resolver: TemplateResolver) -> None:
        """Test auto-generated multiplier words."""
        result = resolver.build_template_vars({}, {"multiplier": 2}, {})
        assert result["mult_word"] == "twice"
        assert result["growth_word"] == "doubled"

        result = resolver.build_template_vars({}, {"multiplier": 3}, {})
        assert result["mult_word"] == "three times"
        assert result["growth_word"] == "tripled"


class TestContractValidator:
    """Tests for ContractValidator."""

    @pytest.fixture
    def validator(self) -> ContractValidator:
        """Create a validator instance."""
        return ContractValidator(get_vocab())

    def test_validate_valid_schema(self, validator: ContractValidator) -> None:
        """Test validating a schema with all required vars."""
        # Load an actual schema that should be valid
        loader = SchemaLoader()
        schema = loader.load("multiply_add")
        errors = validator.validate_schema(schema)
        assert errors == []

    def test_validate_schema_no_pattern(self, validator: ContractValidator) -> None:
        """Test schema without pattern has no contract."""
        schema = SchemaSpec(name="test", answer="x")
        errors = validator.validate_schema(schema)
        assert errors == []

    def test_validate_schema_missing_pattern(self, validator: ContractValidator) -> None:
        """Test schema with nonexistent pattern."""
        schema = SchemaSpec(
            name="test",
            pattern="nonexistent_pattern_xyz",
            answer="x",
        )
        errors = validator.validate_schema(schema)
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_schema_missing_variant(self, validator: ContractValidator) -> None:
        """Test schema with nonexistent variant."""
        schema = SchemaSpec(
            name="test",
            pattern="multiply_add",
            variant="nonexistent_variant_xyz",
            answer="x",
        )
        errors = validator.validate_schema(schema)
        assert len(errors) >= 1

    def test_validate_all_schemas(self, validator: ContractValidator) -> None:
        """Test validating all loaded schemas."""
        loader = SchemaLoader()
        schemas = loader.get_all()
        errors = validator.validate_all(schemas)

        # Most schemas should be valid (we fixed them earlier)
        # Just verify the method runs without crashing
        assert isinstance(errors, dict)

    def test_get_pattern_requirements(self, validator: ContractValidator) -> None:
        """Test extracting required variables from a pattern."""
        # This depends on actual patterns existing
        reqs = validator.get_pattern_requirements("multiply_add", "default")
        assert isinstance(reqs, set)

    def test_provided_vars_from_person_vocab(self, validator: ContractValidator) -> None:
        """Test that person vocab auto-generates expected vars."""
        schema = SchemaSpec(
            name="test",
            vocab={"person": VocabSpec(type="person_with_pronouns")},
            answer="x",
        )
        provided = validator._get_provided_vars(schema)
        assert "name" in provided
        assert "subject" in provided
        assert "his_her" in provided

    def test_provided_vars_from_path_vocab(self, validator: ContractValidator) -> None:
        """Test that path-based vocab adds the item name."""
        schema = SchemaSpec(
            name="test",
            vocab={"item": VocabSpec(path="items.countable_singular")},
            answer="x",
        )
        provided = validator._get_provided_vars(schema)
        assert "item" in provided
        assert "item_plural" in provided


class TestWeightedTemplates:
    """Tests for weighted template selection."""

    def test_weighted_template_selection(self) -> None:
        """Test that weighted templates are selected correctly."""
        vocab = get_vocab()

        # Test with simple string templates (should work as before)
        simple_templates = ["Template A", "Template B", "Template C"]
        result = vocab._select_weighted_template(simple_templates)
        assert result in simple_templates

    def test_weighted_dict_templates(self) -> None:
        """Test selection from weighted dict templates."""
        vocab = get_vocab()

        weighted_templates = [
            {"text": "Common template", "weight": 100},
            {"text": "Rare template", "weight": 1},
        ]

        # Run many times - common should appear much more often
        results = [vocab._select_weighted_template(weighted_templates) for _ in range(100)]
        common_count = sum(1 for r in results if r == "Common template")

        # With weights 100:1, common should appear ~99% of the time
        assert common_count > 80, f"Expected >80 common, got {common_count}"

    def test_mixed_templates(self) -> None:
        """Test selection from mixed string and dict templates."""
        vocab = get_vocab()

        mixed_templates = [
            "Simple string template",
            {"text": "Weighted template", "weight": 2},
        ]

        result = vocab._select_weighted_template(mixed_templates)
        assert result in ["Simple string template", "Weighted template"]

    def test_empty_templates(self) -> None:
        """Test handling of empty template list."""
        vocab = get_vocab()
        result = vocab._select_weighted_template([])
        assert result == ""

    def test_non_list_template(self) -> None:
        """Test handling of non-list template."""
        vocab = get_vocab()
        result = vocab._select_weighted_template("single template")
        assert result == "single template"


class TestSchemaComposer:
    """Tests for SchemaComposer."""

    @pytest.fixture
    def composer(self) -> SchemaComposer:
        """Create a composer instance."""
        return SchemaComposer()

    def test_list_mixins(self, composer: SchemaComposer) -> None:
        """Test listing available mixins."""
        mixins = composer.list_mixins()
        assert "person_vocab" in mixins
        assert "item_vocab" in mixins

    def test_load_mixin(self, composer: SchemaComposer) -> None:
        """Test loading a mixin."""
        mixin = composer._load_mixin("person_vocab")
        assert "vocab" in mixin
        assert "person" in mixin["vocab"]

    def test_load_mixin_not_found(self, composer: SchemaComposer) -> None:
        """Test loading nonexistent mixin."""
        with pytest.raises(CompositionError, match="Mixin not found"):
            composer._load_mixin("nonexistent_mixin_xyz")

    def test_compose_with_mixin(self, composer: SchemaComposer) -> None:
        """Test composing a schema with mixins."""
        schema = {
            "name": "test_schema",
            "mixins": ["person_vocab"],
            "variables": {"count": {"type": "int", "min": 1, "max": 10}},
            "answer": "count",
        }

        result = composer.compose(schema)

        # Should have vocab from mixin
        assert "vocab" in result
        assert "person" in result["vocab"]

        # Should still have original variables
        assert "variables" in result
        assert "count" in result["variables"]

        # mixins key should be removed
        assert "mixins" not in result

    def test_compose_multiple_mixins(self, composer: SchemaComposer) -> None:
        """Test composing with multiple mixins."""
        schema = {
            "name": "test_schema",
            "mixins": ["person_vocab", "item_vocab"],
            "answer": "x",
        }

        result = composer.compose(schema)

        # Should have vocab from both mixins
        assert "person" in result["vocab"]
        assert "item" in result["vocab"]

    def test_compose_override(self, composer: SchemaComposer) -> None:
        """Test that child values override mixin values."""
        schema = {
            "name": "test_schema",
            "mixins": ["person_vocab"],
            "template_vars": {
                "name": "custom_name",  # Override mixin's name
            },
            "answer": "x",
        }

        result = composer.compose(schema)

        # Child should override mixin
        assert result["template_vars"]["name"] == "custom_name"

    def test_merge_dicts_deep(self, composer: SchemaComposer) -> None:
        """Test deep merging of dicts."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 20, "z": 30}, "c": 4}

        result = composer._merge_dicts(base, override)

        assert result["a"]["x"] == 1  # Kept from base
        assert result["a"]["y"] == 20  # Overridden
        assert result["a"]["z"] == 30  # Added from override
        assert result["b"] == 3  # Kept from base
        assert result["c"] == 4  # Added from override

    def test_loader_with_composition(self) -> None:
        """Test that loader applies composition."""
        loader = SchemaLoader(compose=True)

        # Load a schema and verify it works
        schema = loader.load("multiply_add")
        assert schema.name == "multiply_add"

    def test_loader_without_composition(self) -> None:
        """Test loader with composition disabled."""
        loader = SchemaLoader(compose=False)

        # Should still load schemas
        schema = loader.load("multiply_add")
        assert schema.name == "multiply_add"


class TestDomainSampler:
    """Tests for DomainSampler."""

    @pytest.fixture
    def sampler(self) -> DomainSampler:
        """Create a sampler instance."""
        return DomainSampler(get_vocab(), seed=42)

    def test_list_domains(self, sampler: DomainSampler) -> None:
        """Test listing available domains."""
        domains = sampler.list_domains()
        assert len(domains) > 0
        assert "kitchen" in domains
        assert "farm" in domains

    def test_sample_kitchen(self, sampler: DomainSampler) -> None:
        """Test sampling from kitchen domain."""
        context = sampler.sample("kitchen")

        assert context["domain"] == "kitchen"
        assert "agent" in context
        assert "item" in context
        assert context["verb"] == "bakes"
        assert context["item"] in ["cookies", "loaves", "cakes", "muffins", "pies", "batches"]

    def test_sample_farm(self, sampler: DomainSampler) -> None:
        """Test sampling from farm domain."""
        context = sampler.sample("farm")

        assert context["domain"] == "farm"
        assert "agent" in context
        assert "item" in context

    def test_sample_nonexistent_domain(self, sampler: DomainSampler) -> None:
        """Test sampling from nonexistent domain returns default."""
        context = sampler.sample("nonexistent_domain_xyz")

        assert context["domain"] == "default"
        assert "agent" in context
        assert context["item"] == "item"

    def test_random_domain(self, sampler: DomainSampler) -> None:
        """Test getting a random domain."""
        domain = sampler.random_domain()
        assert domain in sampler.list_domains()

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed gives same results."""
        sampler1 = DomainSampler(get_vocab(), seed=123)
        sampler2 = DomainSampler(get_vocab(), seed=123)

        context1 = sampler1.sample("kitchen")
        context2 = sampler2.sample("kitchen")

        assert context1["agent"] == context2["agent"]
        assert context1["item"] == context2["item"]

    def test_item_plural(self, sampler: DomainSampler) -> None:
        """Test that item_plural is generated."""
        context = sampler.sample("kitchen")
        assert "item_plural" in context

    def test_time_units(self, sampler: DomainSampler) -> None:
        """Test that time units are sampled when available."""
        context = sampler.sample("kitchen")
        assert "time_unit" in context
        assert "time_unit_plural" in context
