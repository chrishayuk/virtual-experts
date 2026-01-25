"""
chuk-virtual-expert: Base specification for virtual experts.

Virtual experts are specialized plugins that language models can route to
for domain-specific tasks. This package provides:

1. VirtualExpert - Pydantic base class for experts
2. VirtualExpertAction - Structured action format for CoT dispatch
3. ExpertRegistry - Registration and lookup
4. Dispatcher - CoT-based routing to experts
5. LazarusAdapter - Bridge to Lazarus MoE routing

Architecture:
    Query → CoT Rewrite → VirtualExpertAction → Calibration Router → Expert

Example:
    from chuk_virtual_expert import ExpertRegistry, Dispatcher
    from chuk_virtual_expert.models import VirtualExpertAction

    # Register experts
    registry = ExpertRegistry()
    registry.register(TimeExpert())

    # Dispatch via CoT
    dispatcher = Dispatcher(registry=registry)
    dispatcher.set_extractor(llm_extractor)
    result = dispatcher.dispatch("What time is it in Tokyo?")
"""

# Core models (Pydantic)
# Dispatcher
from chuk_virtual_expert.dispatch import (
    ActionExtractor,
    CalibrationData,
    Dispatcher,
    FewShotExtractor,
)

# Base class for experts
from chuk_virtual_expert.expert import VirtualExpert

# MCP-backed expert base class
try:
    from chuk_virtual_expert.mcp_expert import MCPExpert, MCPTransportType
except ImportError:
    # chuk-mcp not installed
    MCPExpert = None  # type: ignore[assignment, misc]
    MCPTransportType = None  # type: ignore[assignment, misc]

# Lazarus integration
from chuk_virtual_expert.lazarus import (
    LazarusAdapter,
    adapt_expert,
)
from chuk_virtual_expert.models import (
    NONE_EXPERT,
    CommonOperation,
    CoTExample,
    CoTExamples,
    DispatchResult,
    ExpertSchema,
    OperationSchema,
    ParameterSchema,
    TraceResult,
    VerificationResult,
    VirtualExpertAction,
    VirtualExpertResult,
)

# Registry
from chuk_virtual_expert.registry_v2 import (
    ExpertRegistry,
    get_registry,
)

# Typed trace models
from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ALL_STEP_TYPES,
    AddEntityStep,
    BaseTraceStep,
    CompareStep,
    ComputeOp,
    ComputeStep,
    ConsumeStep,
    ConvertTimeStep,
    FormulaStep,
    GeocodeStep,
    GetAirQualityStep,
    GetForecastStep,
    GetHistoricalStep,
    GetMarineStep,
    GetTimeStep,
    GetTimezoneInfoStep,
    GivenStep,
    InitStep,
    InterpretCodeStep,
    PercentIncreaseStep,
    PercentOffStep,
    PercentOfStep,
    QueryStep,
    StateAssertStep,
    TraceStep,
    TransferStep,
)

# Trace execution
from chuk_virtual_expert.composition_solver import CompositionSolver
from chuk_virtual_expert.trace_solver import TraceSolverExpert
from chuk_virtual_expert.trace_verifier import TraceVerifier

# Validation
from chuk_virtual_expert.validation import (
    FewShotValidator,
    ValidationResult,
    ValidationSummary,
    validate_expert_few_shot,
)

__all__ = [
    # Core models
    "CommonOperation",
    "NONE_EXPERT",
    "VirtualExpertAction",
    "VirtualExpertResult",
    "DispatchResult",
    "CoTExample",
    "CoTExamples",
    "ExpertSchema",
    "OperationSchema",
    "ParameterSchema",
    "TraceResult",
    "VerificationResult",
    # Typed trace step models
    "BaseTraceStep",
    "TraceStep",
    "ComputeOp",
    "InitStep",
    "GivenStep",
    "ComputeStep",
    "FormulaStep",
    "QueryStep",
    "StateAssertStep",
    "TransferStep",
    "ConsumeStep",
    "AddEntityStep",
    "PercentOffStep",
    "PercentIncreaseStep",
    "PercentOfStep",
    "CompareStep",
    "GeocodeStep",
    "GetForecastStep",
    "GetHistoricalStep",
    "GetAirQualityStep",
    "GetMarineStep",
    "InterpretCodeStep",
    "GetTimeStep",
    "ConvertTimeStep",
    "GetTimezoneInfoStep",
    "ALL_STEP_TYPES",
    # Trace example
    "TraceExample",
    # Expert base classes
    "VirtualExpert",
    "TraceSolverExpert",
    "CompositionSolver",
    "MCPExpert",
    "MCPTransportType",
    # Trace verification
    "TraceVerifier",
    # Registry
    "ExpertRegistry",
    "get_registry",
    # Dispatcher
    "ActionExtractor",
    "FewShotExtractor",
    "Dispatcher",
    "CalibrationData",
    # Lazarus integration
    "LazarusAdapter",
    "adapt_expert",
    # Validation
    "FewShotValidator",
    "ValidationResult",
    "ValidationSummary",
    "validate_expert_few_shot",
]

__version__ = "3.0.0"
