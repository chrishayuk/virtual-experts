"""Schema composition with mixins and inheritance.

Resolves schema inheritance and mixin application to reduce duplication.

Usage:
    composer = SchemaComposer(schema_dir)
    resolved = composer.compose(schema)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CompositionError(Exception):
    """Raised when schema composition fails."""

    pass


class SchemaComposer:
    """Composes schemas by resolving inheritance and mixins.

    Supports:
    - extends: Single inheritance from a base schema
    - mixins: Multiple mixin composition
    - Deep merging of vocab, template_vars, variables

    Merge rules:
    - Child values override parent/mixin values
    - Dicts are deep merged (child keys override parent keys)
    - Lists are NOT merged (child replaces parent)
    """

    def __init__(self, schema_dir: Path | None = None) -> None:
        """Initialize the composer.

        Args:
            schema_dir: Directory containing schemas, mixins, bases
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "schemas"
        self._schema_dir = schema_dir
        self._mixin_cache: dict[str, dict[str, Any]] = {}
        self._base_cache: dict[str, dict[str, Any]] = {}

    def compose(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Compose a schema by resolving inheritance and mixins.

        Args:
            schema: Raw schema dict

        Returns:
            Fully composed schema dict

        Merge order (later values override earlier):
        1. Base schema (from extends)
        2. Mixins (in order)
        3. Original schema values (highest priority)
        """
        # Keep original values to apply last
        original = dict(schema)
        original.pop("extends", None)
        original.pop("mixins", None)

        result: dict[str, Any] = {}

        # Resolve inheritance first
        if "extends" in schema:
            base_name = schema["extends"]
            base = self._load_base(base_name)
            result = self._merge_schemas(result, base)

        # Apply mixins
        if "mixins" in schema:
            mixin_names = schema["mixins"]
            for mixin_name in mixin_names:
                mixin = self._load_mixin(mixin_name)
                result = self._merge_schemas(result, mixin)

        # Apply original values last (highest priority)
        result = self._merge_schemas(result, original)

        return result

    def _load_mixin(self, name: str) -> dict[str, Any]:
        """Load a mixin by name."""
        if name in self._mixin_cache:
            return self._mixin_cache[name]

        # Try mixins directory
        path = self._schema_dir / "mixins" / f"{name}.json"
        if path.exists():
            mixin = self._read_json(path)
            self._mixin_cache[name] = mixin
            return mixin

        raise CompositionError(f"Mixin not found: {name}")

    def _load_base(self, name: str) -> dict[str, Any]:
        """Load a base schema by name."""
        if name in self._base_cache:
            return self._base_cache[name]

        # Try bases directory first
        path = self._schema_dir / "bases" / f"{name}.json"
        if path.exists():
            base = self._read_json(path)
            # Recursively compose the base
            base = self.compose(base)
            self._base_cache[name] = base
            return base

        # Fall back to regular schema directories
        for subdir in self._schema_dir.iterdir():
            if subdir.is_dir() and subdir.name not in ("mixins", "bases"):
                path = subdir / f"{name}.json"
                if path.exists():
                    base = self._read_json(path)
                    base = self.compose(base)
                    self._base_cache[name] = base
                    return base

        raise CompositionError(f"Base schema not found: {name}")

    def _read_json(self, path: Path) -> dict[str, Any]:
        """Read and parse a JSON file."""
        with open(path) as f:
            data: dict[str, Any] = json.load(f)
            return data

    def _merge_schemas(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two schema dicts.

        Override values take precedence. Dicts are deep merged.
        """
        result = dict(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Deep merge dicts
                result[key] = self._merge_dicts(result[key], value)
            else:
                # Override with new value
                result[key] = value

        return result

    def _merge_dicts(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dicts."""
        result = dict(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def list_mixins(self) -> list[str]:
        """List all available mixin names."""
        mixins_dir = self._schema_dir / "mixins"
        if not mixins_dir.exists():
            return []
        return [p.stem for p in mixins_dir.glob("*.json")]

    def list_bases(self) -> list[str]:
        """List all available base schema names."""
        bases_dir = self._schema_dir / "bases"
        if not bases_dir.exists():
            return []
        return [p.stem for p in bases_dir.glob("*.json")]

    def clear_cache(self) -> None:
        """Clear all cached mixins and bases."""
        self._mixin_cache.clear()
        self._base_cache.clear()
