"""Additional tests for SchemaComposer - comprehensive coverage."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from chuk_virtual_expert_arithmetic.core.composer import CompositionError, SchemaComposer


class TestSchemaComposerInit:
    """Tests for SchemaComposer initialization."""

    def test_default_schema_dir(self) -> None:
        """Test default schema directory."""
        composer = SchemaComposer()
        assert composer._schema_dir.exists()

    def test_custom_schema_dir(self) -> None:
        """Test custom schema directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SchemaComposer(schema_dir=Path(tmpdir))
            assert composer._schema_dir == Path(tmpdir)


class TestSchemaComposerLoadBase:
    """Tests for loading base schemas."""

    def test_load_base_from_bases_dir(self) -> None:
        """Test loading base from bases directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            bases_dir = schema_dir / "bases"
            bases_dir.mkdir()

            # Create base schema
            base = {"name": "test_base", "vocab": {"person": {"type": "person_with_pronouns"}}}
            (bases_dir / "test_base.json").write_text(json.dumps(base))

            composer = SchemaComposer(schema_dir=schema_dir)
            loaded = composer._load_base("test_base")

            assert loaded["name"] == "test_base"
            assert "vocab" in loaded

    def test_load_base_from_regular_dir(self) -> None:
        """Test loading base from regular schema directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            subdir = schema_dir / "arithmetic"
            subdir.mkdir()

            # Create schema in regular directory (not bases)
            base = {"name": "regular_base", "variables": {"x": {"type": "int"}}}
            (subdir / "regular_base.json").write_text(json.dumps(base))

            composer = SchemaComposer(schema_dir=schema_dir)
            loaded = composer._load_base("regular_base")

            assert loaded["name"] == "regular_base"

    def test_load_base_not_found(self) -> None:
        """Test error when base not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SchemaComposer(schema_dir=Path(tmpdir))
            with pytest.raises(CompositionError, match="Base schema not found"):
                composer._load_base("nonexistent_base")

    def test_load_base_caching(self) -> None:
        """Test that bases are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            bases_dir = schema_dir / "bases"
            bases_dir.mkdir()

            base = {"name": "cached_base"}
            (bases_dir / "cached_base.json").write_text(json.dumps(base))

            composer = SchemaComposer(schema_dir=schema_dir)
            loaded1 = composer._load_base("cached_base")
            loaded2 = composer._load_base("cached_base")

            assert loaded1 is loaded2


