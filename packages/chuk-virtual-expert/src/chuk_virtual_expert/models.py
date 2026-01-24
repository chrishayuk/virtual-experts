"""
Pydantic models for virtual expert system.

Clean, type-safe models with no magic strings.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CommonOperation(str, Enum):
    """Common operations shared by all experts."""

    EXECUTE = "execute"  # Generic execution
    PASSTHROUGH = "passthrough"  # Pass to base model


# Constants for special expert names
NONE_EXPERT = "none"


class VirtualExpertAction(BaseModel):
    """
    Structured action for virtual expert invocation.

    This is the normalized format that CoT produces from any query phrasing.
    The calibration router is trained on this format.

    Example:
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"timezone": "Asia/Tokyo"},
            confidence=0.95,
            reasoning="User asking for current time in Tokyo"
        )
    """

    expert: str = Field(
        description="Name of the virtual expert to invoke, or 'none' for passthrough"
    )
    operation: str = Field(description="Specific operation to perform")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the operation"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Model's confidence in this action (0-1)"
    )
    reasoning: str = Field(default="", description="CoT reasoning that led to this action")

    @classmethod
    def none_action(cls, reasoning: str = "") -> VirtualExpertAction:
        """Create a 'no action' response for passthrough to base model."""
        return cls(
            expert=NONE_EXPERT,
            operation=CommonOperation.PASSTHROUGH,
            confidence=1.0,
            reasoning=reasoning,
        )

    def is_passthrough(self) -> bool:
        """Check if this action should pass through to base model."""
        return self.expert == NONE_EXPERT or self.operation == CommonOperation.PASSTHROUGH


class VirtualExpertResult(BaseModel):
    """
    Result from virtual expert execution.

    Contains structured data that the model can use for chain-of-thought
    reasoning and response formatting.
    """

    data: dict[str, Any] | None = Field(
        default=None, description="Structured result data from the expert"
    )
    expert_name: str = Field(description="Name of the expert that produced this result")
    success: bool = Field(default=True, description="Whether the expert executed successfully")
    error: str | None = Field(default=None, description="Error message if execution failed")
    action: VirtualExpertAction | None = Field(
        default=None, description="The action that was executed"
    )

    @property
    def query_type(self) -> str | None:
        """Extract query_type from data if present."""
        if self.data:
            return self.data.get("query_type")
        return None


class DispatchResult(BaseModel):
    """Result from the dispatcher."""

    action: VirtualExpertAction = Field(description="The action that was dispatched")
    result: VirtualExpertResult | None = Field(
        default=None, description="Result from virtual expert execution, if any"
    )

    @property
    def was_handled(self) -> bool:
        """Check if a virtual expert handled this request."""
        return self.result is not None and not self.action.is_passthrough()


class CoTExample(BaseModel):
    """
    A single CoT training example.

    Maps a user query to the expected VirtualExpertAction.
    Used for both few-shot prompting and model fine-tuning.
    """

    query: str = Field(description="User's natural language query")
    action: VirtualExpertAction = Field(description="Expected action for this query")

    def to_few_shot_format(self) -> str:
        """Format as a few-shot example for the prompt."""
        action_json = self.action.model_dump_json(exclude_none=True)
        return f'Query: "{self.query}"\nAction: {action_json}'


class CoTExamples(BaseModel):
    """
    Collection of CoT training examples for a virtual expert.

    Loaded from cot_examples.json in the expert's package.
    """

    expert_name: str = Field(description="Name of the virtual expert these examples are for")
    examples: list[CoTExample] = Field(
        default_factory=list, description="List of query → action mappings"
    )

    def get_few_shot_prompt(self, max_examples: int = 5) -> str:
        """Generate few-shot examples for the extraction prompt."""
        examples = self.examples[:max_examples]
        return "\n\n".join(ex.to_few_shot_format() for ex in examples)

    @property
    def positive_actions(self) -> list[str]:
        """Get actions that SHOULD route to this expert (for calibration)."""
        return [
            ex.action.model_dump_json()
            for ex in self.examples
            if ex.action.expert == self.expert_name
        ]

    @property
    def negative_actions(self) -> list[str]:
        """Get actions that should NOT route to this expert (for calibration)."""
        return [
            ex.action.model_dump_json()
            for ex in self.examples
            if ex.action.expert != self.expert_name
        ]


class OperationSchema(BaseModel):
    """Schema for a single expert operation."""

    name: str = Field(description="Operation name")
    description: str = Field(description="What this operation does")
    parameters: dict[str, ParameterSchema] = Field(
        default_factory=dict, description="Parameters this operation accepts"
    )


class ParameterSchema(BaseModel):
    """Schema for an operation parameter."""

    type: str = Field(description="Parameter type: string, number, boolean, etc.")
    description: str = Field(description="What this parameter is for")
    required: bool = Field(default=False, description="Whether this parameter is required")
    default: Any = Field(default=None, description="Default value if not provided")
    enum: list[Any] | None = Field(default=None, description="Allowed values if restricted")


class ExpertSchema(BaseModel):
    """
    Full schema describing a virtual expert's capabilities.

    Used to generate prompts and validate operations.
    """

    name: str = Field(description="Expert name")
    description: str = Field(description="What this expert does")
    operations: dict[str, OperationSchema] = Field(
        default_factory=dict, description="Available operations"
    )

    def get_operations_summary(self) -> str:
        """Get a summary of operations for prompts."""
        lines = []
        for op_name, op in self.operations.items():
            params = ", ".join(
                f"{p}{'*' if schema.required else ''}" for p, schema in op.parameters.items()
            )
            lines.append(f"  - {op_name}({params}): {op.description}")
        return "\n".join(lines)


# --- Trace Execution Models ---


class TraceResult(BaseModel):
    """Result from executing a trace."""

    success: bool = Field(default=False, description="Whether trace executed without errors")
    answer: Any = Field(default=None, description="Computed answer from trace")
    state: dict[str, Any] = Field(default_factory=dict, description="Final state after execution")
    error: str | None = Field(default=None, description="Error message if execution failed")
    expert: str = Field(default="", description="Expert that executed the trace")
    steps_executed: int = Field(default=0, description="Number of steps successfully executed")


class VerificationResult(BaseModel):
    """Result from verifying a trace against expected answer."""

    parsed: bool = Field(default=False, description="Whether YAML was parsed successfully")
    expert: str | None = Field(default=None, description="Expert name from trace")
    trace_valid: bool = Field(default=False, description="Whether trace executed without errors")
    trace_error: str | None = Field(default=None, description="Error if trace failed")
    computed_answer: Any = Field(default=None, description="Answer computed by executing trace")
    expected_answer: Any = Field(default=None, description="Expected answer for comparison")
    answer_correct: bool = Field(default=False, description="Whether computed matches expected")
    final_state: dict[str, Any] = Field(default_factory=dict, description="Final variable state")
    reward: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Graduated reward score (0.0-1.0)"
    )
