"""
chuk-virtual-expert-arithmetic: Arithmetic trace-solving virtual experts.

Provides 5 specialized experts for different math problem types:
- ArithmeticExpert: Pure arithmetic chains
- EntityTrackExpert: Entity state tracking (gives, loses, transfers)
- PercentageExpert: Percentage calculations (discounts, increases)
- RateEquationExpert: Rate/formula-based problems
- ComparisonExpert: Comparison and difference calculations

Package structure:
- experts/: Inference code (TraceSolverExpert subclasses)
- data/: Training data (calibration prompts, CoT examples)
- generators/: Data generation utilities
- core/: Foundational components (expression eval, schema loading, etc.)
- models/: Pydantic models for schema validation
"""

from chuk_virtual_expert_arithmetic.core import (
    ConstraintValidator,
    SafeEvaluator,
    SchemaLoader,
    TemplateResolver,
    TransformRegistry,
    VariableGenerator,
    VocabSampler,
)
from chuk_virtual_expert_arithmetic.experts.arithmetic import ArithmeticExpert
from chuk_virtual_expert_arithmetic.experts.comparison import ComparisonExpert
from chuk_virtual_expert_arithmetic.experts.entity_track import EntityTrackExpert
from chuk_virtual_expert_arithmetic.experts.percentage import PercentageExpert
from chuk_virtual_expert_arithmetic.experts.rate_equation import RateEquationExpert
from chuk_virtual_expert_arithmetic.generators import TraceGenerator
from chuk_virtual_expert_arithmetic.models import SchemaSpec, TraceOp, VariableSpec, VocabSpec
from chuk_virtual_expert_arithmetic.types import ExpertType

__all__ = [
    # Experts
    "ArithmeticExpert",
    "EntityTrackExpert",
    "PercentageExpert",
    "RateEquationExpert",
    "ComparisonExpert",
    # Generators
    "TraceGenerator",
    # Types
    "ExpertType",
    # Models
    "SchemaSpec",
    "VariableSpec",
    "VocabSpec",
    "TraceOp",
    # Core components
    "SafeEvaluator",
    "SchemaLoader",
    "VariableGenerator",
    "ConstraintValidator",
    "TransformRegistry",
    "VocabSampler",
    "TemplateResolver",
]

__version__ = "1.0.0"