class TestSchemaComposerLoadMixin:
    """Tests for loading mixins."""

    def test_load_mixin(self) -> None:
        """Test loading a mixin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            mixin = {"name": "test_mixin", "template_vars": {"name": "person.name"}}
            (mixins_dir / "test_mixin.json").write_text(json.dumps(mixin))

            composer = SchemaComposer(schema_dir=schema_dir)
            loaded = composer._load_mixin("test_mixin")

            assert loaded["name"] == "test_mixin"

    def test_load_mixin_not_found(self) -> None:
        """Test error when mixin not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SchemaComposer(schema_dir=Path(tmpdir))
            with pytest.raises(CompositionError, match="Mixin not found"):
                composer._load_mixin("nonexistent_mixin")

    def test_load_mixin_caching(self) -> None:
        """Test that mixins are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            mixin = {"name": "cached_mixin"}
            (mixins_dir / "cached_mixin.json").write_text(json.dumps(mixin))

            composer = SchemaComposer(schema_dir=schema_dir)
            loaded1 = composer._load_mixin("cached_mixin")
            loaded2 = composer._load_mixin("cached_mixin")

            assert loaded1 is loaded2


class TestSchemaComposerCompose:
    """Tests for compose method."""

    def test_compose_no_extends_or_mixins(self) -> None:
        """Test compose with simple schema."""
        composer = SchemaComposer()
        schema = {"name": "simple", "variables": {"x": {"type": "int"}}}

        result = composer.compose(schema)

        assert result["name"] == "simple"
        assert result["variables"] == {"x": {"type": "int"}}

    def test_compose_with_extends(self) -> None:
        """Test compose with extends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            bases_dir = schema_dir / "bases"
            bases_dir.mkdir()

            # Create base
            base = {
                "name": "base",
                "vocab": {"person": {"type": "person_with_pronouns"}},
                "template_vars": {"name": "person.name"},
            }
            (bases_dir / "base.json").write_text(json.dumps(base))

            composer = SchemaComposer(schema_dir=schema_dir)
            schema = {
                "name": "derived",
                "extends": "base",
                "variables": {"x": {"type": "int"}},
            }

            result = composer.compose(schema)

            assert result["name"] == "derived"
            assert "vocab" in result
            assert "template_vars" in result
            assert "variables" in result
            assert "extends" not in result

    def test_compose_with_mixins(self) -> None:
        """Test compose with mixins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            # Create mixins
            mixin1 = {"name": "mixin1", "vocab": {"item": {"path": "items.test"}}}
            mixin2 = {"name": "mixin2", "template_vars": {"count": "count"}}
            (mixins_dir / "mixin1.json").write_text(json.dumps(mixin1))
            (mixins_dir / "mixin2.json").write_text(json.dumps(mixin2))

            composer = SchemaComposer(schema_dir=schema_dir)
            schema = {
                "name": "mixed",
                "mixins": ["mixin1", "mixin2"],
                "answer": "x",
            }

            result = composer.compose(schema)

            assert result["name"] == "mixed"
            assert "vocab" in result
            assert "template_vars" in result
            assert "mixins" not in result

    def test_compose_override_order(self) -> None:
        """Test that child values override parent/mixin values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            mixin = {"name": "mixin", "template_vars": {"name": "original"}}
            (mixins_dir / "mixin.json").write_text(json.dumps(mixin))

            composer = SchemaComposer(schema_dir=schema_dir)
            schema = {
                "name": "child",
                "mixins": ["mixin"],
                "template_vars": {"name": "overridden"},
            }

            result = composer.compose(schema)

            assert result["template_vars"]["name"] == "overridden"

    def test_compose_recursive_base(self) -> None:
        """Test compose with recursive base inheritance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            bases_dir = schema_dir / "bases"
            bases_dir.mkdir()

            # Create base that extends another base
            grandparent = {"name": "grandparent", "vocab": {"a": {"type": "choice"}}}
            parent = {"name": "parent", "extends": "grandparent", "vocab": {"b": {"type": "choice"}}}

            (bases_dir / "grandparent.json").write_text(json.dumps(grandparent))
            (bases_dir / "parent.json").write_text(json.dumps(parent))

            composer = SchemaComposer(schema_dir=schema_dir)
            schema = {"name": "child", "extends": "parent"}

            result = composer.compose(schema)

            assert result["name"] == "child"
            assert "a" in result["vocab"]
            assert "b" in result["vocab"]


class TestSchemaComposerMerge:
    """Tests for merge methods."""

    @pytest.fixture
    def composer(self) -> SchemaComposer:
        """Create composer instance."""
        return SchemaComposer()

    def test_merge_schemas_simple(self, composer: SchemaComposer) -> None:
        """Test simple schema merging."""
        base = {"a": 1, "b": 2}
        override = {"b": 20, "c": 3}

        result = composer._merge_schemas(base, override)

        assert result["a"] == 1
        assert result["b"] == 20
        assert result["c"] == 3

    def test_merge_schemas_deep(self, composer: SchemaComposer) -> None:
        """Test deep schema merging."""
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 20, "c": 3}}

        result = composer._merge_schemas(base, override)

        assert result["outer"]["a"] == 1
        assert result["outer"]["b"] == 20
        assert result["outer"]["c"] == 3

    def test_merge_dicts_simple(self, composer: SchemaComposer) -> None:
        """Test simple dict merging."""
        base = {"x": 1}
        override = {"y": 2}

        result = composer._merge_dicts(base, override)

        assert result == {"x": 1, "y": 2}

    def test_merge_dicts_nested(self, composer: SchemaComposer) -> None:
        """Test nested dict merging."""
        base = {"level1": {"level2": {"a": 1}}}
        override = {"level1": {"level2": {"b": 2}}}

        result = composer._merge_dicts(base, override)

        assert result["level1"]["level2"]["a"] == 1
        assert result["level1"]["level2"]["b"] == 2


class TestSchemaComposerList:
    """Tests for list methods."""

    def test_list_mixins(self) -> None:
        """Test listing available mixins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            (mixins_dir / "mixin_a.json").write_text("{}")
            (mixins_dir / "mixin_b.json").write_text("{}")

            composer = SchemaComposer(schema_dir=schema_dir)
            mixins = composer.list_mixins()

            assert "mixin_a" in mixins
            assert "mixin_b" in mixins

    def test_list_mixins_empty(self) -> None:
        """Test listing mixins when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SchemaComposer(schema_dir=Path(tmpdir))
            mixins = composer.list_mixins()
            assert mixins == []

    def test_list_bases(self) -> None:
        """Test listing available bases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            bases_dir = schema_dir / "bases"
            bases_dir.mkdir()

            (bases_dir / "base_x.json").write_text("{}")
            (bases_dir / "base_y.json").write_text("{}")

            composer = SchemaComposer(schema_dir=schema_dir)
            bases = composer.list_bases()

            assert "base_x" in bases
            assert "base_y" in bases

    def test_list_bases_empty(self) -> None:
        """Test listing bases when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SchemaComposer(schema_dir=Path(tmpdir))
            bases = composer.list_bases()
            assert bases == []


class TestSchemaComposerClearCache:
    """Tests for cache clearing."""

    def test_clear_cache(self) -> None:
        """Test clearing caches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            bases_dir = schema_dir / "bases"
            mixins_dir.mkdir()
            bases_dir.mkdir()

            (mixins_dir / "test_mixin.json").write_text("{}")
            (bases_dir / "test_base.json").write_text("{}")

            composer = SchemaComposer(schema_dir=schema_dir)
            composer._load_mixin("test_mixin")
            composer._load_base("test_base")

            assert len(composer._mixin_cache) > 0
            assert len(composer._base_cache) > 0

            composer.clear_cache()

            assert len(composer._mixin_cache) == 0
            assert len(composer._base_cache) == 0


class TestSchemaComposerIntegration:
    """Integration tests with real schemas."""

    def test_compose_real_schema_with_mixin(self) -> None:
        """Test composing a real schema with mixins."""
        composer = SchemaComposer()

        # Load a schema that uses mixins
        mixins = composer.list_mixins()
        if "person_vocab" in mixins:
            schema = {"name": "test", "mixins": ["person_vocab"], "answer": "x"}
            result = composer.compose(schema)

            assert "vocab" in result
            assert "person" in result["vocab"]

    def test_compose_preserves_name(self) -> None:
        """Test that compose preserves child's name."""
        composer = SchemaComposer()

        # Even when using mixins/extends, child name should win
        mixins = composer.list_mixins()
        if mixins:
            schema = {"name": "my_custom_name", "mixins": [mixins[0]], "answer": "x"}
            result = composer.compose(schema)

            assert result["name"] == "my_custom_name"
