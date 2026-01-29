"""Pydantic models for schema validation and type safety.

This module provides:
- Schema models (SchemaSpec, TraceOp, VariableSpec, VocabSpec)
- Domain models (DomainSpec, DomainContext, AgentTemplate, ItemSpec, VerbSpec)
- Configuration models (GenerationConfig, DiversityConfig, BatchConfig)

All models use enums from chuk_virtual_expert_arithmetic.types for type safety.
"""

from chuk_virtual_expert_arithmetic.models.config import (
    BatchConfig,
    ConstraintConfig,
    DiversityConfig,
    GenerationConfig,
    TraceExampleConfig,
)
from chuk_virtual_expert_arithmetic.models.domain import (
    AgentTemplate,
    DomainContext,
    DomainSpec,
    ItemSpec,
    TimeUnitSpec,
    VerbSpec,
)
from chuk_virtual_expert_arithmetic.models.schema_spec import (
    SchemaSpec,
    TraceOp,
    VariableSpec,
    VocabSpec,
)

__all__ = [
    # Schema models
    "SchemaSpec",
    "TraceOp",
    "VariableSpec",
    "VocabSpec",
    # Domain models
    "DomainSpec",
    "DomainContext",
    "AgentTemplate",
    "ItemSpec",
    "VerbSpec",
    "TimeUnitSpec",
    # Configuration models
    "GenerationConfig",
    "DiversityConfig",
    "ConstraintConfig",
    "BatchConfig",
    "TraceExampleConfig",
]
