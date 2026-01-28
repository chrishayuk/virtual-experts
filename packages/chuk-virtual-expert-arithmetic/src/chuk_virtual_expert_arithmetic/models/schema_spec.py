"""Pydantic models for schema definitions.

These models provide:
- Type safety for schema parsing
- Validation at load time
- Clear documentation of schema structure
- IDE autocompletion support
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VariableSpec(BaseModel):
    """Specification for a variable in a schema.

    Defines how a random value should be generated for this variable.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["int", "float", "bool", "choice"] = "int"
    min: int | float | None = None
    max: int | float | None = None
    precision: int | None = None  # For float types
    options: list[Any] | None = None  # For choice types
    values: list[Any] | None = None  # Alternative to options for choice
    multiple_of: int | None = None  # Constrain to multiples

    # Future: numeric diversity constraints
    requires_carrying: bool = False
    requires_borrowing: bool = False
    avoid_round: bool = False
    difficulty: Literal["easy", "medium", "hard"] | None = None

    @field_validator("options", "values", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> list[Any] | None:
        """Ensure options/values is a list if provided."""
        if v is None:
            return None
        if not isinstance(v, list):
            return [v]
        return v


class VocabSpec(BaseModel):
    """Specification for vocabulary sampling.

    Defines how to sample vocabulary items (names, items, phrases).
    """

    model_config = ConfigDict(extra="forbid")

    type: str | None = None  # "person_with_pronouns", "choice"
    path: str | None = None  # "items.countable_singular", "phrases.activities"
    values: list[Any] | None = None  # For choice type
    sample: int | None = None  # Number of items to sample


class TraceOp(BaseModel):
    """A single operation in the trace sequence.

    Trace operations define the step-by-step computation that solves the problem.
    """

    model_config = ConfigDict(extra="allow")

    op: Literal[
        "init",
        "compute",
        "query",
        "transfer",
        "consume",
        "add_entity",
        "percent_off",
        "percent_increase",
        "percent_of",
    ]

    # Common fields
    var: str | None = None
    value: str | int | float | None = None

    # Compute-specific
    compute_op: Literal["add", "sub", "mul", "div", "floordiv", "mod", "pow"] | None = None
    args: list[str | int | float] | None = None

    # Entity tracking
    entity: str | None = None
    from_entity: str | None = None
    to_entity: str | None = None
    amount: str | int | float | None = None

    # Percentage operations
    base: str | None = None
    rate: str | int | float | None = None

    @field_validator("args", mode="before")
    @classmethod
    def ensure_args_list(cls, v: Any) -> list[Any] | None:
        """Ensure args is a list if provided."""
        if v is None:
            return None
        if not isinstance(v, list):
            return [v]
        return v


class SchemaSpec(BaseModel):
    """Complete schema specification for a problem type.

    This is the main model that validates entire schema JSON files.
    """

    model_config = ConfigDict(extra="allow")

    # Identity
    name: str
    description: str | None = None
    pattern: str | None = None
    variant: str | None = None
    expert: str | None = None

    # Variables
    variables: dict[str, VariableSpec] = Field(default_factory=dict)
    derived: dict[str, str] | None = None
    constraints: dict[str, dict[str, float]] | None = None

    # Vocabulary
    vocab: dict[str, VocabSpec] | None = None
    template_vars: dict[str, str] | None = None

    # Trace definition
    trace: list[TraceOp] = Field(default_factory=list)
    answer: str = "0"

    # Composition support (Phase 4)
    extends: str | None = None
    mixins: list[str] | None = None
    domain: str | None = None
    abstract: bool = False

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables(cls, v: Any) -> dict[str, VariableSpec]:
        """Parse variable specifications from dict."""
        if v is None:
            return {}
        if isinstance(v, dict):
            result: dict[str, VariableSpec] = {
                name: VariableSpec(**spec) if isinstance(spec, dict) else spec
                for name, spec in v.items()
            }
            return result
        return dict(v)

    @field_validator("vocab", mode="before")
    @classmethod
    def parse_vocab(cls, v: Any) -> dict[str, VocabSpec] | None:
        """Parse vocab specifications from dict."""
        if v is None:
            return None
        if isinstance(v, dict):
            result: dict[str, VocabSpec] = {
                name: VocabSpec(**spec) if isinstance(spec, dict) else spec
                for name, spec in v.items()
            }
            return result
        return dict(v)

    @field_validator("trace", mode="before")
    @classmethod
    def parse_trace(cls, v: Any) -> list[TraceOp]:
        """Parse trace operations from list of dicts."""
        if v is None:
            return []
        if isinstance(v, list):
            result: list[TraceOp] = [TraceOp(**op) if isinstance(op, dict) else op for op in v]
            return result
        return list(v)

    def get_required_template_vars(self) -> set[str]:
        """Get the set of template variables this schema provides."""
        provided: set[str] = set()
        if self.template_vars:
            provided.update(self.template_vars.keys())
        if self.variables:
            provided.update(self.variables.keys())
        return provided

    def estimate_trace_depth(self) -> int:
        """Estimate the number of computation steps in the trace."""
        return sum(1 for op in self.trace if op.op == "compute")
