# Creating Virtual Experts: A Complete Guide

This guide walks through creating a production-ready virtual expert from scratch, using the Time Expert as a reference implementation. By the end, you'll have a fully tested, documented, and deployable virtual expert package.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Step 1: Create Package Structure](#step-1-create-package-structure)
5. [Step 2: Define Enums (No Magic Strings)](#step-2-define-enums-no-magic-strings)
6. [Step 3: Implement the Expert Class](#step-3-implement-the-expert-class)
7. [Step 4: Create CoT Examples](#step-4-create-cot-examples)
8. [Step 5: Write Comprehensive Tests](#step-5-write-comprehensive-tests)
9. [Step 6: Configure pyproject.toml](#step-6-configure-pyprojecttoml)
10. [Step 7: Create Makefile](#step-7-create-makefile)
11. [Step 8: Write README](#step-8-write-readme)
12. [Step 9: GitHub Actions CI/CD](#step-9-github-actions-cicd)
13. [Step 10: Publishing](#step-10-publishing)
14. [Best Practices Checklist](#best-practices-checklist)

---

## Overview

Virtual experts are specialized plugins that language models can route to for domain-specific tasks. Each expert:

- **Returns structured data** - `dict[str, Any]` for model chain-of-thought reasoning
- **Is async-native** - Supports both sync and async execution
- **Is Pydantic-native** - Type-safe with validation throughout
- **Has no magic strings** - Uses enums for operations, query types, and constants
- **Has 90%+ test coverage** - Comprehensive tests for reliability
- **Has CI/CD** - Automated testing, linting, and publishing

### Two Types of Experts

1. **VirtualExpert** - For experts with local logic (computations, transformations)
2. **MCPExpert** - For experts that delegate to remote MCP servers (recommended for complex operations)

The Time Expert uses `MCPExpert` to delegate to a hosted MCP server for NTP-accurate time.

---

## Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Git
- GitHub account (for CI/CD)

---

## Project Structure

```
chuk-virtual-expert-{name}/
├── .github/
│   └── workflows/
│       ├── ci-{name}-expert.yml      # CI workflow
│       └── publish-{name}-expert.yml # PyPI publish workflow
├── src/
│   └── chuk_virtual_expert_{name}/
│       ├── __init__.py               # Package exports
│       ├── expert.py                 # Expert class with enums
│       ├── cot_examples.json         # Training examples
│       ├── schema.json               # Operation schema
│       └── calibration.json          # Calibration data
├── tests/
│   ├── __init__.py
│   ├── test_expert.py               # Expert class tests
│   ├── test_enums.py                # Enum tests
│   └── test_init.py                 # Package export tests
├── Makefile                          # Development commands
├── pyproject.toml                    # Package configuration
├── README.md                         # Documentation
└── LICENSE                           # MIT license
```

---

## Step 1: Create Package Structure

Create the directory structure:

```bash
mkdir -p chuk-virtual-expert-myexpert/src/chuk_virtual_expert_myexpert
mkdir -p chuk-virtual-expert-myexpert/tests
mkdir -p chuk-virtual-expert-myexpert/.github/workflows
cd chuk-virtual-expert-myexpert
```

Create `src/chuk_virtual_expert_myexpert/__init__.py`:

```python
"""
chuk-virtual-expert-myexpert: My domain-specific virtual expert.

Async-native, Pydantic-native, no magic strings.
"""

from chuk_virtual_expert_myexpert.expert import (
    MyExpert,
    MyOperation,
    MyQueryType,
)

__all__ = [
    "MyExpert",
    "MyOperation",
    "MyQueryType",
]

__version__ = "1.0.0"
```

---

## Step 2: Define Enums (No Magic Strings)

All string constants should be enums. This provides:
- Type safety
- IDE autocomplete
- Refactoring support
- Documentation

Create `src/chuk_virtual_expert_myexpert/expert.py` with enums:

```python
"""
My virtual expert implementation.

Pydantic-native, async-native, no magic strings.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar


class MyOperation(str, Enum):
    """Operations supported by this expert."""

    DO_THING = "do_thing"
    DO_OTHER = "do_other"
    GET_INFO = "get_info"


class MyQueryType(str, Enum):
    """Query result types for this expert."""

    THING_RESULT = "thing_result"
    OTHER_RESULT = "other_result"
    INFO_RESULT = "info_result"
    ERROR = "error"


# Constants as dictionaries (not inline strings)
MY_KEYWORDS: list[str] = [
    "keyword1",
    "keyword2",
    "something",
]
```

**Time Expert Example:**

```python
class TimeOperation(str, Enum):
    """Operations supported by the time expert."""
    GET_TIME = "get_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"


class TimeMCPTool(str, Enum):
    """MCP tool names from chuk-mcp-time server."""
    GET_LOCAL_TIME = "get_local_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"


class TimeQueryType(str, Enum):
    """Query result types for time expert."""
    CURRENT_TIME = "current_time"
    CONVERSION = "conversion"
    TIMEZONE_INFO = "timezone_info"
    ERROR = "error"
```

---

## Step 3: Implement the Expert Class

### Option A: VirtualExpert (Local Logic)

For experts that compute results locally:

```python
from chuk_virtual_expert import VirtualExpert


class MyExpert(VirtualExpert):
    """My domain-specific expert with local logic."""

    # Class configuration
    name: ClassVar[str] = "myexpert"
    description: ClassVar[str] = "Does domain-specific operations"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 5

    # File paths (relative to module)
    cot_examples_file: ClassVar[str] = "cot_examples.json"
    schema_file: ClassVar[str] = "schema.json"

    # Keywords for can_handle check
    _KEYWORDS: ClassVar[list[str]] = MY_KEYWORDS

    def can_handle(self, prompt: str) -> bool:
        """Check if this expert can handle the prompt."""
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self._KEYWORDS)

    def get_operations(self) -> list[str]:
        """Return list of available operations."""
        return [op.value for op in MyOperation]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute operation by name."""
        op = MyOperation(operation)

        if op == MyOperation.DO_THING:
            return self._do_thing(**parameters)
        elif op == MyOperation.DO_OTHER:
            return self._do_other(**parameters)
        elif op == MyOperation.GET_INFO:
            return self._get_info(**parameters)
        else:
            return {
                "query_type": MyQueryType.ERROR.value,
                "error": f"Unknown operation: {operation}",
            }

    def _do_thing(self, param1: str, param2: int = 10) -> dict[str, Any]:
        """Actual implementation."""
        return {
            "query_type": MyQueryType.THING_RESULT.value,
            "result": f"Did thing with {param1}",
            "count": param2,
        }

    def _do_other(self, **kwargs: Any) -> dict[str, Any]:
        """Another operation."""
        return {
            "query_type": MyQueryType.OTHER_RESULT.value,
            "data": kwargs,
        }

    def _get_info(self, item: str) -> dict[str, Any]:
        """Get information about something."""
        return {
            "query_type": MyQueryType.INFO_RESULT.value,
            "item": item,
            "info": f"Information about {item}",
        }
```

### Option B: MCPExpert (Remote MCP Server)

For experts that delegate to MCP servers (recommended for complex operations):

```python
from chuk_virtual_expert.mcp_expert import MCPExpert


class TimeExpert(MCPExpert):
    """Time expert backed by MCP server."""

    # Class configuration
    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Get current time and perform timezone conversions"
    version: ClassVar[str] = "3.0.0"
    priority: ClassVar[int] = 5

    # MCP server configuration
    mcp_server_url: ClassVar[str] = "https://time.chukai.io/mcp"
    mcp_timeout: ClassVar[float] = 30.0

    # File paths
    cot_examples_file: ClassVar[str] = "cot_examples.json"
    schema_file: ClassVar[str] = "schema.json"

    # Keywords for can_handle
    _TIME_KEYWORDS: ClassVar[list[str]] = [
        "time", "timezone", "clock", "utc", "gmt",
        "est", "pst", "cst", "jst", "convert",
    ]

    def can_handle(self, prompt: str) -> bool:
        """Check if this expert can handle the prompt."""
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self._TIME_KEYWORDS)

    def get_operations(self) -> list[str]:
        """Return list of available operations."""
        return [op.value for op in TimeOperation]

    def get_mcp_tool_name(self, operation: str) -> str:
        """Map virtual expert operation to MCP tool name."""
        op = TimeOperation(operation)

        mapping = {
            TimeOperation.GET_TIME: TimeMCPTool.GET_LOCAL_TIME,
            TimeOperation.CONVERT_TIME: TimeMCPTool.CONVERT_TIME,
            TimeOperation.GET_TIMEZONE_INFO: TimeMCPTool.GET_TIMEZONE_INFO,
        }

        tool = mapping.get(op)
        if not tool:
            raise ValueError(f"Unknown operation: {operation}")

        return tool.value

    def transform_parameters(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Transform virtual expert parameters to MCP tool arguments."""
        op = TimeOperation(operation)

        if op == TimeOperation.GET_TIME:
            timezone = parameters.get("timezone", "UTC")
            return {"timezone": timezone, "mode": "fast"}

        elif op == TimeOperation.CONVERT_TIME:
            return {
                "datetime_str": parameters.get("time", ""),
                "from_timezone": parameters.get("from_timezone", "UTC"),
                "to_timezone": parameters.get("to_timezone", "UTC"),
            }

        return parameters

    def transform_result(
        self, operation: str, tool_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Transform MCP tool result to virtual expert format."""
        op = TimeOperation(operation)

        # Handle error results
        if "error" in tool_result:
            return {
                "query_type": TimeQueryType.ERROR.value,
                "error": tool_result["error"],
            }

        if op == TimeOperation.GET_TIME:
            return {
                "query_type": TimeQueryType.CURRENT_TIME.value,
                "timezone": tool_result.get("timezone", ""),
                "iso8601": tool_result.get("local_datetime", ""),
                # ... more fields
            }

        return tool_result
```

---

## Step 4: Create CoT Examples

Create `src/chuk_virtual_expert_myexpert/cot_examples.json`:

```json
{
  "expert_name": "myexpert",
  "examples": [
    {
      "query": "Do the thing with foo",
      "action": {
        "expert": "myexpert",
        "operation": "do_thing",
        "parameters": {"param1": "foo"},
        "confidence": 1.0,
        "reasoning": "User wants to do the thing with foo"
      }
    },
    {
      "query": "Get info about bar",
      "action": {
        "expert": "myexpert",
        "operation": "get_info",
        "parameters": {"item": "bar"},
        "confidence": 1.0,
        "reasoning": "User wants information about bar"
      }
    },
    {
      "query": "Tell me a joke",
      "action": {
        "expert": "none",
        "operation": "passthrough",
        "parameters": {},
        "confidence": 1.0,
        "reasoning": "Not related to myexpert domain"
      }
    }
  ]
}
```

Create `src/chuk_virtual_expert_myexpert/schema.json`:

```json
{
  "name": "myexpert",
  "description": "Does domain-specific operations",
  "operations": {
    "do_thing": {
      "description": "Does the thing",
      "parameters": {
        "param1": {
          "type": "string",
          "description": "What to do",
          "required": true
        },
        "param2": {
          "type": "integer",
          "description": "How many times",
          "default": 10
        }
      }
    },
    "get_info": {
      "description": "Get information about an item",
      "parameters": {
        "item": {
          "type": "string",
          "description": "Item to get info about",
          "required": true
        }
      }
    }
  }
}
```

---

## Step 5: Write Comprehensive Tests

**Coverage Requirement: 90%+ for each file**

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_expert.py           # Expert class tests
├── test_enums.py            # Enum tests
├── test_init.py             # Package export tests
└── test_integration.py      # Integration tests (optional)
```

### tests/conftest.py

```python
"""Shared test fixtures."""

import pytest

from chuk_virtual_expert_myexpert import MyExpert


@pytest.fixture
def expert() -> MyExpert:
    """Create expert instance for testing."""
    return MyExpert()
```

### tests/test_enums.py

```python
"""Tests for enum definitions."""

from chuk_virtual_expert_myexpert.expert import (
    MyOperation,
    MyQueryType,
)


class TestMyOperation:
    """Tests for MyOperation enum."""

    def test_do_thing_value(self):
        assert MyOperation.DO_THING.value == "do_thing"

    def test_do_other_value(self):
        assert MyOperation.DO_OTHER.value == "do_other"

    def test_get_info_value(self):
        assert MyOperation.GET_INFO.value == "get_info"

    def test_is_string_enum(self):
        assert isinstance(MyOperation.DO_THING, str)

    def test_all_operations_listed(self):
        ops = list(MyOperation)
        assert len(ops) == 3


class TestMyQueryType:
    """Tests for MyQueryType enum."""

    def test_thing_result_value(self):
        assert MyQueryType.THING_RESULT.value == "thing_result"

    def test_error_value(self):
        assert MyQueryType.ERROR.value == "error"
```

### tests/test_expert.py

```python
"""Tests for MyExpert class."""

from typing import ClassVar

import pytest

from chuk_virtual_expert.models import VirtualExpertAction
from chuk_virtual_expert_myexpert import MyExpert, MyOperation, MyQueryType


class TestExpertClassAttributes:
    """Tests for expert class attributes."""

    def test_name(self, expert):
        assert expert.name == "myexpert"

    def test_description(self, expert):
        assert "domain-specific" in expert.description

    def test_version(self, expert):
        assert expert.version == "1.0.0"

    def test_priority(self, expert):
        assert expert.priority == 5


class TestCanHandle:
    """Tests for can_handle method."""

    def test_handles_keyword1(self, expert):
        assert expert.can_handle("Do something with keyword1")

    def test_handles_keyword2(self, expert):
        assert expert.can_handle("Use keyword2 here")

    def test_rejects_unrelated(self, expert):
        assert not expert.can_handle("Tell me a joke")

    def test_case_insensitive(self, expert):
        assert expert.can_handle("KEYWORD1 something")


class TestGetOperations:
    """Tests for get_operations method."""

    def test_returns_all_operations(self, expert):
        ops = expert.get_operations()
        assert MyOperation.DO_THING.value in ops
        assert MyOperation.DO_OTHER.value in ops
        assert MyOperation.GET_INFO.value in ops

    def test_returns_correct_count(self, expert):
        ops = expert.get_operations()
        assert len(ops) == len(MyOperation)


class TestExecuteOperation:
    """Tests for execute_operation method."""

    def test_do_thing(self, expert):
        result = expert.execute_operation(
            MyOperation.DO_THING.value,
            {"param1": "test"}
        )
        assert result["query_type"] == MyQueryType.THING_RESULT.value
        assert "test" in result["result"]

    def test_do_thing_with_param2(self, expert):
        result = expert.execute_operation(
            MyOperation.DO_THING.value,
            {"param1": "test", "param2": 20}
        )
        assert result["count"] == 20

    def test_get_info(self, expert):
        result = expert.execute_operation(
            MyOperation.GET_INFO.value,
            {"item": "something"}
        )
        assert result["query_type"] == MyQueryType.INFO_RESULT.value
        assert result["item"] == "something"

    def test_unknown_operation_returns_error(self, expert):
        with pytest.raises(ValueError):
            expert.execute_operation("invalid_op", {})


class TestExecute:
    """Tests for execute method with VirtualExpertAction."""

    def test_execute_success(self, expert):
        action = VirtualExpertAction(
            expert="myexpert",
            operation=MyOperation.DO_THING.value,
            parameters={"param1": "test"},
        )
        result = expert.execute(action)

        assert result.success is True
        assert result.expert_name == "myexpert"
        assert result.data is not None
        assert result.data["query_type"] == MyQueryType.THING_RESULT.value

    def test_execute_failure(self, expert):
        action = VirtualExpertAction(
            expert="myexpert",
            operation="invalid",
            parameters={},
        )
        result = expert.execute(action)

        assert result.success is False
        assert result.error is not None


class TestExecuteAsync:
    """Tests for async execution."""

    @pytest.mark.asyncio
    async def test_execute_operation_async(self, expert):
        result = await expert.execute_operation_async(
            MyOperation.DO_THING.value,
            {"param1": "async_test"}
        )
        assert result["query_type"] == MyQueryType.THING_RESULT.value

    @pytest.mark.asyncio
    async def test_execute_async(self, expert):
        action = VirtualExpertAction(
            expert="myexpert",
            operation=MyOperation.GET_INFO.value,
            parameters={"item": "async_item"},
        )
        result = await expert.execute_async(action)

        assert result.success is True
        assert result.data["item"] == "async_item"
```

### tests/test_init.py

```python
"""Tests for package __init__.py exports."""


class TestPackageExports:
    """Tests for package exports."""

    def test_exports_expert(self):
        from chuk_virtual_expert_myexpert import MyExpert
        assert MyExpert is not None

    def test_exports_operation_enum(self):
        from chuk_virtual_expert_myexpert import MyOperation
        assert MyOperation is not None

    def test_exports_query_type_enum(self):
        from chuk_virtual_expert_myexpert import MyQueryType
        assert MyQueryType is not None


class TestAllExports:
    """Tests for __all__ exports."""

    def test_all_exports_are_importable(self):
        import chuk_virtual_expert_myexpert

        for name in chuk_virtual_expert_myexpert.__all__:
            obj = getattr(chuk_virtual_expert_myexpert, name)
            assert obj is not None, f"{name} should not be None"
```

### Running Tests with Coverage

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Check coverage report
make coverage-report
```

**Target: 90%+ coverage for each file**

---

## Step 6: Configure pyproject.toml

```toml
[project]
name = "chuk-virtual-expert-myexpert"
version = "1.0.0"
description = "My domain-specific virtual expert for LLM routing"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    { name = "Your Name" }
]
keywords = [
    "virtual-expert",
    "llm",
    "pydantic",
    "async",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "chuk-virtual-expert>=2.0.0",
]

# For MCP-backed experts, use:
# dependencies = [
#     "chuk-virtual-expert[mcp]>=2.0.0",
# ]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "coverage[toml]>=7.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "bandit>=1.7",
    "twine>=4.0",
    "build>=1.0",
]

[project.urls]
Homepage = "https://github.com/yourname/virtual-experts"
Repository = "https://github.com/yourname/virtual-experts"
Issues = "https://github.com/yourname/virtual-experts/issues"

[project.entry-points."chuk_virtual_expert.plugins"]
myexpert = "chuk_virtual_expert_myexpert:MyExpert"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/chuk_virtual_expert_myexpert"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src/chuk_virtual_expert_myexpert"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
fail_under = 90
show_missing = true

[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = ["E501"]  # line too long (handled by formatter)

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101"]  # assert used for tests
```

---

## Step 7: Create Makefile

```makefile
.PHONY: help clean clean-pyc clean-build clean-test clean-all install dev-install test test-cov coverage-report lint format typecheck security check build version bump-patch bump-minor bump-major publish publish-test publish-manual release

# Detect if 'uv' is available for faster operations
UV := $(shell command -v uv 2> /dev/null)

help:
	@echo "chuk-virtual-expert-myexpert - My domain virtual expert"
	@echo ""
	@echo "Available targets:"
	@echo "  help              Show this help message"
	@echo ""
	@echo "Clean targets:"
	@echo "  clean             Clean basic artifacts (pyc, build)"
	@echo "  clean-pyc         Remove Python bytecode and cache"
	@echo "  clean-build       Remove build and dist directories"
	@echo "  clean-test        Remove pytest cache and coverage"
	@echo "  clean-all         Deep clean everything"
	@echo ""
	@echo "Development targets:"
	@echo "  install           Install package"
	@echo "  dev-install       Install in editable mode with dev dependencies"
	@echo "  test              Run pytest"
	@echo "  test-cov          Run pytest with coverage reports"
	@echo "  coverage-report   Display coverage metrics"
	@echo "  lint              Run ruff checks and formatting"
	@echo "  format            Auto-format code with ruff"
	@echo "  typecheck         Run mypy type checking"
	@echo "  security          Run bandit security checks"
	@echo "  check             Run all checks (lint, typecheck, security, test)"
	@echo ""
	@echo "Build & Release targets:"
	@echo "  build             Build the project (creates dist/ artifacts)"
	@echo "  version           Display current version"
	@echo "  bump-patch        Increment patch version (0.0.X)"
	@echo "  bump-minor        Increment minor version (0.X.0)"
	@echo "  bump-major        Increment major version (X.0.0)"
	@echo "  publish           Create tag and trigger GitHub Actions release"
	@echo "  publish-test      Upload to TestPyPI"
	@echo "  publish-manual    Manual PyPI upload with PYPI_TOKEN"
	@echo "  release           Alias for publish"

# Clean targets
clean: clean-pyc clean-build clean-test

clean-pyc:
	@echo "Cleaning Python bytecode and cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

clean-build:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	rm -rf .eggs/

clean-test:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

clean-all: clean
	@echo "Deep cleaning..."
	rm -rf venv/
	rm -rf .venv/

# Development targets
install:
ifdef UV
	@echo "Installing with uv..."
	uv pip install .
else
	@echo "Installing with pip..."
	pip install .
endif

dev-install:
ifdef UV
	@echo "Installing in editable mode with dev dependencies (using uv)..."
	uv pip install -e ".[dev]"
else
	@echo "Installing in editable mode with dev dependencies (using pip)..."
	pip install -e ".[dev]"
endif

test:
ifdef UV
	@echo "Running tests with uv..."
	uv run pytest
else
	@echo "Running tests..."
	pytest
endif

test-cov:
ifdef UV
	@echo "Running tests with coverage (using uv)..."
	uv run pytest --cov=src/chuk_virtual_expert_myexpert --cov-report=html --cov-report=term-missing
else
	@echo "Running tests with coverage..."
	pytest --cov=chuk_virtual_expert_myexpert --cov-report=html --cov-report=term-missing
endif

coverage-report:
	@echo "Coverage report:"
ifdef UV
	uv run coverage report
else
	coverage report
endif

lint:
	@echo "Running ruff checks..."
	ruff check src/ tests/
	@echo "Checking formatting..."
	ruff format --check src/ tests/

format:
	@echo "Formatting code with ruff..."
	ruff format src/ tests/
	@echo "Fixing linting issues..."
	ruff check --fix src/ tests/

typecheck:
	@echo "Running mypy type checking..."
ifdef UV
	uv run mypy src/
else
	mypy src/
endif

security:
	@echo "Running bandit security checks..."
ifdef UV
	uv run bandit -r src/ -ll
else
	bandit -r src/ -ll
endif

check: lint typecheck security test
	@echo "All checks passed!"

# Build target
build: clean-build
	@echo "Building project..."
ifdef UV
	uv build
else
	python3 -m build
endif
	@echo "Build complete. Distributions are in the 'dist' folder."

# Version & Release targets
version:
	@echo "Current version:"
	@grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'

bump-patch:
	@echo "Bumping patch version..."
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	IFS='.' read -r major minor patch <<< "$$current"; \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	sed -i.bak "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	rm -f pyproject.toml.bak; \
	echo "Version bumped to $$new_version"

bump-minor:
	@echo "Bumping minor version..."
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	IFS='.' read -r major minor patch <<< "$$current"; \
	new_minor=$$((minor + 1)); \
	new_version="$$major.$$new_minor.0"; \
	sed -i.bak "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	rm -f pyproject.toml.bak; \
	echo "Version bumped to $$new_version"

bump-major:
	@echo "Bumping major version..."
	@current=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	IFS='.' read -r major minor patch <<< "$$current"; \
	new_major=$$((major + 1)); \
	new_version="$$new_major.0.0"; \
	sed -i.bak "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	rm -f pyproject.toml.bak; \
	echo "Version bumped to $$new_version"

publish:
	@echo "Creating release..."
	@version=$$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Creating tag v$$version"; \
	git tag -a "v$$version" -m "Release v$$version"; \
	git push origin "v$$version"; \
	echo "Tag created and pushed. GitHub Actions will handle the release."

publish-test: build
	@echo "Publishing to TestPyPI..."
ifdef UV
	uv run twine upload --repository testpypi dist/*
else
	python3 -m twine upload --repository testpypi dist/*
endif

publish-manual: build
	@echo "Manual PyPI Publishing"
ifdef UV
	uv run twine upload dist/*
else
	python3 -m twine upload dist/*
endif

release: publish
```

---

## Step 8: Write README

Create a comprehensive README with:

1. Badges (CI, PyPI, Coverage, License)
2. Overview and features
3. Installation instructions
4. Quick start examples
5. API reference
6. Development instructions

See the `chuk-virtual-expert-time` README for a complete example.

**Key Sections:**

```markdown
# chuk-virtual-expert-myexpert

My domain-specific virtual expert for LLM routing.

[![CI](https://github.com/yourname/virtual-experts/actions/workflows/ci-myexpert.yml/badge.svg)](...)
[![PyPI version](https://badge.fury.io/py/chuk-virtual-expert-myexpert.svg)](...)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](...)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](...)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](...)

## Overview

**Features:**
- **Async-native** - Built for async/await patterns
- **Pydantic-native** - Type-safe with structured responses
- **No magic strings** - Uses enums throughout

## Installation

\```bash
pip install chuk-virtual-expert-myexpert
\```

## Quick Start

\```python
from chuk_virtual_expert_myexpert import MyExpert, MyOperation

expert = MyExpert()

# Sync execution
result = expert.execute_operation(
    MyOperation.DO_THING.value,
    {"param1": "test"}
)

# Async execution
result = await expert.execute_operation_async(
    MyOperation.DO_THING.value,
    {"param1": "test"}
)
\```

## Development

\```bash
make dev-install  # Install with dev dependencies
make test         # Run tests
make test-cov     # Run tests with coverage
make check        # Run all checks
make build        # Build package
\```
```

---

## Step 9: GitHub Actions CI/CD

### CI Workflow

Create `.github/workflows/ci-myexpert.yml`:

```yaml
name: CI - MyExpert

on:
  push:
    branches: [main]
    paths:
      - 'packages/chuk-virtual-expert-myexpert/**'
      - '.github/workflows/ci-myexpert.yml'
  pull_request:
    branches: [main]
    paths:
      - 'packages/chuk-virtual-expert-myexpert/**'
      - '.github/workflows/ci-myexpert.yml'
  workflow_dispatch:

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd ../..
          uv sync --all-packages

      - name: Run ruff check
        run: uv run ruff check src/ tests/

      - name: Run ruff format check
        run: uv run ruff format --check src/ tests/

  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd ../..
          uv sync --all-packages

      - name: Run mypy
        run: uv run mypy src/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd ../..
          uv sync --all-packages

      - name: Run bandit
        run: uv run bandit -r src/ -ll

  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          cd ../..
          uv sync --all-packages

      - name: Run tests with coverage
        run: |
          cd ../..
          uv run python -m pytest packages/chuk-virtual-expert-myexpert/tests/ \
            --cov=packages/chuk-virtual-expert-myexpert/src/chuk_virtual_expert_myexpert \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=90

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: myexpert
          fail_ci_if_error: false

  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, typecheck, security, test]
    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: uv pip install --system build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-myexpert
          path: packages/chuk-virtual-expert-myexpert/dist/
```

### Publish Workflow

Create `.github/workflows/publish-myexpert.yml`:

```yaml
name: Publish - MyExpert

on:
  push:
    tags:
      - 'myexpert-v*'
  workflow_dispatch:
    inputs:
      target:
        description: 'Publish target'
        required: true
        default: 'testpypi'
        type: choice
        options:
          - testpypi
          - pypi

jobs:
  publish:
    name: Publish to ${{ github.event.inputs.target || 'pypi' }}
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/chuk-virtual-expert-myexpert

    permissions:
      id-token: write  # For trusted publishing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to TestPyPI
        if: github.event.inputs.target == 'testpypi'
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          packages-dir: packages/chuk-virtual-expert-myexpert/dist/

      - name: Publish to PyPI
        if: github.event.inputs.target == 'pypi' || startsWith(github.ref, 'refs/tags/')
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: packages/chuk-virtual-expert-myexpert/dist/
```

---

## Step 10: Publishing

### Initial Setup

1. Create accounts on [PyPI](https://pypi.org) and [TestPyPI](https://test.pypi.org)
2. Configure trusted publishing in PyPI project settings
3. Add repository secrets if using manual token-based publishing

### Publishing Flow

```bash
# 1. Run all checks
make check

# 2. Bump version
make bump-patch  # or bump-minor, bump-major

# 3. Commit and push
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git push

# 4. Create release tag (triggers GitHub Actions)
make publish

# Or publish manually
make publish-test  # TestPyPI
make publish-manual  # PyPI
```

---

## Best Practices Checklist

### Code Quality

- [ ] All string constants use enums (no magic strings)
- [ ] Type hints on all functions
- [ ] Docstrings on all public methods
- [ ] ClassVar for class-level attributes
- [ ] Pydantic BaseModel or dataclass for data structures

### Testing

- [ ] 90%+ coverage for each file
- [ ] Tests for all enum values
- [ ] Tests for all operations
- [ ] Tests for error handling
- [ ] Tests for async methods
- [ ] Tests for package exports
- [ ] Tests for edge cases

### Documentation

- [ ] README with badges
- [ ] Installation instructions
- [ ] Quick start examples
- [ ] API reference
- [ ] Development instructions

### CI/CD

- [ ] Linting (ruff)
- [ ] Type checking (mypy)
- [ ] Security scanning (bandit)
- [ ] Tests with coverage
- [ ] Multi-Python version testing (3.11, 3.12)
- [ ] Package build verification
- [ ] Automated publishing

### Package Structure

- [ ] src layout
- [ ] Proper __init__.py exports
- [ ] __all__ defined
- [ ] __version__ defined
- [ ] Entry point registered
- [ ] LICENSE file
- [ ] pyproject.toml complete

---

## Reference: Time Expert

The Time Expert (`chuk-virtual-expert-time`) is the reference implementation:

- **Location:** `packages/chuk-virtual-expert-time/`
- **Type:** MCPExpert (delegates to MCP server)
- **Coverage:** 100%
- **Tests:** 42 passing
- **Features:** Async-native, Pydantic-native, no magic strings

Study its structure as a template for new experts.
