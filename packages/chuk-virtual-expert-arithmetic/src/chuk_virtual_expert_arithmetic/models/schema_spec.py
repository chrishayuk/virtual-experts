"""Pydantic models for schema definitions.

These models provide:
- Type safety for schema parsing
- Validation at load time
- Clear documentation of schema structure
- IDE autocompletion support

All models use enums from chuk_virtual_expert_arithmetic.types for
type-safe operation and variable type handling.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from chuk_virtual_expert_arithmetic.types import (
    ComputeOpType,
    DifficultyLevel,
    TraceOpType,
    VariableType,
    VocabSpecType,
)


class VariableSpec(BaseModel):
    """Specification for a variable in a schema.

    Defines how a random value should be generated for this variable.

    Example:
        >>> spec = VariableSpec(type=VariableType.INT, min=1, max=10)
        >>> spec = VariableSpec(type="int", min=1, max=10)  # Also works
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    type: VariableType | str = VariableType.INT
    min: int | float | None = None
    max: int | float | None = None
    precision: int | None = None  # For float types
    options: list[Any] | None = None  # For choice types
    values: list[Any] | None = None  # Alternative to options for choice
    multiple_of: int | None = None  # Constrain to multiples

    # Numeric diversity constraints
    requires_carrying: bool = False
    requires_borrowing: bool = False
    avoid_round: bool = False
    difficulty: DifficultyLevel | str | None = None

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

    Example:
        >>> spec = VocabSpec(type=VocabSpecType.PERSON_WITH_PRONOUNS)
        >>> spec = VocabSpec(path="items.countable_singular")
        >>> spec = VocabSpec(type=VocabSpecType.CHOICE, values=["a", "b", "c"])
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    type: VocabSpecType | str | None = None
    path: str | None = None  # Vocab path like "items.countable_singular"
    values: list[Any] | None = None  # For choice type
    sample: int | None = None  # Number of items to sample
    distinct_from: list[str] | None = None  # Vocab keys to exclude from sampling
    domain: str | None = None  # Domain name for domain_context type


class TraceOp(BaseModel):
    """A single operation in the trace sequence.

    Trace operations define the step-by-step computation that solves the problem.

    Example:
        >>> op = TraceOp(op=TraceOpType.INIT, var="x", value=5)
        >>> op = TraceOp(op=TraceOpType.COMPUTE, compute_op=ComputeOpType.ADD, args=["x", "y"], var="z")
        >>> op = TraceOp(op="init", var="x", value=5)  # String also works
    """

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    op: TraceOpType | str

    # Common fields
    var: str | None = None
    value: str | int | float | None = None

    # Compute-specific
    compute_op: ComputeOpType | str | None = None
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

    def is_compute(self) -> bool:
        """Check if this is a compute operation."""
        return self.op == TraceOpType.COMPUTE or self.op == "compute"

    def is_init(self) -> bool:
        """Check if this is an init operation."""
        return self.op == TraceOpType.INIT or self.op == "init"

    def is_query(self) -> bool:
        """Check if this is a query operation."""
        return self.op == TraceOpType.QUERY or self.op == "query"


class SchemaSpec(BaseModel):
    """Complete schema specification for a problem type.

    This is the main model that validates entire schema JSON files.

    Example:
        >>> schema = SchemaSpec(
        ...     name="add_two",
        ...     variables={"a": VariableSpec(min=1, max=10), "b": VariableSpec(min=1, max=10)},
        ...     trace=[
        ...         TraceOp(op=TraceOpType.INIT, var="a", value="a"),
        ...         TraceOp(op=TraceOpType.INIT, var="b", value="b"),
        ...         TraceOp(op=TraceOpType.COMPUTE, compute_op=ComputeOpType.ADD, args=["a", "b"], var="result"),
        ...         TraceOp(op=TraceOpType.QUERY, var="result"),
        ...     ],
        ...     answer="a + b",
        ... )
    """

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    # Identity
    name: str
    description: str | None = None
    pattern: str | None = None
    variant: str | None = None
    expert: str | None = None  # ExpertType value or custom string

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

    # Composition support
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
        return sum(1 for op in self.trace if op.is_compute())

    def get_compute_ops(self) -> list[TraceOp]:
        """Get all compute operations in the trace."""
        return [op for op in self.trace if op.is_compute()]

    def get_init_ops(self) -> list[TraceOp]:
        """Get all init operations in the trace."""
        return [op for op in self.trace if op.is_init()]

    def get_query_op(self) -> TraceOp | None:
        """Get the query operation (usually the last one)."""
        for op in reversed(self.trace):
            if op.is_query():
                return op
        return None
