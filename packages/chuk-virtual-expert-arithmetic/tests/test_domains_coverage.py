"""Additional tests for DomainSampler - comprehensive coverage."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from chuk_virtual_expert_arithmetic.core.domains import DomainSampler


class MockVocab:
    """Mock Vocab for testing DomainSampler."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}

    def get(self, path: str) -> Any:
        parts = path.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def person_with_pronouns(self) -> dict[str, str]:
        return {
            "name": "Test Person",
            "subject": "they",
            "object": "them",
            "possessive": "their",
            "reflexive": "themselves",
        }

    def random(self, source: str) -> str | None:
        return f"Random_{source}"


class TestDomainSamplerInit:
    """Tests for DomainSampler initialization."""

    def test_init_with_seed(self) -> None:
        """Test initialization with seed."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        assert sampler._vocab is vocab

    def test_init_without_seed(self) -> None:
        """Test initialization without seed."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab)
        assert sampler._rng is not None


class TestDomainSamplerSample:
    """Tests for sample method."""

    def test_sample_unknown_domain(self) -> None:
        """Test sampling unknown domain returns default context."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("nonexistent_domain")
        assert context["domain"] == "default"
        assert context["agent_type"] == "person"

    def test_sample_domain_with_agent_templates(self) -> None:
        """Test sampling domain with agent templates."""
        vocab = MockVocab({
            "domains": {
                "kitchen": {
                    "agent_templates": {
                        "machine": {"pattern": "Oven ${number}", "numbers": [1, 2, 3]},
                    },
                    "items": ["cookies", "cakes"],
                    "verbs": {"singular": "bakes", "plural": "bake"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("kitchen")
        assert context["domain"] == "kitchen"
        assert "Oven" in context["agent"]
        assert context["agent_type"] == "machine"

    def test_sample_domain_without_agent_templates(self) -> None:
        """Test sampling domain without agent templates uses person."""
        vocab = MockVocab({
            "domains": {
                "simple": {
                    "items": ["books"],
                    "verbs": {"singular": "reads", "plural": "read"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("simple")
        assert context["agent_type"] == "person"
        assert context["agent"] == "Test Person"
        assert context["agent2"] == "Test Person"

    def test_sample_domain_with_dict_items(self) -> None:
        """Test sampling with dict-format items."""
        vocab = MockVocab({
            "domains": {
                "test": {
                    "items": [{"singular": "cookie", "plural": "cookies"}],
                    "verbs": {"singular": "eats", "plural": "eat"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("test")
        assert context["item"] == "cookie"
        assert context["item_plural"] == "cookies"

    def test_sample_domain_with_string_items(self) -> None:
        """Test sampling with string-format items (legacy)."""
        vocab = MockVocab({
            "domains": {
                "test": {
                    "items": ["apples"],  # plural string
                    "verbs": {"singular": "collects", "plural": "collect"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("test")
        assert context["item"] == "apple"  # singularized
        assert context["item_plural"] == "apples"

    def test_sample_domain_without_items(self) -> None:
        """Test sampling domain without items."""
        vocab = MockVocab({
            "domains": {
                "empty": {
                    "verbs": {"singular": "does", "plural": "do"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("empty")
        assert context["item"] == "item"
        assert context["item_plural"] == "items"

    def test_sample_domain_with_time_units(self) -> None:
        """Test sampling domain with time units."""
        vocab = MockVocab({
            "domains": {
                "timed": {
                    "items": ["tasks"],
                    "verbs": {"singular": "completes", "plural": "complete"},
                    "time_units": [
                        {"singular": "hour", "plural": "hours"},
                        {"singular": "minute", "plural": "minutes"},
                    ],
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("timed")
        assert "time_unit" in context
        assert "time_unit_plural" in context

    def test_sample_domain_agent2_different(self) -> None:
        """Test that agent2 is different from agent when possible."""
        vocab = MockVocab({
            "domains": {
                "multi_agent": {
                    "agent_templates": {
                        "worker": {"pattern": "Worker ${letter}", "letters": ["A", "B", "C", "D", "E"]},
                    },
                    "items": ["tasks"],
                    "verbs": {"singular": "processes", "plural": "process"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context = sampler.sample("multi_agent")
        # With enough letters, agent2 should be different
        # (though with seed it might still be same, just checking logic runs)
        assert "agent" in context
        assert "agent2" in context


class TestSampleAgent:
    """Tests for _sample_agent method."""

    def test_sample_agent_with_numbers(self) -> None:
        """Test agent sampling with numbers."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        template = {"pattern": "Machine ${number}", "numbers": [1, 2, 3]}
        agent = sampler._sample_agent(template)
        assert "Machine" in agent
        assert any(str(n) in agent for n in [1, 2, 3])

    def test_sample_agent_with_letters(self) -> None:
        """Test agent sampling with letters."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        template = {"pattern": "Robot ${letter}", "letters": ["X", "Y", "Z"]}
        agent = sampler._sample_agent(template)
        assert "Robot" in agent
        assert any(letter in agent for letter in ["X", "Y", "Z"])

    def test_sample_agent_with_source(self) -> None:
        """Test agent sampling with vocab source."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        template = {"pattern": "${name}", "source": "names.male"}
        agent = sampler._sample_agent(template)
        assert agent == "Random_names.male"

    def test_sample_agent_with_source_no_value(self) -> None:
        """Test agent sampling when source returns None."""
        vocab = MagicMock()
        vocab.random.return_value = None
        sampler = DomainSampler(vocab, seed=42)
        template = {"pattern": "Worker ${name}", "source": "empty_source"}
        agent = sampler._sample_agent(template)
        # Pattern is returned without substitution when value is None
        assert agent == "Worker ${name}"

    def test_sample_agent_pattern_only(self) -> None:
        """Test agent with just pattern (no numbers/letters/source)."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        template = {"pattern": "Generic Agent"}
        agent = sampler._sample_agent(template)
        assert agent == "Generic Agent"


class TestDefaultContext:
    """Tests for _default_context method."""

    def test_default_context_structure(self) -> None:
        """Test default context has all required keys."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        context = sampler._default_context()
        assert context["domain"] == "default"
        assert context["agent"] == "Test Person"
        assert context["agent_type"] == "person"
        assert context["item"] == "item"
        assert context["item_plural"] == "items"
        assert context["verb"] == "has"
        assert context["verb_plural"] == "have"


