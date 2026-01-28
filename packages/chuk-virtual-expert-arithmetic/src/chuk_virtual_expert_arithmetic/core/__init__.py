"""Core components for problem generation.

This module provides the foundational building blocks:
- SafeEvaluator: Secure expression evaluation without eval()
- SchemaLoader: Load and validate JSON schemas
- VariableGenerator: Generate random variable values
- ConstraintValidator: Validate and enforce constraints
- TransformRegistry: Pluggable value transformations
- VocabSampler: Sample vocabulary items
- TemplateResolver: Resolve template variable specs
- DomainSampler: Domain-first vocabulary sampling
- TemplatePerturbator: GSM-8K generalization via perturbation
- NumericDiversifier: Numeric diversity for training
"""

from chuk_virtual_expert_arithmetic.core.composer import CompositionError, SchemaComposer
from chuk_virtual_expert_arithmetic.core.constraints import ConstraintValidator
from chuk_virtual_expert_arithmetic.core.contracts import (
    ContractValidationError,
    ContractValidator,
)
from chuk_virtual_expert_arithmetic.core.domains import DomainSampler
from chuk_virtual_expert_arithmetic.core.expression import (
    ExpressionError,
    SafeEvaluator,
    safe_eval,
)
from chuk_virtual_expert_arithmetic.core.loader import (
    SchemaLoader,
    SchemaLoadError,
    SchemaValidationError,
    get_loader,
)
from chuk_virtual_expert_arithmetic.core.perturbation import (
    NumericDiversifier,
    TemplatePerturbator,
)
from chuk_virtual_expert_arithmetic.core.resolver import TemplateResolver
from chuk_virtual_expert_arithmetic.core.sampler import VocabSampler
from chuk_virtual_expert_arithmetic.core.transforms import (
    TransformError,
    TransformRegistry,
    capitalize,
    pluralize,
    singularize,
    with_article,
)
from chuk_virtual_expert_arithmetic.core.variables import DifficultyProfile, VariableGenerator

__all__ = [
    # Expression evaluation
    "SafeEvaluator",
    "ExpressionError",
    "safe_eval",
    # Schema loading
    "SchemaLoader",
    "SchemaLoadError",
    "SchemaValidationError",
    "get_loader",
    # Schema composition
    "SchemaComposer",
    "CompositionError",
    # Variables
    "VariableGenerator",
    "DifficultyProfile",
    # Constraints
    "ConstraintValidator",
    # Contracts
    "ContractValidator",
    "ContractValidationError",
    # Transforms
    "TransformRegistry",
    "TransformError",
    "pluralize",
    "singularize",
    "capitalize",
    "with_article",
    # Vocab sampling
    "VocabSampler",
    # Domain sampling
    "DomainSampler",
    # Template resolution
    "TemplateResolver",
    # Perturbation & diversity (GSM-8K generalization)
    "TemplatePerturbator",
    "NumericDiversifier",
]
