# chuk-virtual-expert

Base specification for virtual expert plugins - async-native, Pydantic-native with CoT dispatch.

[![CI](https://github.com/chrishayuk/virtual-experts/actions/workflows/ci-virtual-expert.yml/badge.svg)](https://github.com/chrishayuk/virtual-experts/actions/workflows/ci-virtual-expert.yml)
[![PyPI version](https://badge.fury.io/py/chuk-virtual-expert.svg)](https://badge.fury.io/py/chuk-virtual-expert)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen.svg)](https://github.com/chrishayuk/virtual-experts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Virtual experts are specialized plugins that language models can route to for domain-specific tasks. This package provides the base infrastructure:

- **VirtualExpert** - Pydantic base class for implementing experts
- **MCPExpert** - Base class for MCP-backed experts (optional)
- **VirtualExpertAction** - Structured action format for CoT dispatch
- **ExpertRegistry** - Registration and lookup of experts
- **Dispatcher** - CoT-based routing to experts
- **LazarusAdapter** - Bridge to Lazarus MoE routing
- **FewShotValidator** - Validation framework for testing few-shot prompts

## Features

- **Async-only** - All experts use `async def execute_operation()` and `async def execute()`
- **Pydantic-native** - Type-safe models with validation throughout
- **No magic strings** - Enum-based operations and constants
- **Typed traces** - Discriminated union step models for trace execution
- **MCP support** - Optional base class for Model Context Protocol backends
- **Validation framework** - Test few-shot prompts before fine-tuning

## Architecture

```
User Query (any phrasing)
    ↓
CoT Rewrite (LLM-based extraction)
    ↓
VirtualExpertAction JSON
    ↓
Calibration Router (trained on action JSONs)
    ↓
await expert.execute(action)
    ↓
VirtualExpertResult (structured data)
```

## Installation

```bash
pip install chuk-virtual-expert
```

With MCP support (for MCPExpert base class):
```bash
pip install chuk-virtual-expert[mcp]
```

With Lazarus integration:
```bash
pip install chuk-virtual-expert[lazarus]
```

For development:
```bash
pip install chuk-virtual-expert[dev]
```

## Quick Start

### Creating a Virtual Expert

```python
from typing import Any, ClassVar
from chuk_virtual_expert import VirtualExpert, VirtualExpertAction

class WeatherExpert(VirtualExpert):
    """Expert for weather queries."""

    name: ClassVar[str] = "weather"
    description: ClassVar[str] = "Get weather forecasts and conditions"
    priority: ClassVar[int] = 5

    def can_handle(self, prompt: str) -> bool:
        """Check if this expert can handle the prompt."""
        keywords = ["weather", "temperature", "forecast", "rain", "sunny"]
        return any(kw in prompt.lower() for kw in keywords)

    def get_operations(self) -> list[str]:
        return ["get_weather", "get_forecast"]

    async def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute operation (async-only)."""
        if operation == "get_weather":
            location = parameters.get("location", "Unknown")
            return {
                "location": location,
                "temperature": 72,
                "condition": "sunny",
            }
        elif operation == "get_forecast":
            return {"forecast": "Sunny all week"}
        else:
            raise ValueError(f"Unknown operation: {operation}")
```

### Execution

```python
import asyncio
from chuk_virtual_expert import VirtualExpertAction

async def main():
    expert = WeatherExpert()

    # Operation execution (async-only)
    result = await expert.execute_operation(
        "get_weather",
        {"location": "Tokyo"}
    )
    print(result)  # {"location": "Tokyo", "temperature": 72, ...}

    # Action execution (async-only)
    action = VirtualExpertAction(
        expert="weather",
        operation="get_weather",
        parameters={"location": "Paris"},
    )
    result = await expert.execute(action)
    print(result.data)  # {"location": "Paris", ...}

asyncio.run(main())
```

### Using the Registry

```python
from chuk_virtual_expert import ExpertRegistry

registry = ExpertRegistry()
registry.register(WeatherExpert())

# Get expert by name
expert = registry.get("weather")

# Get all experts (sorted by priority)
all_experts = registry.get_all()

# Check if expert exists
if "weather" in registry:
    print("Weather expert is available")
```

### Executing Actions

```python
from chuk_virtual_expert import VirtualExpertAction

# Create an action
action = VirtualExpertAction(
    expert="weather",
    operation="get_weather",
    parameters={"location": "Tokyo"},
    confidence=0.95,
    reasoning="User asking for weather in Tokyo",
)

# Execute on expert (async-only)
expert = registry.get("weather")
result = await expert.execute(action)

print(result.data)  # {"location": "Tokyo", "temperature": 72, ...}
print(result.success)  # True
```

### Creating an MCP-Backed Expert

For experts that call remote MCP servers:

```python
from typing import Any, ClassVar
from chuk_virtual_expert import MCPExpert

class TimeExpert(MCPExpert):
    """Time expert backed by MCP server."""

    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Time and timezone operations"
    mcp_server_url: ClassVar[str] = "https://time.example.com/mcp"
    mcp_timeout: ClassVar[float] = 30.0

    def can_handle(self, prompt: str) -> bool:
        return any(kw in prompt.lower() for kw in ["time", "timezone", "clock"])

    def get_operations(self) -> list[str]:
        return ["get_time", "convert_time"]

    def get_mcp_tool_name(self, operation: str) -> str:
        """Map operation to MCP tool name."""
        mapping = {
            "get_time": "get_local_time",
            "convert_time": "convert_time",
        }
        return mapping[operation]

    def transform_parameters(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Transform parameters for MCP tool."""
        return parameters  # Pass through or transform as needed

    def transform_result(
        self, operation: str, tool_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Transform MCP result to expert format."""
        return {"query_type": operation, **tool_result}
```

### Using the Dispatcher

```python
from chuk_virtual_expert import Dispatcher, FewShotExtractor

# Create dispatcher with registry
dispatcher = Dispatcher(registry=registry)

# Set up LLM-based action extraction
extractor = FewShotExtractor(
    experts={"weather": WeatherExpert()},
    max_examples_per_expert=3,
)

# Use with your LLM
class MyLLMExtractor:
    def extract(self, query: str, available_experts: list[str]) -> VirtualExpertAction:
        # Use extractor.get_prompt(query) and call your LLM
        prompt = extractor.get_prompt(query)
        response = my_llm.generate(prompt)
        return extractor.parse_response(response)

dispatcher.set_extractor(MyLLMExtractor())

# Dispatch a query
result = dispatcher.dispatch("What's the weather in Tokyo?")
print(result.action.expert)  # "weather"
print(result.result.data)  # Weather data
```

### Validating Few-Shot Prompts

Before investing in fine-tuning, validate that your expert works with few-shot prompting:

```python
from chuk_virtual_expert import FewShotValidator, validate_expert_few_shot

expert = WeatherExpert()

def my_generate(prompt: str, max_tokens: int) -> str:
    """Your LLM generation function."""
    return my_llm.generate(prompt, max_tokens=max_tokens)

# Quick validation
summary = validate_expert_few_shot(
    expert=expert,
    generate_fn=my_generate,
    test_queries=["What's the weather in Tokyo?", "Get forecast for NYC"],
    expected_answers=[{"temperature": 72}, {"forecast": "Sunny"}],
)

summary.print_summary()
# Shows: parse rate, route rate, execution rate, accuracy
# Plus guidance on whether to fine-tune or if few-shot is sufficient

# Detailed validation
validator = FewShotValidator(expert, my_generate, verbose=True)
result = validator.validate_single("What's the weather?", expected_answer=72)
print(result.parsed)  # True/False
print(result.routed_to_expert)  # True/False
print(result.correct)  # True/False
```

### Integration with Lazarus

```python
from chuk_virtual_expert import LazarusAdapter, adapt_expert

# Create adapter for Lazarus
expert = WeatherExpert()
adapter = LazarusAdapter(expert)

# Or use the helper function
adapter = adapt_expert(expert)

# The adapter provides Lazarus-compatible interface
adapter.name  # "weather"
adapter.can_handle("What's the weather?")  # True
await adapter.execute("What's the weather in Tokyo?")  # String result
adapter.get_calibration_actions()  # For router training
```

## CoT Examples

Each expert should provide `cot_examples.json` with training data:

```json
{
  "expert_name": "weather",
  "examples": [
    {
      "query": "What's the weather in Tokyo?",
      "action": {
        "expert": "weather",
        "operation": "get_weather",
        "parameters": {"location": "Tokyo"},
        "confidence": 1.0,
        "reasoning": "User asking for current weather"
      }
    },
    {
      "query": "Tell me a joke",
      "action": {
        "expert": "none",
        "operation": "passthrough",
        "parameters": {},
        "confidence": 1.0,
        "reasoning": "Not a weather query"
      }
    }
  ]
}
```

## API Reference

### VirtualExpert

Abstract base class for all virtual experts.

**Class Attributes:**
- `name: ClassVar[str]` - Unique expert identifier
- `description: ClassVar[str]` - Human-readable description
- `version: ClassVar[str]` - Expert version
- `priority: ClassVar[int]` - Routing priority (higher = first)

**Abstract Methods:**
- `can_handle(prompt) -> bool` - Check if expert can handle prompt
- `get_operations() -> list[str]` - Available operation names
- `async execute_operation(operation, parameters) -> dict` - Execute an operation

**Provided Methods:**
- `async execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction
- `get_cot_examples() -> CoTExamples` - Load training examples
- `get_calibration_data() -> tuple[list[str], list[str]]` - Get calibration data
- `get_schema() -> ExpertSchema` - Get expert schema for prompts

### MCPExpert

Base class for MCP-backed experts (requires `chuk-virtual-expert[mcp]`).

**Additional Class Attributes:**
- `mcp_server_url: ClassVar[str]` - MCP server endpoint
- `mcp_timeout: ClassVar[float]` - Request timeout (default: 30.0)
- `mcp_transport_type: ClassVar[MCPTransportType]` - HTTP or STDIO

**Additional Abstract Methods:**
- `get_mcp_tool_name(operation) -> str` - Map operation to MCP tool
- `transform_result(operation, tool_result) -> dict` - Transform MCP result

**Additional Methods:**
- `transform_parameters(operation, parameters) -> dict` - Transform parameters (optional override)
- `list_mcp_tools() -> list[dict]` - List available MCP tools

### VirtualExpertAction

Pydantic model for structured actions.

**Fields:**
- `expert: str` - Expert name or "none" for passthrough
- `operation: str` - Operation to execute
- `parameters: dict[str, Any]` - Operation parameters
- `confidence: float` - Model confidence (0-1)
- `reasoning: str` - CoT reasoning

**Methods:**
- `none_action(reasoning="")` - Create passthrough action
- `is_passthrough()` - Check if action should pass to base model

### VirtualExpertResult

Result from expert execution.

**Fields:**
- `data: dict | None` - Structured result data
- `expert_name: str` - Expert that produced result
- `success: bool` - Whether execution succeeded
- `error: str | None` - Error message if failed
- `action: VirtualExpertAction | None` - The action that was executed

### ExpertRegistry

Registry for managing experts.

**Methods:**
- `register(expert)` - Register an expert
- `unregister(name)` - Remove an expert
- `get(name) -> VirtualExpert | None` - Get expert by name
- `get_all() -> list[VirtualExpert]` - Get all (sorted by priority)
- `expert_names -> list[str]` - List of registered names

### Dispatcher

Routes queries to experts via CoT extraction.

**Methods:**
- `set_extractor(extractor)` - Set LLM-based extractor
- `dispatch(query) -> DispatchResult` - Route a query
- `dispatch_action(action) -> DispatchResult` - Route pre-extracted action

### FewShotValidator

Validates expert few-shot prompting before fine-tuning.

**Methods:**
- `validate_single(query, expected) -> ValidationResult` - Validate one query
- `validate(queries, expected) -> ValidationSummary` - Validate multiple queries

### ValidationSummary

Summary of validation results with guidance.

**Properties:**
- `parse_rate` - Percentage successfully parsed
- `route_rate` - Percentage routed to expert
- `exec_rate` - Percentage executed successfully
- `valid_rate` - Percentage with valid traces
- `accuracy` - Percentage correct

**Methods:**
- `print_summary()` - Print summary with fine-tuning guidance

## Development

```bash
# Clone and install
git clone https://github.com/chrishayuk/virtual-experts
cd virtual-experts/packages/chuk-virtual-expert
make dev-install

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all checks (lint, format, mypy, bandit, tests)
make check

# Format code
make format

# Build package
make build
```

## License

MIT License - see [LICENSE](LICENSE) for details.
