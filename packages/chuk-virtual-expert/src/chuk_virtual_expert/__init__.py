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
    VirtualExpertAction,
    VirtualExpertResult,
)

# Registry
from chuk_virtual_expert.registry_v2 import (
    ExpertRegistry,
    get_registry,
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
    # Expert base
    "VirtualExpert",
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
]

__version__ = "2.0.0"
