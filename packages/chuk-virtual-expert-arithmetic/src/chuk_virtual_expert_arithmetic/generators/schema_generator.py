"""Schema-based generator for arithmetic problems.

Generates problems from JSON schema definitions, reducing hardcoded logic.

Architecture:
    This module uses the following core components:
    - SchemaLoader: Loads and composes schemas (handles mixins/extends)
    - SafeEvaluator: Secure expression evaluation (replaces eval())
    - TemplatePerturbator: GSM-8K generalization via query perturbation

    For new development, consider using the standalone core components:
    - core.VariableGenerator: Variable generation with difficulty/diversity
    - core.ConstraintValidator: Constraint validation with retry logic
    - core.TransformRegistry: Pluggable value transformations
    - core.TemplateResolver: Template variable resolution
    - core.VocabSampler: Vocabulary sampling
    - core.DomainSampler: Domain-first vocabulary bundles

Usage:
    from chuk_virtual_expert_arithmetic.generators.schema_generator import SchemaGenerator

    gen = SchemaGenerator()
    example = gen.generate("price_chain")
    examples = gen.generate_batch(["price_chain", "subtract_chain"], n=10)

    # With perturbation for GSM-8K generalization
    gen = SchemaGenerator(perturbation_level=0.5)
"""

from __future__ import annotations

import random
import re
from typing import Any

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    AddEntityStep,
    ComputeOp,
    ComputeStep,
    ConsumeStep,
    InitStep,
    PercentIncreaseStep,
    PercentOffStep,
    PercentOfStep,
    QueryStep,
    TransferStep,
)

from chuk_virtual_expert_arithmetic.core.expression import ExpressionError, SafeEvaluator
from chuk_virtual_expert_arithmetic.core.loader import SchemaLoader
from chuk_virtual_expert_arithmetic.core.perturbation import TemplatePerturbator
from chuk_virtual_expert_arithmetic.types import DEFAULT_EXPERT
from chuk_virtual_expert_arithmetic.vocab import get_vocab

# Word number mappings
WORD_NUMBERS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
    21: "twenty-one",
    22: "twenty-two",
    23: "twenty-three",
    24: "twenty-four",
    25: "twenty-five",
    30: "thirty",
    40: "forty",
    50: "fifty",
}


