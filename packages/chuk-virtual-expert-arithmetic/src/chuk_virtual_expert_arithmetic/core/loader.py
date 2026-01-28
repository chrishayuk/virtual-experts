"""Schema loading and validation.

Loads JSON schemas, validates them against Pydantic models,
and caches parsed schemas for performance.

Usage:
    loader = SchemaLoader()
    schema = loader.load("multiply_add")
    all_schemas = loader.get_all()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chuk_virtual_expert_arithmetic.models.schema_spec import SchemaSpec

if TYPE_CHECKING:
    from chuk_virtual_expert_arithmetic.core.composer import SchemaComposer


class SchemaLoadError(Exception):
    """Raised when schema loading fails."""

    pass


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""

    pass


class SchemaLoader:
    """Loads and validates schema JSON files.

    Provides:
    - Schema loading from filesystem
    - Pydantic validation at load time
    - Schema composition (mixins, inheritance)
    - Caching for performance
    - Support for subdirectory organization (by expert type)
    """

    def __init__(
        self,
        schema_dir: Path | None = None,
        compose: bool = True,
    ) -> None:
        """Initialize the loader.

        Args:
            schema_dir: Directory containing schemas. Defaults to package schemas dir.
            compose: Whether to resolve mixins and inheritance
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "schemas"
        self._schema_dir = schema_dir
        self._compose = compose
        self._composer: SchemaComposer | None = None
        self._cache: dict[str, SchemaSpec] = {}
        self._raw_cache: dict[str, dict[str, Any]] = {}

    def _get_composer(self) -> SchemaComposer:
        """Lazy-load the composer to avoid circular imports."""
        if self._composer is None:
            from chuk_virtual_expert_arithmetic.core.composer import SchemaComposer

            self._composer = SchemaComposer(self._schema_dir)
        return self._composer

    def load(self, name: str, validate: bool = True) -> SchemaSpec:
        """Load a schema by name.

        Args:
            name: Schema name (e.g., "multiply_add")
            validate: Whether to validate with Pydantic

        Returns:
            Parsed SchemaSpec

        Raises:
            SchemaLoadError: If schema file not found
            SchemaValidationError: If validation fails
        """
        if name in self._cache:
            return self._cache[name]

        raw = self._load_raw(name)

        # Apply composition (resolve mixins and inheritance)
        if self._compose and ("extends" in raw or "mixins" in raw):
            raw = self._get_composer().compose(raw)

        if validate:
            try:
                schema = SchemaSpec(**raw)
            except Exception as e:
                raise SchemaValidationError(f"Validation failed for '{name}': {e}") from e
        else:
            schema = SchemaSpec.model_construct(**raw)

        self._cache[name] = schema
        return schema

    def load_raw(self, name: str) -> dict[str, Any]:
        """Load raw schema dict without validation.

        Useful for backward compatibility or when you need the raw dict.

        Args:
            name: Schema name

        Returns:
            Raw schema dict
        """
        return self._load_raw(name)

    def _load_raw(self, name: str) -> dict[str, Any]:
        """Load raw schema from filesystem."""
        if name in self._raw_cache:
            return self._raw_cache[name]

        # Try root directory first
        path = self._schema_dir / f"{name}.json"
        if path.exists():
            raw = self._read_json(path)
            self._raw_cache[name] = raw
            return raw

        # Search subdirectories
        for subdir in self._schema_dir.iterdir():
            if subdir.is_dir():
                path = subdir / f"{name}.json"
                if path.exists():
                    raw = self._read_json(path)
                    self._raw_cache[name] = raw
                    return raw

        raise SchemaLoadError(f"Schema not found: {name}")

    def _read_json(self, path: Path) -> dict[str, Any]:
        """Read and parse a JSON file."""
        try:
            with open(path) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except json.JSONDecodeError as e:
            raise SchemaLoadError(f"Invalid JSON in {path}: {e}") from e
        except OSError as e:
            raise SchemaLoadError(f"Cannot read {path}: {e}") from e

    # Directories to skip when loading schemas
    SKIP_DIRS = {"mixins", "bases"}

    def get_all(self, validate: bool = True) -> dict[str, SchemaSpec]:
        """Load all available schemas.

        Args:
            validate: Whether to validate schemas

        Returns:
            Dict of schema name -> SchemaSpec
        """
        schemas: dict[str, SchemaSpec] = {}

        if not self._schema_dir.exists():
            return schemas

        # Load from root directory
        for path in self._schema_dir.glob("*.json"):
            name = path.stem
            try:
                schemas[name] = self.load(name, validate=validate)
            except (SchemaLoadError, SchemaValidationError):
                # Skip invalid schemas
                pass

        # Load from subdirectories (skip mixins/bases)
        for subdir in self._schema_dir.iterdir():
            if subdir.is_dir() and subdir.name not in self.SKIP_DIRS:
                for path in subdir.glob("*.json"):
                    raw = self._read_json(path)
                    name = raw.get("name", path.stem)
                    if name not in schemas:
                        try:
                            # Use the name from the file, not path.stem
                            self._raw_cache[name] = raw
                            schemas[name] = self.load(name, validate=validate)
                        except (SchemaLoadError, SchemaValidationError):
                            pass

        return schemas

    def get_all_raw(self) -> dict[str, dict[str, Any]]:
        """Load all schemas as raw dicts without validation.

        Returns:
            Dict of schema name -> raw dict
        """
        schemas: dict[str, dict[str, Any]] = {}

        if not self._schema_dir.exists():
            return schemas

        # Load from root directory
        for path in self._schema_dir.glob("*.json"):
            try:
                raw = self._read_json(path)
                name = raw.get("name", path.stem)
                schemas[name] = raw
            except SchemaLoadError:
                pass

        # Load from subdirectories (skip mixins/bases)
        for subdir in self._schema_dir.iterdir():
            if subdir.is_dir() and subdir.name not in self.SKIP_DIRS:
                for path in subdir.glob("*.json"):
                    try:
                        raw = self._read_json(path)
                        name = raw.get("name", path.stem)
                        if name not in schemas:
                            schemas[name] = raw
                    except SchemaLoadError:
                        pass

        return schemas

    @property
    def schema_names(self) -> list[str]:
        """List all available schema names."""
        return list(self.get_all_raw().keys())

    def clear_cache(self) -> None:
        """Clear all cached schemas."""
        self._cache.clear()
        self._raw_cache.clear()

    def exists(self, name: str) -> bool:
        """Check if a schema exists.

        Args:
            name: Schema name to check

        Returns:
            True if schema exists
        """
        try:
            self._load_raw(name)
            return True
        except SchemaLoadError:
            return False


# Module-level default loader
_default_loader: SchemaLoader | None = None


def get_loader() -> SchemaLoader:
    """Get the default loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = SchemaLoader()
    return _default_loader


def set_loader(loader: SchemaLoader) -> None:
    """Set the default loader instance."""
    global _default_loader
    _default_loader = loader