class TestListDomains:
    """Tests for list_domains method."""

    def test_list_domains_with_domains(self) -> None:
        """Test listing domains when they exist."""
        vocab = MockVocab({
            "domains": {
                "kitchen": {},
                "farm": {},
                "school": {},
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        domains = sampler.list_domains()
        assert "kitchen" in domains
        assert "farm" in domains
        assert "school" in domains

    def test_list_domains_empty(self) -> None:
        """Test listing domains when none exist."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        domains = sampler.list_domains()
        assert domains == []

    def test_list_domains_not_dict(self) -> None:
        """Test listing domains when domains is not a dict."""
        vocab = MockVocab({"domains": "not_a_dict"})
        sampler = DomainSampler(vocab, seed=42)
        domains = sampler.list_domains()
        assert domains == []


class TestRandomDomain:
    """Tests for random_domain method."""

    def test_random_domain_with_domains(self) -> None:
        """Test random domain selection."""
        vocab = MockVocab({
            "domains": {
                "kitchen": {},
                "farm": {},
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        domain = sampler.random_domain()
        assert domain in ["kitchen", "farm"]

    def test_random_domain_no_domains(self) -> None:
        """Test random domain when none exist."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        domain = sampler.random_domain()
        assert domain == "default"


class TestReseed:
    """Tests for reseed method."""

    def test_reseed(self) -> None:
        """Test reseeding."""
        vocab = MockVocab({
            "domains": {
                "test": {
                    "items": ["a", "b", "c", "d", "e"],
                    "verbs": {"singular": "does", "plural": "do"},
                }
            }
        })
        sampler = DomainSampler(vocab, seed=42)
        context1 = sampler.sample("test")

        sampler.reseed(42)
        context2 = sampler.sample("test")

        assert context1["item"] == context2["item"]

    def test_reseed_with_none(self) -> None:
        """Test reseeding with None."""
        vocab = MockVocab()
        sampler = DomainSampler(vocab, seed=42)
        sampler.reseed(None)
        # Should still work
        assert sampler._rng is not None
