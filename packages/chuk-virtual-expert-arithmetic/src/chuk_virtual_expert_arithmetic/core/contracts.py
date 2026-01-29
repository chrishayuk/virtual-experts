"""Pattern-schema contract validation.

Validates that schemas provide all template variables required by their patterns.

Usage:
    validator = ContractValidator(vocab)
    errors = validator.validate_schema(schema)
"""

from __future__ import annotations

import re
from typing import Any

from chuk_virtual_expert_arithmetic.models.schema_spec import SchemaSpec


class ContractValidationError(Exception):
    """Raised when a schema violates its pattern contract."""

    pass


class ContractValidator:
    """Validates pattern-schema contracts.

    Ensures that:
    - Schema provides all template variables required by its pattern
    - Pattern exists and has the specified variant
    - Template variables can be resolved from vocab, variables, or template_vars
    """

    # Pattern for finding template variables like ${name} or ${item}
    TEMPLATE_VAR_PATTERN = re.compile(r"\$\{(\w+)\}")

    def __init__(self, vocab: Any) -> None:
        """Initialize the validator.

        Args:
            vocab: Vocab instance to look up patterns
        """
        self._vocab = vocab

    def validate_schema(self, schema: SchemaSpec) -> list[str]:
        """Validate a schema against its pattern contract.

        Args:
            schema: The schema to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []

        if not schema.pattern:
            return errors  # No pattern = no contract

        # Get pattern data
        pattern_data = self._vocab.get(f"patterns.{schema.pattern}")
        if not pattern_data:
            errors.append(f"Pattern '{schema.pattern}' not found")
            return errors

        # Get templates for the variant
        templates = self._get_templates(pattern_data, schema.variant)
        if not templates:
            if schema.variant:
                errors.append(f"Variant '{schema.variant}' not found in pattern '{schema.pattern}'")
            else:
                errors.append(f"No templates found in pattern '{schema.pattern}'")
            return errors

        # Extract required variables from all templates
        required_vars = self._extract_template_vars(templates)

        # Get provided variables from schema
        provided_vars = self._get_provided_vars(schema)

        # Check for missing variables
        missing = required_vars - provided_vars
        if missing:
            errors.append(
                f"Schema '{schema.name}' missing template vars for pattern "
                f"'{schema.pattern}': {sorted(missing)}"
            )

        return errors

    def validate_all(self, schemas: dict[str, SchemaSpec]) -> dict[str, list[str]]:
        """Validate all schemas against their pattern contracts.

        Args:
            schemas: Dict of schema name -> SchemaSpec

        Returns:
            Dict of schema name -> list of errors (only includes schemas with errors)
        """
        all_errors: dict[str, list[str]] = {}

        for name, schema in schemas.items():
            errors = self.validate_schema(schema)
            if errors:
                all_errors[name] = errors

        return all_errors

    def _get_templates(self, pattern_data: Any, variant: str | None) -> list[str]:
        """Extract template strings from pattern data."""
        templates: list[str] = []

        if isinstance(pattern_data, list):
            templates = [t for t in pattern_data if isinstance(t, str)]
        elif isinstance(pattern_data, dict):
            if "templates" in pattern_data:
                raw_templates = pattern_data["templates"]
            elif variant and variant in pattern_data:
                raw_templates = pattern_data[variant]
            else:
                raw_templates = []

            if isinstance(raw_templates, list):
                for t in raw_templates:
                    if isinstance(t, str):
                        templates.append(t)
                    elif isinstance(t, dict) and "text" in t:
                        # Weighted template format
                        templates.append(t["text"])

        return templates

    def _extract_template_vars(self, templates: list[str]) -> set[str]:
        """Extract all template variable names from templates."""
        variables: set[str] = set()

        for template in templates:
            matches = self.TEMPLATE_VAR_PATTERN.findall(template)
            variables.update(matches)

        return variables

    def _get_provided_vars(self, schema: SchemaSpec) -> set[str]:
        """Get all variable names provided by the schema."""
        provided: set[str] = set()

        # From template_vars
        if schema.template_vars:
            provided.update(schema.template_vars.keys())

        # From variables (numeric)
        if schema.variables:
            provided.update(schema.variables.keys())

        # Auto-generated from person vocab
        if schema.vocab:
            for name, spec in schema.vocab.items():
                if spec.type == "person_with_pronouns":
                    # These are auto-generated
                    if name == "person":
                        provided.update(
                            [
                                "name", "subject", "subj", "his_her",
                                "him_her", "reflexive", "verb_s",
                                "has_have", "does_do", "is_are", "was_were",
                            ]
                        )
                    else:
                        # personN variants
                        suffix = name[6:] if name.startswith("person") else ""
                        if suffix:
                            provided.update(
                                [
                                    f"name{suffix}",
                                    f"subject{suffix}",
                                    f"subj{suffix}",
                                    f"his_her{suffix}",
                                    f"him_her{suffix}",
                                    f"reflexive{suffix}",
                                    f"verb_s{suffix}",
                                    f"has_have{suffix}",
                                    f"does_do{suffix}",
                                    f"is_are{suffix}",
                                    f"was_were{suffix}",
                                ]
                            )

                # Path-based vocab items are added by name
                if spec.path:
                    provided.add(name)
                    # Also add plural form for countable_singular
                    if "countable_singular" in spec.path:
                        provided.add(f"{name}_plural")

        # Multiplier words (auto-generated when multiplier variable exists)
        if schema.variables and "multiplier" in schema.variables:
            provided.update(["mult_word", "growth_word"])

        return provided

    def get_pattern_requirements(self, pattern_name: str, variant: str | None = None) -> set[str]:
        """Get all template variables required by a pattern.

        Args:
            pattern_name: Name of the pattern
            variant: Optional variant name

        Returns:
            Set of required variable names
        """
        pattern_data = self._vocab.get(f"patterns.{pattern_name}")
        if not pattern_data:
            return set()

        templates = self._get_templates(pattern_data, variant)
        return self._extract_template_vars(templates)
