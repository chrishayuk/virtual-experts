"""Additional tests for ContractValidator - comprehensive coverage."""

from __future__ import annotations

from typing import Any

from chuk_virtual_expert_arithmetic.core.contracts import ContractValidator
from chuk_virtual_expert_arithmetic.models.schema_spec import SchemaSpec, VariableSpec, VocabSpec


class MockVocab:
    """Mock Vocab for testing ContractValidator."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}

    def get(self, path: str) -> Any:
        parts = path.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current


class TestValidateSchemaNoPattern:
    """Tests for validate_schema when schema has no pattern."""

    def test_no_pattern_returns_empty(self) -> None:
        """Test schema without pattern returns no errors."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(name="test", answer="x")
        errors = validator.validate_schema(schema)
        assert errors == []


class TestValidateSchemaPatternNotFound:
    """Tests for validate_schema when pattern not found."""

    def test_pattern_not_found(self) -> None:
        """Test error when pattern doesn't exist."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(name="test", pattern="nonexistent", answer="x")
        errors = validator.validate_schema(schema)
        assert len(errors) == 1
        assert "not found" in errors[0]


class TestValidateSchemaNoTemplates:
    """Tests for validate_schema when no templates found."""

    def test_no_templates_in_pattern(self) -> None:
        """Test error when pattern has no templates."""
        # Pattern exists but has no templates key - use non-empty dict so it passes existence check
        data: dict[str, Any] = {"patterns": {"empty_pattern": {"description": "No templates here"}}}
        vocab = MockVocab(data)
        validator = ContractValidator(vocab)
        schema = SchemaSpec(name="test", pattern="empty_pattern", answer="x")
        errors = validator.validate_schema(schema)
        assert len(errors) == 1
        assert "No templates found" in errors[0]

    def test_variant_not_found(self) -> None:
        """Test error when variant doesn't exist."""
        # Pattern has templates but not the requested variant
        data: dict[str, Any] = {"patterns": {"test_pattern": {"default": ["Some template"]}}}
        vocab = MockVocab(data)
        validator = ContractValidator(vocab)
        schema = SchemaSpec(name="test", pattern="test_pattern", variant="missing_variant", answer="x")
        errors = validator.validate_schema(schema)
        assert len(errors) == 1
        assert "Variant 'missing_variant' not found" in errors[0]


class TestValidateSchemaMissingVars:
    """Tests for validate_schema with missing variables."""

    def test_missing_template_vars(self) -> None:
        """Test error when template vars are missing."""
        vocab = MockVocab({
            "patterns": {
                "test_pattern": {
                    "templates": ["${name} has ${count} ${item}"]
                }
            }
        })
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            pattern="test_pattern",
            answer="x",
            variables={"count": VariableSpec(type="int", min=1, max=10)},
        )
        errors = validator.validate_schema(schema)
        assert len(errors) == 1
        assert "missing template vars" in errors[0]
        assert "name" in errors[0] or "item" in errors[0]


class TestValidateSchemaWithValidVars:
    """Tests for validate_schema with all required vars."""

    def test_all_vars_provided(self) -> None:
        """Test no errors when all vars are provided."""
        vocab = MockVocab({
            "patterns": {
                "simple": {
                    "templates": ["${name} has ${count}"]
                }
            }
        })
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            pattern="simple",
            answer="count",
            variables={"count": VariableSpec(type="int", min=1, max=10)},
            template_vars={"name": "person.name"},
        )
        errors = validator.validate_schema(schema)
        assert errors == []


class TestValidateAll:
    """Tests for validate_all method."""

    def test_validate_all_no_errors(self) -> None:
        """Test validate_all with no errors."""
        vocab = MockVocab({
            "patterns": {
                "simple": {"templates": ["${x}"]}
            }
        })
        validator = ContractValidator(vocab)
        schemas = {
            "test1": SchemaSpec(
                name="test1",
                pattern="simple",
                answer="x",
                variables={"x": VariableSpec(type="int")},
            ),
            "test2": SchemaSpec(name="test2", answer="y"),
        }
        errors = validator.validate_all(schemas)
        assert errors == {}

    def test_validate_all_with_errors(self) -> None:
        """Test validate_all with some errors."""
        vocab = MockVocab({
            "patterns": {
                "needs_name": {"templates": ["${name} does something"]}
            }
        })
        validator = ContractValidator(vocab)
        schemas = {
            "good": SchemaSpec(
                name="good",
                pattern="needs_name",
                answer="x",
                template_vars={"name": "person.name"},
            ),
            "bad": SchemaSpec(name="bad", pattern="needs_name", answer="x"),
        }
        errors = validator.validate_all(schemas)
        assert "bad" in errors
        assert "good" not in errors


