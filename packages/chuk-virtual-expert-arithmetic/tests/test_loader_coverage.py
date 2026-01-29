"""Additional tests for SchemaLoader - comprehensive coverage."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from chuk_virtual_expert_arithmetic.core.loader import (
    SchemaLoader,
    SchemaLoadError,
    SchemaValidationError,
    get_loader,
    set_loader,
)


class TestSchemaLoaderValidation:
    """Tests for schema validation behavior."""

    def test_load_without_validation(self) -> None:
        """Test loading without Pydantic validation."""
        loader = SchemaLoader()
        schema = loader.load("multiply_add", validate=False)
        assert schema.name == "multiply_add"

    def test_load_with_validation_error(self) -> None:
        """Test validation error on invalid schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            # Write invalid schema with invalid field types
            # variables must be dict of VariableSpec, not a string
            invalid_schema = {
                "name": "test",
                "answer": "x",
                "variables": "invalid_type_should_be_dict",
            }
            (schema_dir / "invalid.json").write_text(json.dumps(invalid_schema))

            loader = SchemaLoader(schema_dir=schema_dir)
            with pytest.raises(SchemaValidationError, match="Validation failed"):
                loader.load("invalid", validate=True)

    def test_load_json_decode_error(self) -> None:
        """Test error on invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            # Write invalid JSON
            (schema_dir / "bad.json").write_text("{ invalid json }")

            loader = SchemaLoader(schema_dir=schema_dir)
            with pytest.raises(SchemaLoadError, match="Invalid JSON"):
                loader.load("bad")

    def test_load_file_not_found(self) -> None:
        """Test error when schema file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            loader = SchemaLoader(schema_dir=schema_dir)
            with pytest.raises(SchemaLoadError, match="Schema not found"):
                loader.load("nonexistent")


class TestSchemaLoaderComposition:
    """Tests for schema composition features."""

    def test_load_with_mixins(self) -> None:
        """Test loading schema with mixins."""
        loader = SchemaLoader(compose=True)
        # Load a schema that uses mixins (if any exist)
        schema = loader.load("multiply_add")
        assert schema is not None

    def test_load_without_composition(self) -> None:
        """Test loading without composition."""
        loader = SchemaLoader(compose=False)
        schema = loader.load("multiply_add")
        assert schema.name == "multiply_add"

    def test_composer_lazy_loading(self) -> None:
        """Test that composer is lazy-loaded."""
        loader = SchemaLoader()
        assert loader._composer is None
        composer = loader._get_composer()
        assert loader._composer is not None
        # Second call returns same instance
        assert loader._get_composer() is composer


class TestSchemaLoaderRaw:
    """Tests for raw schema loading."""

    def test_load_raw(self) -> None:
        """Test loading raw schema dict."""
        loader = SchemaLoader()
        raw = loader.load_raw("multiply_add")
        assert isinstance(raw, dict)
        assert "name" in raw

    def test_load_raw_caching(self) -> None:
        """Test that raw schemas are cached."""
        loader = SchemaLoader()
        raw1 = loader.load_raw("multiply_add")
        raw2 = loader.load_raw("multiply_add")
        # Should be same dict from cache
        assert raw1 is raw2


class TestSchemaLoaderGetAll:
    """Tests for get_all methods."""

    def test_get_all(self) -> None:
        """Test loading all schemas."""
        loader = SchemaLoader()
        schemas = loader.get_all()
        assert len(schemas) > 0
        assert "multiply_add" in schemas

    def test_get_all_without_validation(self) -> None:
        """Test loading all without validation."""
        loader = SchemaLoader()
        schemas = loader.get_all(validate=False)
        assert len(schemas) > 0

    def test_get_all_raw(self) -> None:
        """Test loading all as raw dicts."""
        loader = SchemaLoader()
        schemas = loader.get_all_raw()
        assert len(schemas) > 0
        assert isinstance(schemas["multiply_add"], dict)

    def test_get_all_empty_directory(self) -> None:
        """Test get_all with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all()
            assert schemas == {}

    def test_get_all_raw_empty_directory(self) -> None:
        """Test get_all_raw with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all_raw()
            assert schemas == {}

    def test_get_all_nonexistent_directory(self) -> None:
        """Test get_all with nonexistent directory."""
        loader = SchemaLoader(schema_dir=Path("/nonexistent/path"))
        schemas = loader.get_all()
        assert schemas == {}


