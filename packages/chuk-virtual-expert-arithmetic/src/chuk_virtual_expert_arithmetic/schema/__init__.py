"""Problem and trace schema for arithmetic virtual experts."""

from chuk_virtual_expert_arithmetic.schema.problem import (
    Constraint,
    Entity,
    Operation,
    OperationType,
    ProblemSpec,
    ProblemType,
    Query,
)
from chuk_virtual_expert_arithmetic.schema.trace import (
    Action,
    State,
    Step,
    Trace,
    TraceBuilder,
    apply_action,
)
from chuk_virtual_expert_arithmetic.schema.verifier import (
    StepError,
    TraceVerifier,
    VerificationResult,
    VerificationStatus,
    verify_trace,
    verify_traces,
)

__all__ = [
    "ProblemType",
    "OperationType",
    "Entity",
    "Operation",
    "Query",
    "Constraint",
    "ProblemSpec",
    "Action",
    "State",
    "Step",
    "Trace",
    "TraceBuilder",
    "apply_action",
    "VerificationStatus",
    "StepError",
    "VerificationResult",
    "TraceVerifier",
    "verify_trace",
    "verify_traces",
]
