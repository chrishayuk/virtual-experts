"""Tests for domain models - comprehensive coverage."""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.models.domain import (
    AgentTemplate,
    DomainContext,
    DomainSpec,
    ItemSpec,
    TimeUnitSpec,
    VerbSpec,
)


class TestAgentTemplate:
    """Tests for AgentTemplate model."""

    def test_default_pattern(self) -> None:
        """Test default pattern is ${name}."""
        template = AgentTemplate()
        assert template.pattern == "${name}"

    def test_pattern_with_numbers(self) -> None:
        """Test pattern with numbers."""
        template = AgentTemplate(pattern="Machine ${number}", numbers=[1, 2, 3])
        assert template.pattern == "Machine ${number}"
        assert template.numbers == [1, 2, 3]

    def test_pattern_with_letters(self) -> None:
        """Test pattern with letters."""
        template = AgentTemplate(pattern="Worker ${letter}", letters=["A", "B", "C"])
        assert template.pattern == "Worker ${letter}"
        assert template.letters == ["A", "B", "C"]

    def test_pattern_with_source(self) -> None:
        """Test pattern with vocab source."""
        template = AgentTemplate(pattern="${name}", source="names.male")
        assert template.source == "names.male"

    def test_all_fields(self) -> None:
        """Test all fields together."""
        template = AgentTemplate(
            pattern="Oven ${number}",
            numbers=[1, 2],
            letters=None,
            source=None,
        )
        assert template.pattern == "Oven ${number}"
        assert template.numbers == [1, 2]
        assert template.letters is None
        assert template.source is None

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed due to model_config."""
        template = AgentTemplate(pattern="${name}", custom_field="value")
        assert template.pattern == "${name}"
        assert template.custom_field == "value"


class TestItemSpec:
    """Tests for ItemSpec model."""

    def test_singular_only(self) -> None:
        """Test with only singular form."""
        item = ItemSpec(singular="apple")
        assert item.singular == "apple"
        assert item.plural is None

    def test_singular_and_plural(self) -> None:
        """Test with both forms."""
        item = ItemSpec(singular="child", plural="children")
        assert item.singular == "child"
        assert item.plural == "children"

    def test_get_plural_explicit(self) -> None:
        """Test get_plural with explicit plural."""
        item = ItemSpec(singular="mouse", plural="mice")
        assert item.get_plural() == "mice"

    def test_get_plural_regular(self) -> None:
        """Test get_plural auto-generates regular plural."""
        item = ItemSpec(singular="apple")
        assert item.get_plural() == "apples"

    def test_get_plural_ending_s(self) -> None:
        """Test get_plural for words ending in s."""
        item = ItemSpec(singular="bus")
        assert item.get_plural() == "buses"

    def test_get_plural_ending_x(self) -> None:
        """Test get_plural for words ending in x."""
        item = ItemSpec(singular="box")
        assert item.get_plural() == "boxes"

    def test_get_plural_ending_ch(self) -> None:
        """Test get_plural for words ending in ch."""
        item = ItemSpec(singular="match")
        assert item.get_plural() == "matches"

    def test_get_plural_ending_sh(self) -> None:
        """Test get_plural for words ending in sh."""
        item = ItemSpec(singular="dish")
        assert item.get_plural() == "dishes"

    def test_get_plural_ending_y_consonant(self) -> None:
        """Test get_plural for words ending in consonant+y."""
        item = ItemSpec(singular="baby")
        assert item.get_plural() == "babies"

        item = ItemSpec(singular="city")
        assert item.get_plural() == "cities"

    def test_get_plural_ending_y_vowel(self) -> None:
        """Test get_plural for words ending in vowel+y."""
        item = ItemSpec(singular="key")
        assert item.get_plural() == "keys"

        item = ItemSpec(singular="day")
        assert item.get_plural() == "days"

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        item = ItemSpec(singular="book", category="education")
        assert item.singular == "book"
        assert item.category == "education"


class TestVerbSpec:
    """Tests for VerbSpec model."""

    def test_minimal_spec(self) -> None:
        """Test minimal spec with required fields."""
        verb = VerbSpec(singular="bakes", plural="bake")
        assert verb.singular == "bakes"
        assert verb.plural == "bake"

    def test_full_spec(self) -> None:
        """Test full spec with all forms."""
        verb = VerbSpec(
            singular="bakes",
            plural="bake",
            base="bake",
            gerund="baking",
            past="baked",
        )
        assert verb.singular == "bakes"
        assert verb.plural == "bake"
        assert verb.base == "bake"
        assert verb.gerund == "baking"
        assert verb.past == "baked"

    def test_default_optional_fields(self) -> None:
        """Test that optional fields default to None."""
        verb = VerbSpec(singular="runs", plural="run")
        assert verb.base is None
        assert verb.gerund is None
        assert verb.past is None

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        verb = VerbSpec(singular="swims", plural="swim", irregular=True)
        assert verb.singular == "swims"
        assert verb.irregular is True


class TestTimeUnitSpec:
    """Tests for TimeUnitSpec model."""

    def test_hour(self) -> None:
        """Test hour time unit."""
        unit = TimeUnitSpec(singular="hour", plural="hours")
        assert unit.singular == "hour"
        assert unit.plural == "hours"

    def test_minute(self) -> None:
        """Test minute time unit."""
        unit = TimeUnitSpec(singular="minute", plural="minutes")
        assert unit.singular == "minute"
        assert unit.plural == "minutes"

    def test_day(self) -> None:
        """Test day time unit."""
        unit = TimeUnitSpec(singular="day", plural="days")
        assert unit.singular == "day"
        assert unit.plural == "days"

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        unit = TimeUnitSpec(singular="week", plural="weeks", abbreviation="wk")
        assert unit.singular == "week"
        assert unit.abbreviation == "wk"


class TestDomainSpec:
    """Tests for DomainSpec model."""

    def test_minimal_spec(self) -> None:
        """Test minimal spec with just name."""
        domain = DomainSpec(name="test")
        assert domain.name == "test"
        assert domain.description is None
        assert domain.agent_templates == {}
        assert domain.items == []
        assert domain.verbs is None
        assert domain.time_units == []

    def test_full_spec(self) -> None:
        """Test full domain specification."""
        domain = DomainSpec(
            name="kitchen",
            description="Baking and cooking domain",
            agent_templates={
                "machine": AgentTemplate(pattern="Oven ${number}", numbers=[1, 2]),
                "person": AgentTemplate(pattern="${name}", source="names.chefs"),
            },
            items=[
                ItemSpec(singular="cookie", plural="cookies"),
                ItemSpec(singular="cake", plural="cakes"),
            ],
            verbs=VerbSpec(singular="bakes", plural="bake"),
            time_units=[
                TimeUnitSpec(singular="hour", plural="hours"),
            ],
        )

        assert domain.name == "kitchen"
        assert domain.description == "Baking and cooking domain"
        assert len(domain.agent_templates) == 2
        assert len(domain.items) == 2
        assert domain.verbs is not None
        assert len(domain.time_units) == 1

    def test_items_as_strings(self) -> None:
        """Test items can be specified as strings."""
        domain = DomainSpec(
            name="test",
            items=["apple", "banana", "orange"],
        )
        assert domain.items == ["apple", "banana", "orange"]

    def test_items_mixed(self) -> None:
        """Test items can be mixed strings and ItemSpec."""
        domain = DomainSpec(
            name="test",
            items=[
                "apple",
                ItemSpec(singular="child", plural="children"),
            ],
        )
        assert len(domain.items) == 2

    def test_verbs_as_dict(self) -> None:
        """Test verbs can be specified as dict."""
        domain = DomainSpec(
            name="test",
            verbs={"singular": "runs", "plural": "run"},
        )
        assert domain.verbs == {"singular": "runs", "plural": "run"}

    def test_get_item_list_from_strings(self) -> None:
        """Test get_item_list converts strings to ItemSpec."""
        domain = DomainSpec(
            name="test",
            items=["apple", "banana"],
        )
        item_list = domain.get_item_list()

        assert len(item_list) == 2
        assert all(isinstance(item, ItemSpec) for item in item_list)
        assert item_list[0].singular == "apple"
        assert item_list[1].singular == "banana"

    def test_get_item_list_from_itemspec(self) -> None:
        """Test get_item_list passes through ItemSpec."""
        domain = DomainSpec(
            name="test",
            items=[ItemSpec(singular="cookie", plural="cookies")],
        )
        item_list = domain.get_item_list()

        assert len(item_list) == 1
        assert item_list[0].singular == "cookie"
        assert item_list[0].plural == "cookies"

    def test_get_item_list_empty(self) -> None:
        """Test get_item_list with no items."""
        domain = DomainSpec(name="test")
        item_list = domain.get_item_list()
        assert item_list == []

    def test_get_verbs_none(self) -> None:
        """Test get_verbs with no verbs returns default."""
        domain = DomainSpec(name="test")
        verbs = domain.get_verbs()

        assert verbs.singular == "processes"
        assert verbs.plural == "process"

    def test_get_verbs_from_dict(self) -> None:
        """Test get_verbs converts dict to VerbSpec."""
        domain = DomainSpec(
            name="test",
            verbs={"singular": "bakes", "plural": "bake"},
        )
        verbs = domain.get_verbs()

        assert isinstance(verbs, VerbSpec)
        assert verbs.singular == "bakes"
        assert verbs.plural == "bake"

    def test_get_verbs_from_verbspec(self) -> None:
        """Test get_verbs returns VerbSpec directly."""
        verb_spec = VerbSpec(singular="runs", plural="run")
        domain = DomainSpec(name="test", verbs=verb_spec)
        verbs = domain.get_verbs()

        assert verbs is verb_spec

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        domain = DomainSpec(name="test", custom_setting="value")
        assert domain.name == "test"
        assert domain.custom_setting == "value"


class TestDomainContext:
    """Tests for DomainContext model."""

    def test_minimal_context(self) -> None:
        """Test minimal context with required fields."""
        context = DomainContext(domain="test", agent="Alice")
        assert context.domain == "test"
        assert context.agent == "Alice"
        assert context.agent2 is None
        assert context.agent_type == "person"
        assert context.item == "item"
        assert context.item_plural == "items"
        assert context.verb == "has"
        assert context.verb_plural == "have"
        assert context.time_unit is None
        assert context.time_unit_plural is None

    def test_full_context(self) -> None:
        """Test full context with all fields."""
        context = DomainContext(
            domain="kitchen",
            agent="Oven 1",
            agent2="Oven 2",
            agent_type="machine",
            item="cookie",
            item_plural="cookies",
            verb="bakes",
            verb_plural="bake",
            time_unit="hour",
            time_unit_plural="hours",
        )

        assert context.domain == "kitchen"
        assert context.agent == "Oven 1"
        assert context.agent2 == "Oven 2"
        assert context.agent_type == "machine"
        assert context.item == "cookie"
        assert context.item_plural == "cookies"
        assert context.verb == "bakes"
        assert context.verb_plural == "bake"
        assert context.time_unit == "hour"
        assert context.time_unit_plural == "hours"

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        context = DomainContext(domain="test", agent="Bob", custom_field="value")
        assert context.domain == "test"
        assert context.custom_field == "value"

    def test_context_serialization(self) -> None:
        """Test context can be serialized to dict."""
        context = DomainContext(
            domain="kitchen",
            agent="Alice",
            item="cookie",
            item_plural="cookies",
        )
        data = context.model_dump()

        assert data["domain"] == "kitchen"
        assert data["agent"] == "Alice"
        assert data["item"] == "cookie"
        assert data["item_plural"] == "cookies"


class TestDomainSpecFromDict:
    """Test creating DomainSpec from dict (JSON-like data)."""

    def test_from_dict_minimal(self) -> None:
        """Test creating from minimal dict."""
        data = {"name": "test"}
        domain = DomainSpec(**data)
        assert domain.name == "test"

    def test_from_dict_with_nested(self) -> None:
        """Test creating from dict with nested structures."""
        data = {
            "name": "kitchen",
            "agent_templates": {
                "machine": {"pattern": "Oven ${number}", "numbers": [1, 2]},
            },
            "items": [
                {"singular": "cookie", "plural": "cookies"},
            ],
            "verbs": {"singular": "bakes", "plural": "bake"},
            "time_units": [
                {"singular": "hour", "plural": "hours"},
            ],
        }

        domain = DomainSpec(**data)

        assert domain.name == "kitchen"
        assert "machine" in domain.agent_templates
        assert domain.agent_templates["machine"].pattern == "Oven ${number}"
        assert len(domain.items) == 1
        assert domain.get_verbs().singular == "bakes"
        assert len(domain.time_units) == 1

    def test_from_dict_mixed_items(self) -> None:
        """Test creating from dict with mixed item types."""
        data = {
            "name": "test",
            "items": [
                "simple_string",
                {"singular": "complex", "plural": "complexes"},
            ],
        }

        domain = DomainSpec(**data)
        item_list = domain.get_item_list()

        assert len(item_list) == 2
        assert item_list[0].singular == "simple_string"
        assert item_list[1].singular == "complex"
        assert item_list[1].plural == "complexes"


class TestItemSpecEdgeCases:
    """Edge case tests for ItemSpec."""

    def test_single_letter_word(self) -> None:
        """Test pluralization of single letter."""
        item = ItemSpec(singular="x")
        # Single letter: 'x' ends in 'x', so 'xes'
        assert item.get_plural() == "xes"

    def test_word_ending_in_ay(self) -> None:
        """Test pluralization of words ending in ay."""
        item = ItemSpec(singular="way")
        assert item.get_plural() == "ways"

    def test_word_ending_in_ey(self) -> None:
        """Test pluralization of words ending in ey."""
        item = ItemSpec(singular="monkey")
        assert item.get_plural() == "monkeys"

    def test_word_ending_in_uy(self) -> None:
        """Test pluralization of words ending in uy (vowel+y)."""
        # 'u' is a vowel, so follows vowel+y rule
        item = ItemSpec(singular="colloquy")
        assert item.get_plural() == "colloquys"

    def test_word_ending_in_oy(self) -> None:
        """Test pluralization of words ending in oy."""
        item = ItemSpec(singular="toy")
        assert item.get_plural() == "toys"

    def test_word_ending_in_uy_guy(self) -> None:
        """Test pluralization of words ending in uy (guy example)."""
        item = ItemSpec(singular="guy")
        assert item.get_plural() == "guys"
