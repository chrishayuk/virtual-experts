"""Vocabulary loader for generators.

Loads vocabulary from JSON files for varied, reusable text generation.

Usage:
    from chuk_virtual_expert_arithmetic.vocab import Vocab

    vocab = Vocab()
    name = vocab.random("names.people")
    animal = vocab.random("animals.farm_animals")
    phrase = vocab.random("phrases.half_of")

    # Get structured data
    container_pair = vocab.random("containers.paired")
    print(container_pair["first"], container_pair["second"])

    # Template substitution
    template = vocab.random("phrases.selling")
    text = vocab.substitute(template, price=5)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


class Vocab:
    """Vocabulary loader with random sampling and template substitution."""

    _instance: Vocab | None = None
    _cache: dict[str, Any] = {}

    def __new__(cls) -> Vocab:
        """Singleton pattern - only load vocab files once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_all()
        return cls._instance

    def _load_all(self) -> None:
        """Load all JSON vocab files."""
        vocab_dir = Path(__file__).parent

        # Load top-level JSON files (names.json, items.json, etc.)
        for json_file in vocab_dir.glob("*.json"):
            key = json_file.stem
            with open(json_file) as f:
                self._cache[key] = json.load(f)

        # Load patterns from patterns/ subdirectory (organized by expert type)
        patterns_dir = vocab_dir / "patterns"
        if patterns_dir.exists():
            patterns = {}
            # Load from root (for backwards compatibility)
            for json_file in patterns_dir.glob("*.json"):
                key = json_file.stem
                with open(json_file) as f:
                    patterns[key] = json.load(f)

            # Load from subdirectories (organized by expert type)
            for subdir in patterns_dir.iterdir():
                if subdir.is_dir():
                    for json_file in subdir.glob("*.json"):
                        key = json_file.stem
                        with open(json_file) as f:
                            patterns[key] = json.load(f)

            self._cache["patterns"] = patterns

        # Load domains from domains/ subdirectory
        domains_dir = vocab_dir / "domains"
        if domains_dir.exists():
            domains = {}
            for json_file in domains_dir.glob("*.json"):
                with open(json_file) as f:
                    domain_data = json.load(f)
                    # Use the domain name from the file or the filename
                    domain_name = domain_data.get("name", json_file.stem)
                    domains[domain_name] = domain_data

            self._cache["domains"] = domains

        # Load messy vocab from messy/ subdirectory (for GSM-8K style diversity)
        messy_dir = vocab_dir / "messy"
        if messy_dir.exists():
            messy = {}
            for json_file in messy_dir.glob("*.json"):
                key = json_file.stem
                with open(json_file) as f:
                    messy[key] = json.load(f)
            self._cache["messy"] = messy

    def get(self, path: str) -> Any:
        """Get vocabulary by dot-separated path.

        Args:
            path: Dot-separated path like "names.people" or "animals.farm_animals"

        Returns:
            The vocabulary list or dict at that path
        """
        parts = path.split(".")
        data: Any = self._cache
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return None
            if data is None:
                return None
        return data

    def random(self, path: str) -> Any:
        """Get a random item from a vocabulary list.

        Args:
            path: Dot-separated path to a list, e.g., "names.people"

        Returns:
            A random item from the list, or None if not found
        """
        items = self.get(path)
        if items and isinstance(items, list):
            return random.choice(items)
        return None

    def sample(self, path: str, k: int = 2) -> list[Any]:
        """Get k random unique items from a vocabulary list.

        Args:
            path: Dot-separated path to a list
            k: Number of items to sample

        Returns:
            List of k random items
        """
        items = self.get(path)
        if items and isinstance(items, list):
            return random.sample(items, min(k, len(items)))
        return []

    def substitute(self, template: str, **kwargs: Any) -> str:
        """Substitute variables in a template string.

        Args:
            template: String with ${var} placeholders
            **kwargs: Variables to substitute

        Returns:
            String with substitutions made

        Example:
            vocab.substitute("sells at ${price} each", price=5)
            # Returns: "sells at 5 each"
        """
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"${{{key}}}", str(value))
        return result

    def pattern(self, pattern_name: str, variant: str | None = None, **kwargs: Any) -> str:
        """Get a random pattern template and substitute variables.

        Supports weighted templates for diversity. Templates can be:
        - Simple strings: "This is a template with ${var}"
        - Weighted dicts: {"text": "Template...", "weight": 3}

        Higher weight = more likely to be selected. Default weight is 1.

        Args:
            pattern_name: Name of the pattern (e.g., "price_chain")
            variant: Optional variant name for patterns with sub-templates
            **kwargs: Variables to substitute in the template

        Returns:
            Filled template string
        """
        pattern_data = self.get(f"patterns.{pattern_name}")
        if not pattern_data:
            return ""

        # Handle patterns with "templates" key vs direct variant lists
        # Priority: explicit variant > "templates" key > first available
        if isinstance(pattern_data, dict):
            if variant and variant in pattern_data:
                # Explicit variant requested and exists
                templates = pattern_data[variant]
            elif "templates" in pattern_data:
                # Default to "templates" key if no variant specified
                templates = pattern_data["templates"]
            else:
                # Pattern has variants directly (no "templates" wrapper)
                templates = pattern_data.get(variant, []) if variant else []
        else:
            templates = pattern_data

        if not templates:
            return ""

        # Select template with weighted random choice
        template = self._select_weighted_template(templates)
        return self.substitute(template, **kwargs)

    def _select_weighted_template(self, templates: list[Any] | Any) -> str:
        """Select a template using weighted random choice.

        Args:
            templates: List of templates (strings or weighted dicts)

        Returns:
            Selected template string
        """
        if not isinstance(templates, list):
            return str(templates)

        if not templates:
            return ""

        # Extract texts and weights
        texts: list[str] = []
        weights: list[int] = []

        for t in templates:
            if isinstance(t, dict):
                texts.append(t.get("text", ""))
                weights.append(t.get("weight", 1))
            else:
                texts.append(str(t))
                weights.append(1)

        # Use weighted random choice
        return random.choices(texts, weights=weights, k=1)[0]

    def random_pair(self, path: str) -> tuple[Any, Any]:
        """Get a random paired container (first, second).

        Args:
            path: Path to list of {"first": ..., "second": ...} dicts

        Returns:
            Tuple of (first, second) values
        """
        pair = self.random(path)
        if pair and isinstance(pair, dict):
            return pair.get("first"), pair.get("second")
        return None, None

    def all_keys(self) -> list[str]:
        """List all top-level vocab file names."""
        return list(self._cache.keys())

    def list_paths(self, prefix: str = "") -> list[str]:
        """List all available paths for a vocab file.

        Args:
            prefix: Vocab file name (e.g., "names", "animals")

        Returns:
            List of available paths
        """
        if not prefix:
            return self.all_keys()

        data = self._cache.get(prefix, {})
        if isinstance(data, dict):
            return [f"{prefix}.{k}" for k in data.keys()]
        return []

    # =========================================================================
    # COMPOSITION HELPERS
    # =========================================================================

    def colored_material(self, material_type: str = "fabrics") -> str:
        """Generate a colored material phrase.

        Args:
            material_type: Type from materials.json (fabrics, building, craft)

        Returns:
            String like "blue fiber", "red fabric", "green cotton"
        """
        color = self.random("colors.basic")
        material = self.random(f"materials.{material_type}")
        return f"{color} {material}" if color and material else material or "material"

    def labeled_container(self, use_words: bool = False) -> str:
        """Generate a labeled container.

        Args:
            use_words: If True, use "first tank" style. If False, use "Tank A" style.

        Returns:
            String like "Tank A", "first shelf", "the large bin"
        """
        container = self.random("containers.types")
        if not container:
            container = "container"

        if use_words:
            ordinal = self.random("ordinals.sequences") or "first"
            return f"the {ordinal} {container}"
        else:
            pair = self.random("ordinals.letter_pairs")
            letter = pair.get("first", "A") if pair else "A"
            return f"{container.capitalize()} {letter}"

    def container_pair(self, use_words: bool | None = None) -> tuple[str, str]:
        """Generate a pair of contrasting containers.

        Args:
            use_words: If True, use word ordinals. If False, use letters. If None, random.

        Returns:
            Tuple of (first_container, second_container)
        """
        if use_words is None:
            use_words = random.choice([True, False])

        container = self.random("containers.types") or "container"

        if use_words:
            pair = self.random("ordinals.word_pairs")
            if pair:
                return f"the {pair['first']} {container}", f"the {pair['second']} {container}"
            return f"the first {container}", f"the second {container}"
        else:
            pair = self.random("ordinals.letter_pairs")
            if pair:
                return (
                    f"{container.capitalize()} {pair['first']}",
                    f"{container.capitalize()} {pair['second']}",
                )
            return f"{container.capitalize()} A", f"{container.capitalize()} B"

    def material_pair(self, material_type: str = "fabrics") -> tuple[str, str]:
        """Generate a pair of colored materials.

        Returns:
            Tuple of two different colored materials
        """
        colors = self.sample("colors.basic", 2)
        material = self.random(f"materials.{material_type}") or "material"

        if len(colors) >= 2:
            return f"{colors[0]} {material}", f"{colors[1]} {material}"
        return f"type A {material}", f"type B {material}"

    def farm_animal_context(self) -> dict[str, Any]:
        """Get a farm animal with its production context.

        Returns:
            Dict with name, singular, produces, verb
        """
        animal = self.random("animals.farm_animals")
        if animal and isinstance(animal, dict):
            return dict(animal)  # Ensure proper typing
        return {"name": "chickens", "singular": "chicken", "produces": "eggs", "verb": "lay"}

    def conjugate(self, verb_data: dict[str, Any] | None, use_singular: bool, **kwargs: Any) -> str:
        """Conjugate a verb phrase based on singular/plural.

        Args:
            verb_data: Dict with "base", "s", "rest" keys
            use_singular: True for "she eats", False for "they eat"
            **kwargs: Variables to substitute in "rest"

        Returns:
            Conjugated phrase like "eats for breakfast" or "eat for breakfast"
        """
        if not verb_data or not isinstance(verb_data, dict):
            return "does"

        verb = verb_data.get("s" if use_singular else "base", "do")
        rest = verb_data.get("rest", "")

        if rest and kwargs:
            rest = self.substitute(rest, **kwargs)

        return f"{verb} {rest}".strip() if rest else verb

    def person_with_pronouns(self) -> dict[str, Any]:
        """Get a random person name with matching pronouns.

        Returns:
            Dict with name, subject, object, possessive, reflexive, verb_suffix
            Example: {"name": "Sarah", "subject": "she", "object": "her",
                      "possessive": "her", "reflexive": "herself", "verb_s": "s"}
        """
        # Randomly pick gender (weighted toward gendered for natural problem text)
        gender = random.choices(["male", "female", "neutral"], weights=[0.45, 0.45, 0.10])[0]

        name = self.random(f"names.{gender}")
        pronouns = self.get(f"names.pronouns.{gender}")

        if not name or not pronouns:
            # Fallback
            return {
                "name": "Alex",
                "subject": "they",
                "object": "them",
                "possessive": "their",
                "reflexive": "themselves",
                "verb_s": "",  # "they eat" not "they eats"
            }

        return {
            "name": name,
            "subject": pronouns["subject"],
            "object": pronouns["object"],
            "possessive": pronouns["possessive"],
            "reflexive": pronouns.get("reflexive", "themselves"),
            "verb_s": "" if gender == "neutral" else "s",  # "she eats" vs "they eat"
        }

    def activity_context(self) -> dict[str, Any]:
        """Get an activity with verb forms.

        Returns:
            Dict with verb, continuous, noun
        """
        activity = self.random("phrases.activities")
        if activity and isinstance(activity, dict):
            return dict(activity)  # Ensure proper typing
        return {"verb": "run", "continuous": "runs", "noun": "laps"}

    def a_an(self, word: str) -> str:
        """Return 'a' or 'an' based on the word's starting sound.

        Args:
            word: The word to check

        Returns:
            'an' if word starts with a vowel sound, 'a' otherwise
        """
        if not word:
            return "a"
        # Simple heuristic - check first letter
        # Note: This doesn't handle all edge cases (e.g., "hour", "university")
        first_letter = word[0].lower()
        if first_letter in "aeiou":
            return "an"
        return "a"

    def with_article(self, word: str) -> str:
        """Return word with appropriate indefinite article.

        Args:
            word: The word to prefix with article

        Returns:
            String like 'a book' or 'an apple'
        """
        return f"{self.a_an(word)} {word}"


# Convenience singleton
_vocab: Vocab | None = None


def get_vocab() -> Vocab:
    """Get the singleton Vocab instance."""
    global _vocab
    if _vocab is None:
        _vocab = Vocab()
    return _vocab
