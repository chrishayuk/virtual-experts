"""Template variable resolution from specs.

Resolves template specs like "person.name" or "item|pluralize" to actual values.

Usage:
    resolver = TemplateResolver()
    template_vars = resolver.resolve(specs, variables, vocab_items)
"""

from __future__ import annotations

import logging
from typing import Any

from chuk_virtual_expert_arithmetic.core.transforms import TransformError, TransformRegistry

logger = logging.getLogger(__name__)


class TemplateResolver:
    """Resolves template variable specifications to values.

    Supports:
    - Dot notation: "person.name" -> person["name"]
    - Pipe transforms: "item|pluralize" -> pluralize(item)
    - Chained transforms: "item|singularize|capitalize"
    - Literal values: "apple" -> "apple"
    """

    def resolve_all(
        self,
        specs: dict[str, str],
        variables: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve all template variable specs.

        Args:
            specs: Dict of name -> spec string
            variables: Numeric variable values
            vocab_items: Sampled vocabulary items

        Returns:
            Dict of name -> resolved value
        """
        result = {}
        for name, spec in specs.items():
            result[name] = self.resolve(spec, variables, vocab_items)
        return result

    def resolve(
        self,
        spec: str,
        variables: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> Any:
        """Resolve a single template spec.

        Args:
            spec: Template spec string (e.g., "person.name|capitalize")
            variables: Numeric variable values
            vocab_items: Sampled vocabulary items

        Returns:
            Resolved value
        """
        # Handle pipes (transformations)
        if "|" in spec:
            parts = spec.split("|")
            value = self.resolve(parts[0], variables, vocab_items)
            for transform in parts[1:]:
                try:
                    value = TransformRegistry.apply(value, transform)
                except TransformError:
                    # Unknown transform - log warning and return value unchanged
                    logger.warning(
                        "Unknown transform '%s' in spec '%s' - value unchanged",
                        transform,
                        spec,
                    )
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

    def build_template_vars(
        self,
        specs: dict[str, str] | None,
        variables: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> dict[str, Any]:
        """Build complete template variables from all sources.

        This is the main entry point that:
        1. Resolves explicit template_vars specs
        2. Adds numeric variables
        3. Adds multiplier words if applicable
        4. Expands structured vocab items

        Args:
            specs: Template variable specifications
            variables: Numeric variable values
            vocab_items: Sampled vocabulary items

        Returns:
            Complete dict of template variables
        """
        template_vars: dict[str, Any] = {}

        # 1. Resolve explicit specs
        if specs:
            template_vars.update(self.resolve_all(specs, variables, vocab_items))

        # 2. Add numeric variables directly
        template_vars.update(variables)

        # 3. Auto-add multiplier word mapping if multiplier variable exists
        if "multiplier" in variables:
            mult = variables["multiplier"]
            mult_words = {2: "twice", 3: "three times", 4: "four times", 5: "five times"}
            growth_words = {
                2: "doubled",
                3: "tripled",
                4: "quadrupled",
                5: "quintupled",
            }
            template_vars["mult_word"] = mult_words.get(mult, f"{mult} times")
            template_vars["growth_word"] = growth_words.get(mult, f"multiplied by {mult}")

        # 4. Expand structured vocab items
        self._expand_vocab_items(template_vars, vocab_items)

        return template_vars

    def _expand_vocab_items(
        self,
        template_vars: dict[str, Any],
        vocab_items: dict[str, Any],
    ) -> None:
        """Expand structured vocab items into template vars."""
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