class SchemaGenerator:
    """Generates arithmetic problems from JSON schemas."""

    def __init__(
        self,
        word_number_prob: float = 0.3,
        perturbation_level: float = 0.0,
        seed: int | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            word_number_prob: Probability of converting a number to word form (0-1).
                             Word problems commonly use word numbers ~30% of the time.
            perturbation_level: Level of template perturbation (0-1). Higher values
                               apply more variations for better GSM-8K generalization.
                               0 = no perturbation (default), 0.3 = moderate, 0.6 = high.
            seed: Random seed for reproducibility.
        """
        self._vocab = get_vocab()
        self._loader = SchemaLoader()
        self._schemas = self._load_schemas()
        self._word_number_prob = word_number_prob
        self._perturbation_level = perturbation_level
        self._evaluator = SafeEvaluator()
        self._perturbator = TemplatePerturbator(seed=seed)

    def _load_schemas(self) -> dict[str, dict[str, Any]]:
        """Load all schemas using SchemaLoader (handles composition/mixins)."""
        raw_schemas = self._loader.get_all_raw()
        composed_schemas: dict[str, dict[str, Any]] = {}

        for name, raw in raw_schemas.items():
            # Use loader to get composed schema (handles mixins/extends)
            try:
                # Load raw and compose if needed
                if "extends" in raw or "mixins" in raw:
                    composed = self._loader._get_composer().compose(raw)
                    composed_schemas[name] = composed
                else:
                    composed_schemas[name] = raw
            except Exception:
                # If composition fails, use raw
                composed_schemas[name] = raw

        return composed_schemas

    @property
    def schema_names(self) -> list[str]:
        """List available schema names."""
        return list(self._schemas.keys())

    @property
    def perturbation_level(self) -> float:
        """Get current perturbation level."""
        return self._perturbation_level

    @perturbation_level.setter
    def perturbation_level(self, level: float) -> None:
        """Set perturbation level (0-1)."""
        self._perturbation_level = max(0.0, min(1.0, level))

    def generate(self, schema_name: str) -> TraceExample:
        """Generate a problem from a schema.

        Args:
            schema_name: Name of the schema to use

        Returns:
            TraceExample with query, trace, and answer
        """
        schema = self._schemas.get(schema_name)
        if not schema:
            raise ValueError(f"Unknown schema: {schema_name}")

        # Generate random variables
        variables = self._generate_variables(schema.get("variables", {}))

        # Generate derived variables
        derived = self._compute_derived(schema.get("derived", {}), variables)
        variables.update(derived)

        # Check and fix constraints
        variables = self._apply_constraints(schema.get("constraints", {}), variables, schema)

        # Sample vocab items
        vocab_items = self._sample_vocab(schema.get("vocab", {}))

        # Build template variables
        template_vars = self._build_template_vars(
            schema.get("template_vars", {}), variables, vocab_items
        )

        # Add numeric variables directly to template vars
        template_vars.update(variables)

        # Auto-add multiplier word mapping if multiplier variable exists
        if "multiplier" in variables:
            mult = variables["multiplier"]
            mult_words = {2: "twice", 3: "three times", 4: "four times", 5: "five times"}
            growth_words = {2: "doubled", 3: "tripled", 4: "quadrupled", 5: "quintupled"}
            template_vars["mult_word"] = mult_words.get(mult, f"{mult} times")
            template_vars["growth_word"] = growth_words.get(mult, f"multiplied by {mult}")

        # Add sampled vocab items
        for key, value in vocab_items.items():
            if isinstance(value, dict):
                # Handle structured vocab (e.g., person_with_pronouns)
                for k, v in value.items():
                    template_vars[f"{key}_{k}"] = v
                # Auto-add common pronoun shortcuts when 'person' is sampled
                if "name" in value and "subject" in value:
                    # This is a person - add common shortcuts
                    if key == "person":
                        template_vars["name"] = value.get("name")
                        template_vars["subject"] = value.get("subject")
                        template_vars["subj"] = value.get("subject", "").capitalize()
                        template_vars["his_her"] = value.get("possessive")
                        template_vars["him_her"] = value.get("object")
                        template_vars["reflexive"] = value.get("reflexive")
                        template_vars["verb_s"] = value.get("verb_s", "s")
                    elif key.startswith("person"):
                        # person1, person2, etc.
                        suffix = key[6:]  # "1", "2", etc.
                        template_vars[f"name{suffix}"] = value.get("name")
                        template_vars[f"subject{suffix}"] = value.get("subject")
                        template_vars[f"subj{suffix}"] = value.get("subject", "").capitalize()
                        template_vars[f"his_her{suffix}"] = value.get("possessive")
            elif isinstance(value, list):
                # Handle sampled lists
                for i, item in enumerate(value):
                    template_vars[f"{key}_{i}"] = item
            else:
                template_vars[key] = value

        # Generate question from pattern
        pattern = schema["pattern"]
        variant = schema.get("variant")
        question = self._vocab.pattern(pattern, variant, **template_vars)

        # Apply word number substitution
        question = self._apply_word_numbers(question)

        # Apply perturbation for GSM-8K generalization
        if self._perturbation_level > 0:
            question = self._perturbator.perturb(question, level=self._perturbation_level)

        # Build trace
        trace = self._build_trace(schema.get("trace", []), variables)

        # Compute answer
        answer = self._compute_answer(schema.get("answer", "0"), variables)

        # Get expert from schema, with default
        expert_name = schema.get("expert", DEFAULT_EXPERT.value)

        return TraceExample(
            expert=expert_name,
            query=question,
            trace=trace,
            answer=answer,
            expected_operation="execute_trace",
        )

    def generate_batch(
        self, schema_names: list[str] | None = None, n: int = 10
    ) -> list[TraceExample]:
        """Generate multiple problems.

        Args:
            schema_names: List of schemas to use (None = all)
            n: Number of problems to generate

        Returns:
            List of TraceExamples
        """
        if schema_names is None:
            schema_names = self.schema_names

        examples = []
        for _ in range(n):
            schema_name = random.choice(schema_names)
            examples.append(self.generate(schema_name))

        return examples

    def _generate_variables(self, var_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Generate random values for variables."""
        variables = {}

        for name, spec in var_specs.items():
            var_type = spec.get("type", "int")

            if var_type == "int":
                min_val = spec.get("min", 1)
                max_val = spec.get("max", 100)
                value = random.randint(min_val, max_val)

                # Handle multiple_of constraint
                if "multiple_of" in spec:
                    mult = spec["multiple_of"]
                    value = (value // mult) * mult
                    if value < min_val:
                        value += mult

                variables[name] = value

            elif var_type == "float":
                min_val = spec.get("min", 0.0)
                max_val = spec.get("max", 10.0)
                precision = spec.get("precision", 2)
                value = round(random.uniform(min_val, max_val), precision)
                variables[name] = value

            elif var_type == "bool":
                variables[name] = random.choice([True, False])

            elif var_type == "choice":
                # Support both "options" and "values" for choice type
                options = spec.get("options") or spec.get("values", [])
                variables[name] = random.choice(options) if options else 0

        return variables

    def _compute_derived(
        self, derived_specs: dict[str, str], variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute derived variables from expressions.

        Expressions are evaluated in order, so later expressions can
        reference earlier derived values.
        """
        derived = {}
        # Create a combined context that includes both base variables and derived
        context = dict(variables)

        for name, expr in derived_specs.items():
            try:
                # Safe expression evaluation using AST parser
                value = self._evaluator.evaluate(expr, context)
                derived[name] = value
                # Add to context so later expressions can reference it
                context[name] = value
            except ExpressionError:
                derived[name] = 0
                context[name] = 0

        return derived

    def _apply_constraints(
        self,
        constraints: dict[str, dict[str, Any]],
        variables: dict[str, Any],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply constraints, regenerating if needed."""
        max_attempts = 10

        for _ in range(max_attempts):
            all_satisfied = True

            for expr, bounds in constraints.items():
                try:
                    # Safe expression evaluation using AST parser
                    value = self._evaluator.evaluate(expr, variables)
                    min_val = bounds.get("min", float("-inf"))
                    max_val = bounds.get("max", float("inf"))

                    if not (min_val <= value <= max_val):
                        all_satisfied = False
                        break
                except ExpressionError:
                    pass

            if all_satisfied:
                return variables

            # Regenerate variables
            variables = self._generate_variables(schema.get("variables", {}))
            derived = self._compute_derived(schema.get("derived", {}), variables)
            variables.update(derived)

        return variables

    def _sample_vocab(self, vocab_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Sample vocabulary items."""
        items: dict[str, Any] = {}

        for name, spec in vocab_specs.items():
            if spec.get("type") == "person_with_pronouns":
                items[name] = self._vocab.person_with_pronouns()
            elif spec.get("type") == "choice":
                # Handle choice type in vocab (e.g., growth_word, mult_word)
                values = spec.get("values", [])
                items[name] = random.choice(values) if values else ""
            elif "path" in spec:
                path = spec["path"]
                if "sample" in spec:
                    items[name] = self._vocab.sample(path, spec["sample"])
                else:
                    value = self._vocab.random(path)
                    items[name] = value
                    # Auto-add plural form for countable_singular items
                    if "countable_singular" in path and isinstance(value, str):
                        items[f"{name}_plural"] = self._pluralize(value)

        return items

    def _pluralize(self, word: str) -> str:
        """Pluralize a word correctly."""
        if word.endswith(("s", "x", "ch", "sh")):
            return word + "es"
        elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        else:
            return word + "s"

    def _build_template_vars(
        self,
        template_specs: dict[str, str],
        variables: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> dict[str, Any]:
        """Build template variables from specs."""
        template_vars = {}

        for name, spec in template_specs.items():
            value = self._resolve_template_spec(spec, variables, vocab_items)
            template_vars[name] = value

        return template_vars

    def _resolve_template_spec(
        self,
        spec: str,
        variables: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> Any:
        """Resolve a template spec like 'person.name' or 'items|singularize'."""
        # Handle pipes (transformations)
        if "|" in spec:
            parts = spec.split("|")
            value = self._resolve_template_spec(parts[0], variables, vocab_items)
            for transform in parts[1:]:
                value = self._apply_transform(value, transform)
            return value

        # Handle dot notation
        if "." in spec:
            parts = spec.split(".")
            obj = vocab_items.get(parts[0]) or variables.get(parts[0])

            for part in parts[1:]:
                if isinstance(obj, dict):
                    obj = obj.get(part)
                elif isinstance(obj, list) and part.isdigit():
                    idx = int(part)
                    obj = obj[idx] if idx < len(obj) else None
                else:
                    obj = None

            return obj

        # Direct lookup - check vocab and variables, else treat as literal
        if spec in vocab_items:
            return vocab_items[spec]
        if spec in variables:
            return variables[spec]
        # Return spec as literal value if not found
        return spec

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply a transformation to a value."""
        if value is None:
            return None

        if transform == "capitalize":
            return str(value).capitalize()
        elif transform == "singularize":
            s = str(value)
            if s.endswith("ies"):
                return s[:-3] + "y"
            elif s.endswith("es"):
                return s[:-2]
            elif s.endswith("s"):
                return s[:-1]
            return s
        elif transform == "pluralize":
            s = str(value)
            if s.endswith("s") or s.endswith("x") or s.endswith("ch") or s.endswith("sh"):
                return s + "es"
            elif s.endswith("y") and len(s) > 1 and s[-2] not in "aeiou":
                return s[:-1] + "ies"
            else:
                return s + "s"
        elif transform == "with_article":
            return self._vocab.with_article(str(value))
        elif transform == "has_have":
            return "has" if value == "s" else "have"
        elif transform == "does_do":
            return "does" if value == "s" else "do"

        return value

    def _build_trace(
        self, trace_specs: list[dict[str, Any]], variables: dict[str, Any]
    ) -> list[Any]:
        """Build trace steps from specs."""
        trace: list[Any] = []

        for spec in trace_specs:
            op = spec["op"]

            if op == "init":
                var_name = spec["var"]
                value_ref = spec["value"]
                # Handle literal values vs variable references
                if isinstance(value_ref, (int, float)):
                    value = value_ref
                else:
                    value = variables.get(value_ref, 0)
                trace.append(InitStep(var=var_name, value=value))

            elif op == "compute":
                compute_op = ComputeOp(spec["compute_op"])
                # Handle args that can be variable names or literal values
                args: list[str | int | float] = []
                for arg in spec["args"]:
                    if isinstance(arg, (int, float)):
                        args.append(arg)
                    else:
                        args.append(str(arg))  # Keep var name as-is for solver
                var_name = spec["var"]
                trace.append(ComputeStep(compute_op=compute_op, args=args, var=var_name))

            elif op == "query":
                var_name = spec["var"]
                trace.append(QueryStep(var=var_name))

            # Entity tracking operations
            elif op == "transfer":
                from_entity = spec["from_entity"]
                to_entity = spec["to_entity"]
                amount_ref = spec["amount"]
                amount = variables.get(amount_ref, 0) if isinstance(amount_ref, str) else amount_ref
                trace.append(
                    TransferStep(from_entity=from_entity, to_entity=to_entity, amount=amount)
                )

            elif op == "consume":
                entity = spec["entity"]
                amount_ref = spec["amount"]
                amount = variables.get(amount_ref, 0) if isinstance(amount_ref, str) else amount_ref
                trace.append(ConsumeStep(entity=entity, amount=amount))

            elif op == "add_entity":
                entity = spec["entity"]
                amount_ref = spec["amount"]
                amount = variables.get(amount_ref, 0) if isinstance(amount_ref, str) else amount_ref
                trace.append(AddEntityStep(entity=entity, amount=amount))

            # Percentage operations
            elif op == "percent_off":
                base = spec["base"]
                rate = spec["rate"]
                var_name = spec["var"]
                trace.append(PercentOffStep(base=base, rate=rate, var=var_name))

            elif op == "percent_increase":
                base = spec["base"]
                rate = spec["rate"]
                var_name = spec["var"]
                trace.append(PercentIncreaseStep(base=base, rate=rate, var=var_name))

            elif op == "percent_of":
                base = spec["base"]
                rate = spec["rate"]
                var_name = spec["var"]
                trace.append(PercentOfStep(base=base, rate=rate, var=var_name))

        return trace

    def _compute_answer(self, expr: str, variables: dict[str, Any]) -> float:
        """Compute answer from expression."""
        try:
            # Safe expression evaluation using AST parser
            result = self._evaluator.evaluate(expr, variables)
            return float(result)
        except ExpressionError:
            return 0.0

    def _apply_word_numbers(self, text: str) -> str:
        """Randomly convert some numbers to word form.

        Only converts small integers (1-25, 30, 40, 50) that are not part of
        prices, decimals, or large numbers. Each eligible number has
        word_number_prob chance of being converted.
        """
        if self._word_number_prob <= 0:
            return text

        def maybe_convert(match: re.Match[str]) -> str:
            # Get the full match and surrounding context
            num_str: str = match.group(0)

            # Skip if it's a price ($X)
            start = match.start()
            if start > 0 and text[start - 1] == "$":
                return num_str

            # Skip decimals
            if "." in num_str:
                return num_str

            try:
                num = int(num_str)
            except ValueError:
                return num_str

            # Only convert numbers we have words for
            if num not in WORD_NUMBERS:
                return num_str

            # Random chance to convert
            if random.random() < self._word_number_prob:
                return WORD_NUMBERS[num]

            return num_str

        # Match standalone numbers (not part of larger numbers or decimals)
        # This pattern matches numbers not preceded by digits, dots, or $
        return re.sub(r"(?<![0-9.$])\b(\d+)\b(?![0-9.])", maybe_convert, text)


# Convenience function
def generate_from_schema(schema_name: str) -> TraceExample:
    """Generate a single problem from a schema."""
    gen = SchemaGenerator()
    return gen.generate(schema_name)


def generate_batch_from_schemas(n: int = 10) -> list[TraceExample]:
    """Generate multiple problems from all schemas."""
    gen = SchemaGenerator()
    return gen.generate_batch(n=n)
