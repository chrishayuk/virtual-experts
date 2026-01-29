"""Tests for VocabSampler - comprehensive coverage."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from chuk_virtual_expert_arithmetic.core.sampler import VocabSampler
from chuk_virtual_expert_arithmetic.models.schema_spec import VocabSpec
from chuk_virtual_expert_arithmetic.vocab import get_vocab


class MockVocab:
    """Mock vocab for testing sampler in isolation."""

    def __init__(self) -> None:
        self._data = {
            "names.male": ["John", "Bob", "Alice", "Charlie"],
            "items.fruits": ["apple", "banana", "orange"],
            "items.countable_singular": ["book", "pencil", "cookie"],
        }
        self._person_data = {
            "name": "Alice",
            "subject": "she",
            "object": "her",
            "possessive": "her",
            "reflexive": "herself",
        }

    def person_with_pronouns(self) -> dict[str, str]:
        """Return mock person with pronouns."""
        return self._person_data

    def get(self, path: str) -> Any:
        """Get data at path."""
        return self._data.get(path)

    def random(self, path: str) -> Any:
        """Return random item from path."""
        items = self._data.get(path)
        if items:
            return items[0]
        return None

    def sample(self, path: str, k: int) -> list[Any]:
        """Sample k items from path."""
        items = self._data.get(path, [])
        return items[:k]


class TestVocabSamplerInit:
    """Tests for VocabSampler initialization."""

    def test_init_with_vocab(self) -> None:
        """Test initialization with vocab instance."""
        vocab = MockVocab()
        sampler = VocabSampler(vocab, seed=42)
        assert sampler._vocab is vocab

    def test_init_with_seed(self) -> None:
        """Test initialization with seed."""
        vocab = MockVocab()
        sampler = VocabSampler(vocab, seed=42)
        assert sampler._rng is not None

    def test_init_without_seed(self) -> None:
        """Test initialization without seed."""
        vocab = MockVocab()
        sampler = VocabSampler(vocab)
        assert sampler._rng is not None


class TestVocabSamplerSample:
    """Tests for sample method."""

    @pytest.fixture
    def sampler(self) -> VocabSampler:
        """Create sampler with mock vocab."""
        return VocabSampler(MockVocab(), seed=42)

    def test_sample_none_specs(self, sampler: VocabSampler) -> None:
        """Test sample with None specs returns empty dict."""
        result = sampler.sample(None)
        assert result == {}

    def test_sample_empty_specs(self, sampler: VocabSampler) -> None:
        """Test sample with empty specs returns empty dict."""
        result = sampler.sample({})
        assert result == {}

    def test_sample_person_with_pronouns(self, sampler: VocabSampler) -> None:
        """Test sampling person_with_pronouns type."""
        specs = {"person": VocabSpec(type="person_with_pronouns")}
        result = sampler.sample(specs)

        assert "person" in result
        assert result["person"]["name"] == "Alice"
        assert result["person"]["subject"] == "she"

    def test_sample_choice_type(self, sampler: VocabSampler) -> None:
        """Test sampling choice type."""
        specs = {"color": VocabSpec(type="choice", values=["red", "blue", "green"])}
        result = sampler.sample(specs)

        assert "color" in result
        assert result["color"] in ["red", "blue", "green"]

    def test_sample_path_type(self, sampler: VocabSampler) -> None:
        """Test sampling from path."""
        specs = {"name": VocabSpec(path="names.male")}
        result = sampler.sample(specs)

        assert "name" in result
        assert result["name"] in ["John", "Bob", "Alice", "Charlie"]

    def test_sample_path_with_sample_count(self, sampler: VocabSampler) -> None:
        """Test sampling multiple items from path."""
        specs = {"names": VocabSpec(path="names.male", sample=2)}
        result = sampler.sample(specs)

        assert "names" in result
        # Should return list when sample > 1
        assert len(result["names"]) == 2

    def test_sample_countable_singular_adds_plural(self, sampler: VocabSampler) -> None:
        """Test that countable_singular path adds plural form."""
        specs = {"item": VocabSpec(path="items.countable_singular")}
        result = sampler.sample(specs)

        assert "item" in result
        assert "item_plural" in result

    def test_sample_distinct_from(self, sampler: VocabSampler) -> None:
        """Test distinct_from excludes values."""
        specs = {
            "first": VocabSpec(type="choice", values=["a", "b", "c"]),
            "second": VocabSpec(type="choice", values=["a", "b", "c"], distinct_from=["first"]),
        }
        result = sampler.sample(specs)

        assert result["first"] != result["second"]


class TestVocabSamplerSampleOne:
    """Tests for sample_one method."""

    @pytest.fixture
    def sampler(self) -> VocabSampler:
        """Create sampler with mock vocab."""
        return VocabSampler(MockVocab(), seed=42)

    def test_sample_one_person(self, sampler: VocabSampler) -> None:
        """Test sample_one for person_with_pronouns."""
        spec = VocabSpec(type="person_with_pronouns")
        result = sampler.sample_one(spec)

        assert isinstance(result, dict)
        assert "name" in result
        assert "subject" in result

    def test_sample_one_choice(self, sampler: VocabSampler) -> None:
        """Test sample_one for choice type."""
        spec = VocabSpec(type="choice", values=["x", "y", "z"])
        result = sampler.sample_one(spec)

        assert result in ["x", "y", "z"]

    def test_sample_one_choice_empty(self, sampler: VocabSampler) -> None:
        """Test sample_one for empty choice returns empty string."""
        spec = VocabSpec(type="choice", values=[])
        result = sampler.sample_one(spec)

        assert result == ""

    def test_sample_one_choice_with_exclude(self, sampler: VocabSampler) -> None:
        """Test sample_one for choice with exclusions."""
        spec = VocabSpec(type="choice", values=["a", "b", "c"])
        result = sampler.sample_one(spec, exclude={"a", "b"})

        assert result == "c"

    def test_sample_one_path(self, sampler: VocabSampler) -> None:
        """Test sample_one from path."""
        spec = VocabSpec(path="names.male")
        result = sampler.sample_one(spec)

        assert result in ["John", "Bob", "Alice", "Charlie"]

    def test_sample_one_path_with_sample(self, sampler: VocabSampler) -> None:
        """Test sample_one from path with sample count."""
        spec = VocabSpec(path="names.male", sample=2)
        result = sampler.sample_one(spec)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_sample_one_unknown_type(self, sampler: VocabSampler) -> None:
        """Test sample_one returns None for unknown type."""
        spec = VocabSpec()  # No type, no path
        result = sampler.sample_one(spec)

        assert result is None


class TestVocabSamplerSampleWithExclusion:
    """Tests for _sample_with_exclusion method."""

    @pytest.fixture
    def sampler(self) -> VocabSampler:
        """Create sampler with mock vocab."""
        return VocabSampler(MockVocab(), seed=42)

    def test_sample_without_exclusion(self, sampler: VocabSampler) -> None:
        """Test sampling without exclusions."""
        result = sampler._sample_with_exclusion("names.male", None)
        assert result in ["John", "Bob", "Alice", "Charlie"]

    def test_sample_with_exclusion(self, sampler: VocabSampler) -> None:
        """Test sampling with exclusions."""
        result = sampler._sample_with_exclusion("names.male", {"John", "Bob", "Alice"})
        assert result == "Charlie"

    def test_sample_all_excluded_falls_back(self, sampler: VocabSampler) -> None:
        """Test when all items excluded, falls back to random."""
        result = sampler._sample_with_exclusion("names.male", {"John", "Bob", "Alice", "Charlie"})
        # Should return one of the items (fallback to random)
        assert result in ["John", "Bob", "Alice", "Charlie"]

    def test_sample_invalid_path(self, sampler: VocabSampler) -> None:
        """Test sampling from invalid path."""
        result = sampler._sample_with_exclusion("nonexistent.path", None)
        # Should return None when path doesn't exist
        assert result is None

    def test_sample_non_list_path(self) -> None:
        """Test sampling from path that returns non-list."""
        mock_vocab = MagicMock()
        mock_vocab.get.return_value = "not a list"
        mock_vocab.random.return_value = "fallback"

        sampler = VocabSampler(mock_vocab, seed=42)
        result = sampler._sample_with_exclusion("some.path", None)

        assert result == "fallback"


class TestVocabSamplerReseed:
    """Tests for reseed method."""

    def test_reseed_changes_random_state(self) -> None:
        """Test that reseed changes the random state."""
        vocab = MockVocab()
        sampler = VocabSampler(vocab, seed=42)

        spec = VocabSpec(type="choice", values=list(range(100)))

        # Get some values
        values1 = [sampler.sample_one(spec) for _ in range(5)]

        # Reseed and get same values
        sampler.reseed(42)
        values2 = [sampler.sample_one(spec) for _ in range(5)]

        assert values1 == values2

    def test_reseed_with_none(self) -> None:
        """Test reseeding with None uses random seed."""
        vocab = MockVocab()
        sampler = VocabSampler(vocab)

        sampler.reseed(None)
        assert sampler._rng is not None


class TestVocabSamplerIntegration:
    """Integration tests with real Vocab."""

    @pytest.fixture
    def sampler(self) -> VocabSampler:
        """Create sampler with real vocab."""
        return VocabSampler(get_vocab(), seed=42)

    def test_real_person_sampling(self, sampler: VocabSampler) -> None:
        """Test sampling person with real vocab."""
        specs = {"person": VocabSpec(type="person_with_pronouns")}
        result = sampler.sample(specs)

        assert "person" in result
        person = result["person"]
        assert "name" in person
        assert "subject" in person
        assert "object" in person
        assert "possessive" in person

    def test_real_path_sampling(self, sampler: VocabSampler) -> None:
        """Test sampling from real vocab paths."""
        specs = {"name": VocabSpec(path="names.male")}
        result = sampler.sample(specs)

        assert "name" in result
        assert isinstance(result["name"], str)
        assert len(result["name"]) > 0

    def test_multiple_specs(self, sampler: VocabSampler) -> None:
        """Test sampling multiple specs at once."""
        specs = {
            "person": VocabSpec(type="person_with_pronouns"),
            "item": VocabSpec(path="items.countable_singular"),
            "number": VocabSpec(type="choice", values=[1, 2, 3, 4, 5]),
        }
        result = sampler.sample(specs)

        assert "person" in result
        assert "item" in result
        assert "item_plural" in result  # Auto-added for countable_singular
        assert "number" in result
        assert result["number"] in [1, 2, 3, 4, 5]

    def test_reproducible_sampling(self) -> None:
        """Test that same seed produces same results."""
        specs = {
            "person": VocabSpec(type="person_with_pronouns"),
            "item": VocabSpec(path="items.countable_singular"),
        }

        sampler1 = VocabSampler(get_vocab(), seed=123)
        sampler2 = VocabSampler(get_vocab(), seed=123)

        result1 = sampler1.sample(specs)
        result2 = sampler2.sample(specs)

        assert result1["item"] == result2["item"]
