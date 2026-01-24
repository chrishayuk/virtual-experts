"""
TraceExample model for typed training examples.

Each expert's generator produces TraceExample instances
that can be serialized via .model_dump() for training data.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from chuk_virtual_expert.trace_models import TraceStep


class TraceExample(BaseModel):
    """
    A typed training example with a query and its trace solution.

    Generators produce these for each expert. Call .model_dump()
    to serialize for training pipelines.
    """

    expert: str = Field(description="Name of the expert that handles this trace")
    query: str = Field(description="Natural language query this trace solves")
    trace: list[TraceStep] = Field(default_factory=list, description="Ordered typed trace steps")
    answer: float | str | None = Field(
        default=None, description="Expected answer from executing the trace"
    )
    expected_operation: str | None = Field(
        default=None, description="Expected operation name for routing validation"
    )
    expected_params: dict[str, Any] | None = Field(
        default=None, description="Expected parameters for routing validation"
    )
    multi_step: bool = Field(default=False, description="Whether this is a multi-step trace")
