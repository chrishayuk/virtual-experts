# chuk-virtual-expert

Base specification for virtual expert plugins - Pydantic-native with CoT dispatch.

[![PyPI version](https://badge.fury.io/py/chuk-virtual-expert.svg)](https://badge.fury.io/py/chuk-virtual-expert)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Virtual experts are specialized plugins that language models can route to for domain-specific tasks. This package provides the base infrastructure:

- **VirtualExpert** - Pydantic base class for implementing experts
- **VirtualExpertAction** - Structured action format for CoT dispatch
- **ExpertRegistry** - Registration and lookup of experts
- **Dispatcher** - CoT-based routing to experts
- **LazarusAdapter** - Bridge to Lazarus MoE routing

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
Expert.execute(action)
    ↓
VirtualExpertResult (structured data)
```

## Installation

```bash
pip install chuk-virtual-expert
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

    def get_operations(self) -> list[str]:
        return ["get_weather", "get_forecast"]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
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

# Execute on expert
expert = registry.get("weather")
result = expert.execute(action)

print(result.data)  # {"location": "Tokyo", "temperature": 72, ...}
print(result.success)  # True
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
adapter.execute("What's the weather in Tokyo?")  # String result
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
- `get_operations() -> list[str]` - Available operation names
- `execute_operation(operation, parameters) -> dict` - Execute an operation

**Provided Methods:**
- `execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction
- `get_cot_examples() -> CoTExamples` - Load training examples
- `get_calibration_data() -> tuple[list[str], list[str]]` - Get calibration data

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

# Run all checks
make check

# Format code
make format

# Build package
make build
```

## License

MIT License - see [LICENSE](LICENSE) for details.
