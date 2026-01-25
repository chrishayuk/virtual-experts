"""Schema-based generator for arithmetic problems.

Generates problems from JSON schema definitions, reducing hardcoded logic.

Usage:
    from chuk_virtual_expert_arithmetic.generators.schema_generator import SchemaGenerator

    gen = SchemaGenerator()
    example = gen.generate("price_chain")
    examples = gen.generate_batch(["price_chain", "subtract_chain"], n=10)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import ComputeOp, ComputeStep, InitStep, QueryStep

from chuk_virtual_expert_arithmetic.vocab import get_vocab


class SchemaGenerator:
    """Generates arithmetic problems from JSON schemas."""

    def __init__(self):
        self._vocab = get_vocab()
        self._schemas = self._load_schemas()

    def _load_schemas(self) -> dict[str, dict]:
        """Load all schemas from the schemas directory."""
        schemas = {}
        schema_dir = Path(__file__).parent.parent / "schemas"

        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.json"):
                with open(schema_file) as f:
                    schema = json.load(f)
                    name = schema.get("name", schema_file.stem)
                    schemas[name] = schema

        return schemas

    @property
    def schema_names(self) -> list[str]:
        """List available schema names."""
        return list(self._schemas.keys())

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

        # Build trace
        trace = self._build_trace(schema.get("trace", []), variables)

        # Compute answer
        answer = self._compute_answer(schema.get("answer", "0"), variables)

        return TraceExample(
            expert="arithmetic",
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

    def _generate_variables(self, var_specs: dict[str, dict]) -> dict[str, Any]:
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
                options = spec.get("options", [])
                variables[name] = random.choice(options) if options else None

        return variables

    def _compute_derived(
        self, derived_specs: dict[str, str], variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute derived variables from expressions."""
        derived = {}

        for name, expr in derived_specs.items():
            try:
                # Simple expression evaluation with variables
                derived[name] = eval(expr, {"__builtins__": {}}, variables)
            except Exception:
                derived[name] = 0

        return derived

    def _apply_constraints(
        self,
        constraints: dict[str, dict],
        variables: dict[str, Any],
        schema: dict,
    ) -> dict[str, Any]:
        """Apply constraints, regenerating if needed."""
        max_attempts = 10

        for _ in range(max_attempts):
            all_satisfied = True

            for expr, bounds in constraints.items():
                try:
                    value = eval(expr, {"__builtins__": {}}, variables)
                    min_val = bounds.get("min", float("-inf"))
                    max_val = bounds.get("max", float("inf"))

                    if not (min_val <= value <= max_val):
                        all_satisfied = False
                        break
                except Exception:
                    pass

            if all_satisfied:
                return variables

            # Regenerate variables
            variables = self._generate_variables(schema.get("variables", {}))
            derived = self._compute_derived(schema.get("derived", {}), variables)
            variables.update(derived)

        return variables

    def _sample_vocab(self, vocab_specs: dict[str, dict]) -> dict[str, Any]:
        """Sample vocabulary items."""
        items = {}

        for name, spec in vocab_specs.items():
            if spec.get("type") == "person_with_pronouns":
                items[name] = self._vocab.person_with_pronouns()
            elif "path" in spec:
                path = spec["path"]
                if "sample" in spec:
                    items[name] = self._vocab.sample(path, spec["sample"])
                else:
                    items[name] = self._vocab.random(path)

        return items

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

        # Direct lookup
        return vocab_items.get(spec) or variables.get(spec)

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
        self, trace_specs: list[dict], variables: dict[str, Any]
    ) -> list:
        """Build trace steps from specs."""
        trace = []

        for spec in trace_specs:
            op = spec["op"]

            if op == "init":
                var_name = spec["var"]
                value_ref = spec["value"]
                value = variables.get(value_ref, 0)
                trace.append(InitStep(var=var_name, value=value))

            elif op == "compute":
                compute_op = ComputeOp(spec["compute_op"])
                args = spec["args"]
                var_name = spec["var"]
                trace.append(ComputeStep(compute_op=compute_op, args=args, var=var_name))

            elif op == "query":
                var_name = spec["var"]
                trace.append(QueryStep(var=var_name))

        return trace

    def _compute_answer(self, expr: str, variables: dict[str, Any]) -> float:
        """Compute answer from expression."""
        try:
            return eval(expr, {"__builtins__": {}}, variables)
        except Exception:
            return 0


# Convenience function
def generate_from_schema(schema_name: str) -> TraceExample:
    """Generate a single problem from a schema."""
    gen = SchemaGenerator()
    return gen.generate(schema_name)


def generate_batch_from_schemas(n: int = 10) -> list[TraceExample]:
    """Generate multiple problems from all schemas."""
    gen = SchemaGenerator()
    return gen.generate_batch(n=n)