class TestSchemaLoaderSubdirectories:
    """Tests for subdirectory loading."""

    def test_load_from_subdirectory(self) -> None:
        """Test loading schema from subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            subdir = schema_dir / "arithmetic"
            subdir.mkdir()

            # Write schema to subdirectory
            schema = {"name": "test_schema", "answer": "x", "variables": {}, "trace": []}
            (subdir / "test_schema.json").write_text(json.dumps(schema))

            loader = SchemaLoader(schema_dir=schema_dir)
            loaded = loader.load("test_schema")
            assert loaded.name == "test_schema"

    def test_skip_mixins_directory(self) -> None:
        """Test that mixins directory is skipped in get_all."""
        loader = SchemaLoader()
        schemas = loader.get_all()
        # No schemas should have names like mixin files
        assert "person_vocab" not in schemas

    def test_skip_bases_directory(self) -> None:
        """Test that bases directory is skipped in get_all."""
        loader = SchemaLoader()
        schemas = loader.get_all()
        # Bases shouldn't be loaded as regular schemas
        assert all(not s.abstract for s in schemas.values() if hasattr(s, "abstract"))


class TestSchemaLoaderModuleLevel:
    """Tests for module-level loader functions."""

    def test_get_loader_singleton(self) -> None:
        """Test get_loader returns singleton."""
        loader1 = get_loader()
        loader2 = get_loader()
        assert loader1 is loader2

    def test_set_loader(self) -> None:
        """Test setting custom loader."""
        original = get_loader()
        custom = SchemaLoader()
        set_loader(custom)
        try:
            assert get_loader() is custom
        finally:
            set_loader(original)


class TestSchemaLoaderReadJsonErrors:
    """Tests for _read_json error handling."""

    def test_oserror_handling(self) -> None:
        """Test OSError handling when reading file."""
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            schema_file = schema_dir / "test.json"
            schema_file.write_text('{"name": "test", "answer": "x"}')

            # Make file unreadable (if possible on this system)
            try:
                os.chmod(schema_file, 0o000)
                loader = SchemaLoader(schema_dir=schema_dir)
                with pytest.raises(SchemaLoadError, match="Cannot read"):
                    loader.load("test")
            except PermissionError:
                # On some systems we can't change permissions
                pass
            finally:
                os.chmod(schema_file, 0o644)


class TestSchemaLoaderGetAllErrors:
    """Tests for get_all error handling."""

    def test_get_all_skips_invalid_in_root(self) -> None:
        """Test get_all skips invalid schemas in root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            # Create valid schema
            (schema_dir / "valid.json").write_text('{"name": "valid", "answer": "x"}')
            # Create invalid schema (bad JSON)
            (schema_dir / "invalid.json").write_text("{ bad json }")

            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all()

            # Only valid schema should be loaded
            assert "valid" in schemas
            assert "invalid" not in schemas

    def test_get_all_skips_invalid_in_subdir(self) -> None:
        """Test get_all skips invalid schemas in subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            subdir = schema_dir / "arithmetic"
            subdir.mkdir()

            # Create valid schema
            (subdir / "valid.json").write_text('{"name": "valid_sub", "answer": "x"}')
            # Create invalid schema (validation error)
            (subdir / "invalid.json").write_text('{"name": "invalid_sub", "answer": "x", "variables": "bad_type"}')

            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all()

            assert "valid_sub" in schemas


class TestSchemaLoaderGetAllRawErrors:
    """Tests for get_all_raw error handling."""

    def test_get_all_raw_skips_invalid_json_in_root(self) -> None:
        """Test get_all_raw skips invalid JSON in root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            (schema_dir / "valid.json").write_text('{"name": "valid", "answer": "x"}')
            (schema_dir / "invalid.json").write_text("{ bad json }")

            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all_raw()

            assert "valid" in schemas
            assert "invalid" not in schemas

    def test_get_all_raw_skips_invalid_json_in_subdir(self) -> None:
        """Test get_all_raw skips invalid JSON in subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            subdir = schema_dir / "arithmetic"
            subdir.mkdir()

            (subdir / "valid.json").write_text('{"name": "valid_sub", "answer": "x"}')
            (subdir / "invalid.json").write_text("{ bad json }")

            loader = SchemaLoader(schema_dir=schema_dir)
            schemas = loader.get_all_raw()

            assert "valid_sub" in schemas


class TestSchemaLoaderExists:
    """Tests for exists method."""

    def test_exists_true(self) -> None:
        """Test exists returns True for existing schema."""
        loader = SchemaLoader()
        assert loader.exists("multiply_add") is True

    def test_exists_false(self) -> None:
        """Test exists returns False for non-existing schema."""
        loader = SchemaLoader()
        assert loader.exists("nonexistent_schema_xyz") is False


class TestSchemaLoaderEdgeCases:
    """Edge case tests for SchemaLoader."""

    def test_load_schema_with_extends_and_mixins(self) -> None:
        """Test loading schema with both extends and mixins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_dir = Path(tmpdir)
            mixins_dir = schema_dir / "mixins"
            mixins_dir.mkdir()

            # Create a mixin
            mixin = {"name": "test_mixin", "vocab": {"item": {"path": "items.test"}}}
            (mixins_dir / "test_mixin.json").write_text(json.dumps(mixin))

            # Create schema using mixin
            schema = {
                "name": "composed_schema",
                "mixins": ["test_mixin"],
                "answer": "x",
                "variables": {},
                "trace": [],
            }
            (schema_dir / "composed_schema.json").write_text(json.dumps(schema))

            loader = SchemaLoader(schema_dir=schema_dir, compose=True)
            loaded = loader.load("composed_schema")
            assert loaded.name == "composed_schema"
            # Should have vocab from mixin
            assert loaded.vocab is not None

    def test_schema_names_property(self) -> None:
        """Test schema_names property."""
        loader = SchemaLoader()
        names = loader.schema_names
        assert isinstance(names, list)
        assert "multiply_add" in names

    def test_clear_cache_clears_both_caches(self) -> None:
        """Test that clear_cache clears both parsed and raw caches."""
        loader = SchemaLoader()
        loader.load("multiply_add")
        loader.load_raw("price_chain")

        assert len(loader._cache) > 0
        assert len(loader._raw_cache) > 0

        loader.clear_cache()

        assert len(loader._cache) == 0
        assert len(loader._raw_cache) == 0
