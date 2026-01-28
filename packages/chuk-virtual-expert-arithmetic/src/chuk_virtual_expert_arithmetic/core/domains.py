"""Domain-first vocabulary sampling.

Domains provide semantically coherent vocabulary bundles:
- kitchen: bakes cookies, Oven 1, hours
- farm: collects eggs, chickens, days
- school: reads books, students, periods

Usage:
    sampler = DomainSampler(vocab)
    context = sampler.sample("kitchen")
    # {"agent": "Oven 1", "item": "cookies", "verb": "bakes", ...}
"""

from __future__ import annotations

import random
from typing import Any


class DomainSampler:
    """Samples vocabulary from domain bundles for semantic coherence.

    Ensures that generated problems use items, verbs, and agents that
    make sense together (e.g., kitchen domain won't generate
    "runs miles" or "manufactures widgets").
    """

    def __init__(self, vocab: Any, seed: int | None = None) -> None:
        """Initialize the sampler.

        Args:
            vocab: Vocab instance with loaded domains
            seed: Random seed for reproducibility
        """
        self._vocab = vocab
        self._rng = random.Random(seed)

    def sample(self, domain_name: str) -> dict[str, Any]:
        """Sample a complete vocabulary context from a domain.

        Args:
            domain_name: Name of the domain (e.g., "kitchen", "farm")

        Returns:
            Dict with sampled values:
            - agent: The actor (e.g., "Oven 1", "Baker")
            - item: The object being processed (e.g., "cookies")
            - item_plural: Pluralized item
            - verb: Action verb (e.g., "bakes")
            - verb_plural: Plural form (e.g., "bake")
            - time_unit: Time unit if applicable
            - domain: The domain name
        """
        domain = self._vocab.get(f"domains.{domain_name}")
        if not domain:
            return self._default_context()

        context: dict[str, Any] = {"domain": domain_name}

        # Sample agent
        agent_templates = domain.get("agent_templates", {})
        if agent_templates:
            agent_type = self._rng.choice(list(agent_templates.keys()))
            context["agent"] = self._sample_agent(agent_templates[agent_type])
            context["agent_type"] = agent_type
        else:
            context["agent"] = self._vocab.person_with_pronouns()["name"]
            context["agent_type"] = "person"

        # Sample item
        items = domain.get("items", [])
        if items:
            item = self._rng.choice(items)
            context["item"] = item
            context["item_plural"] = self._pluralize(item)
        else:
            context["item"] = "item"
            context["item_plural"] = "items"

        # Get verbs
        verbs = domain.get("verbs", {})
        context["verb"] = verbs.get("singular", "processes")
        context["verb_plural"] = verbs.get("plural", "process")

        # Sample time unit if available
        time_units = domain.get("time_units", [])
        if time_units:
            time_unit = self._rng.choice(time_units)
            context["time_unit"] = time_unit.get("singular", "hour")
            context["time_unit_plural"] = time_unit.get("plural", "hours")

        return context

    def _sample_agent(self, template: dict[str, Any]) -> str:
        """Sample an agent from a template."""
        pattern: str = str(template.get("pattern", "${name}"))

        if "numbers" in template:
            number = self._rng.choice(template["numbers"])
            return pattern.replace("${number}", str(number))

        if "letters" in template:
            letter = self._rng.choice(template["letters"])
            return pattern.replace("${letter}", str(letter))

        if "source" in template:
            source = template["source"]
            value = self._vocab.random(source)
            if value:
                return pattern.replace("${name}", str(value))

        return pattern

    def _default_context(self) -> dict[str, Any]:
        """Return a default context when domain not found."""
        person = self._vocab.person_with_pronouns()
        return {
            "domain": "default",
            "agent": person["name"],
            "agent_type": "person",
            "item": "item",
            "item_plural": "items",
            "verb": "has",
            "verb_plural": "have",
        }

    def _pluralize(self, word: str) -> str:
        """Pluralize a word."""
        if word.endswith(("s", "x", "ch", "sh")):
            return word + "es"
        elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        else:
            return word + "s"

    def list_domains(self) -> list[str]:
        """List all available domain names."""
        domains = self._vocab.get("domains")
        if isinstance(domains, dict):
            return list(domains.keys())
        return []

    def random_domain(self) -> str:
        """Get a random domain name."""
        domains = self.list_domains()
        return self._rng.choice(domains) if domains else "default"

    def reseed(self, seed: int | None = None) -> None:
        """Reseed the random number generator."""
        self._rng = random.Random(seed)