class TestGetTemplates:
    """Tests for _get_templates method."""

    def test_templates_as_list(self) -> None:
        """Test extracting templates from list."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        pattern_data = ["template1", "template2", 123]  # Non-string should be skipped
        templates = validator._get_templates(pattern_data, None)
        assert templates == ["template1", "template2"]

    def test_templates_as_dict_with_templates_key(self) -> None:
        """Test extracting templates from dict with 'templates' key."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        pattern_data = {"templates": ["template1", "template2"]}
        templates = validator._get_templates(pattern_data, None)
        assert templates == ["template1", "template2"]

    def test_templates_from_variant(self) -> None:
        """Test extracting templates from variant."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        pattern_data = {
            "default": ["default template"],
            "variant1": ["variant1 template"],
        }
        templates = validator._get_templates(pattern_data, "variant1")
        assert templates == ["variant1 template"]

    def test_templates_weighted_format(self) -> None:
        """Test extracting templates with weighted format."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        pattern_data = {
            "templates": [
                {"text": "weighted template", "weight": 2},
                "plain template",
            ]
        }
        templates = validator._get_templates(pattern_data, None)
        assert "weighted template" in templates
        assert "plain template" in templates

    def test_templates_empty_dict(self) -> None:
        """Test empty dict returns empty list."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        pattern_data = {}
        templates = validator._get_templates(pattern_data, None)
        assert templates == []


class TestExtractTemplateVars:
    """Tests for _extract_template_vars method."""

    def test_extract_single_var(self) -> None:
        """Test extracting single variable."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        templates = ["Hello ${name}"]
        vars = validator._extract_template_vars(templates)
        assert vars == {"name"}

    def test_extract_multiple_vars(self) -> None:
        """Test extracting multiple variables."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        templates = ["${name} has ${count} ${item}"]
        vars = validator._extract_template_vars(templates)
        assert vars == {"name", "count", "item"}

    def test_extract_from_multiple_templates(self) -> None:
        """Test extracting from multiple templates."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        templates = ["${a} and ${b}", "${c} or ${d}"]
        vars = validator._extract_template_vars(templates)
        assert vars == {"a", "b", "c", "d"}

    def test_extract_no_vars(self) -> None:
        """Test template without variables."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        templates = ["No variables here"]
        vars = validator._extract_template_vars(templates)
        assert vars == set()


class TestGetProvidedVars:
    """Tests for _get_provided_vars method."""

    def test_from_template_vars(self) -> None:
        """Test getting vars from template_vars."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            template_vars={"name": "person.name", "item": "items.fruit"},
        )
        provided = validator._get_provided_vars(schema)
        assert "name" in provided
        assert "item" in provided

    def test_from_variables(self) -> None:
        """Test getting vars from variables."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            variables={
                "count": VariableSpec(type="int"),
                "price": VariableSpec(type="float"),
            },
        )
        provided = validator._get_provided_vars(schema)
        assert "count" in provided
        assert "price" in provided

    def test_from_person_vocab(self) -> None:
        """Test auto-generated vars from person vocab."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            vocab={"person": VocabSpec(type="person_with_pronouns")},
        )
        provided = validator._get_provided_vars(schema)
        assert "name" in provided
        assert "subject" in provided
        assert "subj" in provided
        assert "his_her" in provided
        assert "him_her" in provided
        assert "reflexive" in provided

    def test_from_person_numbered_vocab(self) -> None:
        """Test auto-generated vars from numbered person vocab."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            vocab={"person1": VocabSpec(type="person_with_pronouns")},
        )
        provided = validator._get_provided_vars(schema)
        assert "name1" in provided
        assert "subject1" in provided
        assert "subj1" in provided
        assert "his_her1" in provided

    def test_from_path_vocab(self) -> None:
        """Test vars from path-based vocab."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            vocab={"item": VocabSpec(path="items.countable_singular")},
        )
        provided = validator._get_provided_vars(schema)
        assert "item" in provided
        assert "item_plural" in provided

    def test_from_path_vocab_non_countable(self) -> None:
        """Test vars from path-based vocab without countable_singular."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            vocab={"verb": VocabSpec(path="verbs.action")},
        )
        provided = validator._get_provided_vars(schema)
        assert "verb" in provided
        assert "verb_plural" not in provided

    def test_multiplier_words(self) -> None:
        """Test auto-generated multiplier words."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        schema = SchemaSpec(
            name="test",
            answer="x",
            variables={"multiplier": VariableSpec(type="int", min=2, max=5)},
        )
        provided = validator._get_provided_vars(schema)
        assert "mult_word" in provided
        assert "growth_word" in provided


class TestGetPatternRequirements:
    """Tests for get_pattern_requirements method."""

    def test_pattern_exists(self) -> None:
        """Test getting requirements for existing pattern."""
        vocab = MockVocab({
            "patterns": {
                "test": {"templates": ["${a} and ${b}"]}
            }
        })
        validator = ContractValidator(vocab)
        reqs = validator.get_pattern_requirements("test")
        assert reqs == {"a", "b"}

    def test_pattern_not_exists(self) -> None:
        """Test getting requirements for non-existent pattern."""
        vocab = MockVocab()
        validator = ContractValidator(vocab)
        reqs = validator.get_pattern_requirements("nonexistent")
        assert reqs == set()

    def test_pattern_with_variant(self) -> None:
        """Test getting requirements for pattern with variant."""
        vocab = MockVocab({
            "patterns": {
                "test": {
                    "default": ["${x}"],
                    "variant1": ["${y} and ${z}"],
                }
            }
        })
        validator = ContractValidator(vocab)
        reqs = validator.get_pattern_requirements("test", "variant1")
        assert reqs == {"y", "z"}
