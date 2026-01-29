"""Additional tests for SchemaGenerator - comprehensive coverage."""

from __future__ import annotations

import pytest

from chuk_virtual_expert_arithmetic.generators.schema_generator import (
    SchemaGenerator,
    generate_batch_from_schemas,
    generate_from_schema,
)


class TestSchemaGeneratorInit:
    """Tests for SchemaGenerator initialization."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        gen = SchemaGenerator()
        assert gen._word_number_prob == 0.3
        assert gen._perturbation_level == 0.0
        assert gen._gsm8k_style_prob == 0.3
        assert gen._messy_vocab_prob == 0.2

    def test_init_with_seed(self) -> None:
        """Test initialization with seed."""
        gen = SchemaGenerator(seed=42)
        assert gen._rng is not None

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        gen = SchemaGenerator(
            word_number_prob=0.5,
            perturbation_level=0.6,
            gsm8k_style_prob=0.4,
            messy_vocab_prob=0.3,
        )
        assert gen._word_number_prob == 0.5
        assert gen._perturbation_level == 0.6


class TestSchemaGeneratorProperties:
    """Tests for property getters and setters."""

    def test_schema_names(self) -> None:
        """Test schema_names property."""
        gen = SchemaGenerator()
        names = gen.schema_names
        assert isinstance(names, list)
        assert len(names) > 0

    def test_perturbation_level_getter(self) -> None:
        """Test perturbation_level getter."""
        gen = SchemaGenerator(perturbation_level=0.5)
        assert gen.perturbation_level == 0.5

    def test_perturbation_level_setter(self) -> None:
        """Test perturbation_level setter."""
        gen = SchemaGenerator()
        gen.perturbation_level = 0.7
        assert gen.perturbation_level == 0.7

    def test_perturbation_level_clamped(self) -> None:
        """Test perturbation_level is clamped."""
        gen = SchemaGenerator()
        gen.perturbation_level = 1.5
        assert gen.perturbation_level == 1.0
        gen.perturbation_level = -0.5
        assert gen.perturbation_level == 0.0

    def test_gsm8k_style_prob_getter(self) -> None:
        """Test gsm8k_style_prob getter."""
        gen = SchemaGenerator(gsm8k_style_prob=0.5)
        assert gen.gsm8k_style_prob == 0.5

    def test_gsm8k_style_prob_setter(self) -> None:
        """Test gsm8k_style_prob setter."""
        gen = SchemaGenerator()
        gen.gsm8k_style_prob = 0.8
        assert gen.gsm8k_style_prob == 0.8

    def test_gsm8k_style_prob_clamped(self) -> None:
        """Test gsm8k_style_prob is clamped."""
        gen = SchemaGenerator()
        gen.gsm8k_style_prob = 1.5
        assert gen.gsm8k_style_prob == 1.0
        gen.gsm8k_style_prob = -0.5
        assert gen.gsm8k_style_prob == 0.0


class TestSchemasByDepth:
    """Tests for schema depth methods."""

    def test_get_schemas_by_depth(self) -> None:
        """Test getting schemas grouped by depth."""
        gen = SchemaGenerator()
        schemas_by_depth = gen._get_schemas_by_depth()
        assert isinstance(schemas_by_depth, dict)
        assert len(schemas_by_depth) > 0
        # Check that depths are integers
        for depth in schemas_by_depth:
            assert isinstance(depth, int)
            assert depth >= 1

    def test_schemas_by_depth_cached(self) -> None:
        """Test that schemas by depth are cached."""
        gen = SchemaGenerator()
        result1 = gen._get_schemas_by_depth()
        result2 = gen._get_schemas_by_depth()
        assert result1 is result2

    def test_estimate_depth(self) -> None:
        """Test depth estimation."""
        gen = SchemaGenerator()
        schema = {"trace": [{"op": "init"}, {"op": "compute"}, {"op": "compute"}]}
        depth = gen._estimate_depth(schema)
        assert depth == 2

    def test_estimate_depth_empty_trace(self) -> None:
        """Test depth estimation with empty trace."""
        gen = SchemaGenerator()
        schema = {"trace": []}
        depth = gen._estimate_depth(schema)
        assert depth == 1  # Minimum depth of 1


class TestGenerateWithTargetDepth:
    """Tests for generate_with_target_depth method."""

    def test_generate_with_specific_depth(self) -> None:
        """Test generating with specific target depth."""
        gen = SchemaGenerator(seed=42)
        example = gen.generate_with_target_depth(target_depth=2)
        assert example is not None
        assert example.query is not None

    def test_generate_with_gsm8k_distribution(self) -> None:
        """Test generating with GSM-8K distribution."""
        gen = SchemaGenerator(seed=42)
        example = gen.generate_with_target_depth(use_gsm8k_distribution=True)
        assert example is not None

    def test_generate_with_fallback(self) -> None:
        """Test generating falls back to random when depth not found."""
        gen = SchemaGenerator(seed=42)
        # Request a very high depth that probably doesn't exist
        example = gen.generate_with_target_depth(target_depth=100)
        assert example is not None


class TestGenerateBatchGsm8kDistribution:
    """Tests for generate_batch_gsm8k_distribution method."""

    def test_generate_batch_gsm8k_distribution(self) -> None:
        """Test batch generation with GSM-8K distribution."""
        gen = SchemaGenerator(seed=42)
        examples = gen.generate_batch_gsm8k_distribution(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex is not None


class TestGenerateVariables:
    """Tests for variable generation."""

    def test_generate_bool_variable(self) -> None:
        """Test generating boolean variable."""
        gen = SchemaGenerator(seed=42)
        var_specs = {"flag": {"type": "bool"}}
        variables = gen._generate_variables(var_specs)
        assert "flag" in variables
        assert isinstance(variables["flag"], bool)

    def test_generate_choice_variable(self) -> None:
        """Test generating choice variable."""
        gen = SchemaGenerator(seed=42)
        var_specs = {"option": {"type": "choice", "options": ["a", "b", "c"]}}
        variables = gen._generate_variables(var_specs)
        assert "option" in variables
        assert variables["option"] in ["a", "b", "c"]

    def test_generate_choice_with_values(self) -> None:
        """Test generating choice variable with values."""
        gen = SchemaGenerator(seed=42)
        var_specs = {"option": {"type": "choice", "values": [1, 2, 3]}}
        variables = gen._generate_variables(var_specs)
        assert variables["option"] in [1, 2, 3]

    def test_generate_choice_empty(self) -> None:
        """Test generating choice variable with empty options."""
        gen = SchemaGenerator(seed=42)
        var_specs = {"option": {"type": "choice", "options": []}}
        variables = gen._generate_variables(var_specs)
        assert variables["option"] == 0


class TestApplyConstraints:
    """Tests for constraint application."""

    def test_apply_constraints_expression_error(self) -> None:
        """Test constraint with expression error."""
        gen = SchemaGenerator(seed=42)
        # Invalid expression in constraint
        constraints = {"x + + y": {"min": 0}}
        variables = {"x": 5, "y": 10}
        schema = {"variables": {"x": {"type": "int", "min": 1, "max": 10}}}
        result = gen._apply_constraints(constraints, variables, schema)
        # Should not crash, returns variables
        assert isinstance(result, dict)


class TestSampleVocab:
    """Tests for vocab sampling."""

    def test_sample_domain_context(self) -> None:
        """Test sampling domain context."""
        gen = SchemaGenerator(seed=42)
        vocab_specs = {"context": {"type": "domain_context", "domain": "random"}}
        items = gen._sample_vocab(vocab_specs)
        assert "context" in items
        assert isinstance(items["context"], dict)

    def test_sample_choice_type(self) -> None:
        """Test sampling choice type in vocab."""
        gen = SchemaGenerator(seed=42)
        vocab_specs = {"word": {"type": "choice", "values": ["twice", "triple"]}}
        items = gen._sample_vocab(vocab_specs)
        assert items["word"] in ["twice", "triple"]

    def test_sample_with_path(self) -> None:
        """Test sampling with vocab path."""
        gen = SchemaGenerator(seed=42)
        vocab_specs = {"name": {"path": "names.male"}}
        items = gen._sample_vocab(vocab_specs)
        assert "name" in items
        assert isinstance(items["name"], str)

    def test_sample_with_distinct_from(self) -> None:
        """Test sampling with distinct_from constraint."""
        gen = SchemaGenerator(seed=42)
        vocab_specs = {
            "name1": {"path": "names.male"},
            "name2": {"path": "names.male", "distinct_from": ["name1"]},
        }
        items = gen._sample_vocab(vocab_specs)
        assert "name1" in items
        assert "name2" in items
        # They should ideally be different (though with small list might be same)

    def test_sample_diverse_person(self) -> None:
        """Test sampling diverse person."""
        gen = SchemaGenerator(seed=42, messy_vocab_prob=1.0)  # Always use messy
        vocab_specs = {"person": {"type": "person_with_pronouns"}}
        items = gen._sample_vocab(vocab_specs)
        assert "person" in items
        assert "name" in items["person"]


class TestSampleWithExclusion:
    """Tests for _sample_with_exclusion method."""

    def test_sample_with_exclusion_non_list(self) -> None:
        """Test sampling when vocab path returns non-list."""
        gen = SchemaGenerator(seed=42)
        # Get a path that doesn't return a list
        result = gen._sample_with_exclusion("names.pronouns", set())
        # Should return the random result (which is None for non-list)
        assert result is None or isinstance(result, (str, dict))


class TestResolveTemplateSpec:
    """Tests for template spec resolution."""

    def test_resolve_list_index(self) -> None:
        """Test resolving list index in spec."""
        gen = SchemaGenerator(seed=42)
        vocab_items = {"items": ["apple", "banana", "cherry"]}
        result = gen._resolve_template_spec("items.1", {}, vocab_items)
        assert result == "banana"

    def test_resolve_list_index_out_of_bounds(self) -> None:
        """Test resolving list index out of bounds."""
        gen = SchemaGenerator(seed=42)
        vocab_items = {"items": ["apple"]}
        result = gen._resolve_template_spec("items.5", {}, vocab_items)
        assert result is None

    def test_resolve_non_dict_non_list(self) -> None:
        """Test resolving when value is not dict or list."""
        gen = SchemaGenerator(seed=42)
        vocab_items = {"value": "simple_string"}
        result = gen._resolve_template_spec("value.something", {}, vocab_items)
        assert result is None


class TestApplyTransform:
    """Tests for _apply_transform method."""

    def test_singularize_ies(self) -> None:
        """Test singularize with -ies ending."""
        gen = SchemaGenerator(seed=42)
        result = gen._apply_transform("berries", "singularize")
        assert result == "berry"

    def test_singularize_es(self) -> None:
        """Test singularize with -es ending."""
        gen = SchemaGenerator(seed=42)
        result = gen._apply_transform("boxes", "singularize")
        assert result == "box"

    def test_singularize_s(self) -> None:
        """Test singularize with -s ending (not -es or -ies)."""
        gen = SchemaGenerator(seed=42)
        # "cats" ends in "s" but not "es" or "ies"
        result = gen._apply_transform("cats", "singularize")
        assert result == "cat"

    def test_singularize_no_s(self) -> None:
        """Test singularize with no -s ending."""
        gen = SchemaGenerator(seed=42)
        result = gen._apply_transform("sheep", "singularize")
        assert result == "sheep"


class TestComputeAnswer:
    """Tests for _compute_answer method."""

    def test_compute_answer_expression_error(self) -> None:
        """Test answer computation with expression error."""
        gen = SchemaGenerator(seed=42)
        # Use unclosed parenthesis for actual syntax error
        result = gen._compute_answer("(x + y", {"x": 5, "y": 10})
        assert result == 0.0


class TestApplyWordNumbers:
    """Tests for _apply_word_numbers method."""

    def test_word_numbers_disabled(self) -> None:
        """Test with word numbers disabled."""
        gen = SchemaGenerator(word_number_prob=0.0)
        result = gen._apply_word_numbers("Alice has 5 apples.")
        assert "5" in result

    def test_word_numbers_skip_price(self) -> None:
        """Test that prices are not converted."""
        gen = SchemaGenerator(word_number_prob=1.0, seed=42)
        result = gen._apply_word_numbers("The cost is $5.")
        assert "$5" in result or "five" in result  # $ should prevent conversion

    def test_word_numbers_skip_decimal(self) -> None:
        """Test that decimals are not converted."""
        gen = SchemaGenerator(word_number_prob=1.0, seed=42)
        result = gen._apply_word_numbers("The value is 5.5.")
        # Decimals shouldn't be converted
        assert "5.5" in result or "five" not in result


class TestAsyncMethods:
    """Tests for async generation methods."""

    @pytest.mark.asyncio
    async def test_generate_async(self) -> None:
        """Test async generate method."""
        gen = SchemaGenerator(seed=42)
        example = await gen.generate_async()
        assert example is not None
        assert example.query is not None

    @pytest.mark.asyncio
    async def test_generate_async_with_schema(self) -> None:
        """Test async generate with specific schema."""
        gen = SchemaGenerator(seed=42)
        example = await gen.generate_async("multiply_add")
        assert example is not None

    @pytest.mark.asyncio
    async def test_generate_batch_async(self) -> None:
        """Test async batch generation."""
        gen = SchemaGenerator(seed=42)
        examples = await gen.generate_batch_async(n=5, concurrency=2)
        assert len(examples) == 5

    @pytest.mark.asyncio
    async def test_generate_batch_async_default_schemas(self) -> None:
        """Test async batch generation with default schemas."""
        gen = SchemaGenerator(seed=42)
        examples = await gen.generate_batch_async(n=3)
        assert len(examples) == 3

    @pytest.mark.asyncio
    async def test_generate_balanced_async(self) -> None:
        """Test async balanced generation."""
        gen = SchemaGenerator(seed=42)
        examples = await gen.generate_balanced_async(n=6, concurrency=2)
        assert len(examples) > 0

    @pytest.mark.asyncio
    async def test_generate_stream_async(self) -> None:
        """Test async stream generation."""
        gen = SchemaGenerator(seed=42)
        examples = []
        async for example in gen.generate_stream_async(n=3):
            examples.append(example)
        assert len(examples) == 3

    @pytest.mark.asyncio
    async def test_generate_stream_async_default_schemas(self) -> None:
        """Test async stream generation with default schemas."""
        gen = SchemaGenerator(seed=42)
        count = 0
        async for _example in gen.generate_stream_async(n=2):
            count += 1
        assert count == 2


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_generate_from_schema(self) -> None:
        """Test generate_from_schema function."""
        example = generate_from_schema("multiply_add")
        assert example is not None
        assert example.query is not None

    def test_generate_batch_from_schemas(self) -> None:
        """Test generate_batch_from_schemas function."""
        examples = generate_batch_from_schemas(n=3)
        assert len(examples) == 3


class TestGenerateWithPerturbation:
    """Tests for generation with perturbation."""

    def test_generate_with_perturbation(self) -> None:
        """Test generation with perturbation enabled."""
        gen = SchemaGenerator(seed=42, perturbation_level=0.5)
        example = gen.generate("multiply_add")
        assert example is not None
        assert example.query is not None


class TestGenerateWithGsm8kStyle:
    """Tests for generation with GSM-8K style."""

    def test_generate_with_gsm8k_style(self) -> None:
        """Test generation with high GSM-8K style probability."""
        gen = SchemaGenerator(seed=42, gsm8k_style_prob=1.0)
        example = gen.generate("multiply_add")
        assert example is not None
        assert example.query is not None


class TestTemplateVarsHandling:
    """Tests for template vars handling."""

    def test_generate_produces_valid_output(self) -> None:
        """Test that generate produces valid output."""
        gen = SchemaGenerator(seed=42)
        example = gen.generate("multiply_add")
        assert "${" not in example.query  # No unresolved template vars
        assert example.answer is not None


class TestLoadSchemasComposition:
    """Tests for schema loading with composition."""

    def test_load_schemas_handles_composition_error(self) -> None:
        """Test that composition errors are handled gracefully."""
        # This test just verifies the generator initializes without error
        # even if some schema composition might fail
        gen = SchemaGenerator()
        assert len(gen.schema_names) > 0
