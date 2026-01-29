"""Pydantic models for domain definitions.

Domains provide semantically coherent vocabulary bundles for problem generation.
Each domain groups related agents, items, verbs, and time units.

Example domain (kitchen):
    - Agents: Oven 1, Oven 2, Baker, Chef
    - Items: cookies, cakes, loaves
    - Verbs: bakes, makes
    - Time units: hours, minutes
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AgentTemplate(BaseModel):
    """Template for generating agent names.

    Supports patterns like:
    - "Machine ${number}" with numbers: [1, 2, 3]
    - "Worker ${letter}" with letters: ["A", "B", "C"]
    - "${name}" with source: "names.male"
    """

    model_config = ConfigDict(extra="allow")

    pattern: str = "${name}"
    numbers: list[int] | None = None
    letters: list[str] | None = None
    source: str | None = None  # Vocab path for name sampling


class ItemSpec(BaseModel):
    """Specification for an item with singular/plural forms."""

    model_config = ConfigDict(extra="allow")

    singular: str
    plural: str | None = None  # Auto-generated if not provided

    def get_plural(self) -> str:
        """Get the plural form, auto-generating if needed."""
        if self.plural:
            return self.plural
        # Simple pluralization
        word = self.singular
        if word.endswith(("s", "x", "ch", "sh")):
            return word + "es"
        elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        return word + "s"


class VerbSpec(BaseModel):
    """Specification for verbs with conjugation forms."""

    model_config = ConfigDict(extra="allow")

    singular: str  # "bakes"
    plural: str  # "bake"
    base: str | None = None  # "bake"
    gerund: str | None = None  # "baking"
    past: str | None = None  # "baked"


class TimeUnitSpec(BaseModel):
    """Specification for time units."""

    model_config = ConfigDict(extra="allow")

    singular: str  # "hour"
    plural: str  # "hours"


class DomainSpec(BaseModel):
    """Complete domain specification for semantic vocabulary coherence.

    A domain groups related vocabulary items that make sense together.

    Example:
        >>> domain = DomainSpec(
        ...     name="kitchen",
        ...     description="Baking and cooking domain",
        ...     agent_templates={
        ...         "machine": AgentTemplate(pattern="Oven ${number}", numbers=[1, 2]),
        ...         "person": AgentTemplate(pattern="${name}", source="names.chefs"),
        ...     },
        ...     items=[
        ...         ItemSpec(singular="cookie", plural="cookies"),
        ...         ItemSpec(singular="cake", plural="cakes"),
        ...     ],
        ...     verbs=VerbSpec(singular="bakes", plural="bake"),
        ...     time_units=[
        ...         TimeUnitSpec(singular="hour", plural="hours"),
        ...     ],
        ... )
    """

    model_config = ConfigDict(extra="allow")

    name: str
    description: str | None = None

    # Agent templates keyed by type (machine, person, etc.)
    agent_templates: dict[str, AgentTemplate] = Field(default_factory=dict)

    # Items that can be processed in this domain
    items: list[ItemSpec | str] = Field(default_factory=list)

    # Verbs for actions in this domain
    verbs: VerbSpec | dict[str, str] | None = None

    # Time units used in this domain
    time_units: list[TimeUnitSpec] = Field(default_factory=list)

    def get_item_list(self) -> list[ItemSpec]:
        """Get all items as ItemSpec objects."""
        result: list[ItemSpec] = []
        for item in self.items:
            if isinstance(item, str):
                result.append(ItemSpec(singular=item))
            else:
                result.append(item)
        return result

    def get_verbs(self) -> VerbSpec:
        """Get verbs as VerbSpec, converting from dict if needed."""
        if self.verbs is None:
            return VerbSpec(singular="processes", plural="process")
        if isinstance(self.verbs, dict):
            return VerbSpec(**self.verbs)
        return self.verbs


class DomainContext(BaseModel):
    """Sampled context from a domain for template substitution.

    This is the output of DomainSampler.sample() with all values resolved.
    """

    model_config = ConfigDict(extra="allow")

    domain: str
    agent: str
    agent2: str | None = None
    agent_type: str = "person"
    item: str = "item"
    item_plural: str = "items"
    verb: str = "has"
    verb_plural: str = "have"
    time_unit: str | None = None
    time_unit_plural: str | None = None
