# Virtual Experts Mono-repo

Lightweight, standalone virtual expert plugins for language models. Supports both **Lazarus MoE routing** and **Chain-of-Thought (CoT) dispatch** for guaranteed expert invocation.

## Overview

Virtual experts are specialized plugins that language models can route to for domain-specific tasks. Each expert:

- **Returns Structured Data**: Outputs `dict[str, Any]` for model chain-of-thought reasoning
- **Standalone**: Can be deployed and used independently
- **Lightweight**: Minimal dependencies
- **Pluggable**: Works with Lazarus or CoT dispatcher

## Packages

| Package | Description | Status |
|---------|-------------|--------|
| `chuk-virtual-expert` | Base specification, registry, and CoT dispatcher | ✅ |
| `chuk-virtual-expert-time` | Time and timezone operations | ✅ |
| `chuk-virtual-expert-weather` | Weather forecasts (planned) | 🔜 |
| `chuk-virtual-expert-celestial` | Astronomy calculations (planned) | 🔜 |
| `chuk-virtual-expert-solver` | Math/equation solving (planned) | 🔜 |

## Documentation

- **[Creating Virtual Experts Guide](docs/CREATING_VIRTUAL_EXPERTS.md)** - Complete guide to creating production-ready virtual experts with MCP, testing, CI/CD, and publishing

## Routing Architecture

### The Problem with Direct Routing

Direct query routing has issues:
- "What time is it in Tokyo?" might route differently than "Tokyo time?"
- Calibration must cover all possible phrasings
- Edge cases slip through threshold gaps

### The Solution: CoT Rewrite + Calibration

We use **both** approaches in sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│  User Query (any phrasing)                                      │
│  "What time is it in Tokyo?"                                    │
│  "Tokyo time please"                                            │
│  "I need the current time in Japan"                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CoT Rewrite (LLM normalizes to consistent format)              │
│                                                                 │
│  → {"expert": "time", "operation": "get_time",                  │
│     "parameters": {"timezone": "Asia/Tokyo"}}                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Calibration Router (trained on normalized format)              │
│                                                                 │
│  Input is now CONSISTENT regardless of original phrasing        │
│  → High confidence routing to time expert                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Virtual Expert Execution                                       │
│                                                                 │
│  time.get_time(timezone="Asia/Tokyo")                           │
│  → {"iso8601": "2026-01-20T08:46:09+09:00", ...}                │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Works

1. **CoT Rewrite**: Normalizes infinite query variations into a small set of structured actions
2. **Calibration**: Only needs to learn routing for the normalized format (much smaller space)
3. **Result**: Reliable routing regardless of how the user phrases their query

### Calibration on Normalized Format

Instead of calibrating on raw queries:
```python
# OLD: Calibrate on raw queries (brittle)
positive = ["What time is it?", "Current time", "Time please", ...]
negative = ["What is 2+2?", "Tell me a joke", ...]
```

Calibrate on the normalized VirtualExpertAction format:
```python
# NEW: Calibrate on normalized actions (robust)
positive = [
    '{"expert": "time", "operation": "get_time", "parameters": {}}',
    '{"expert": "time", "operation": "get_time", "parameters": {"timezone": "Asia/Tokyo"}}',
    '{"expert": "time", "operation": "convert_time", "parameters": {"time": "3pm", ...}}',
]
negative = [
    '{"expert": "none", "operation": "passthrough", "parameters": {}}',
    '{"expert": "math", "operation": "calculate", "parameters": {...}}',
]
```

The calibration space is now **deterministic** - same action format always routes the same way.

## Quick Start

### Install

```bash
pip install chuk-virtual-expert-time
```

### Using the Clean API (Pydantic-native)

```python
from chuk_virtual_expert_time import TimeExpert, TimeOperation
from chuk_virtual_expert import VirtualExpertAction

# Create expert
expert = TimeExpert()

# Direct method calls
result = expert.get_time(timezone="Asia/Tokyo")
print(result)
# {'query_type': 'current_time', 'timezone': 'Asia/Tokyo',
#  'iso8601': '2026-01-20T08:46:09+09:00', 'formatted': '2026-01-20 08:46:09 JST', ...}

result = expert.convert_time(time="3pm", from_timezone="EST", to_timezone="PST")
print(result)
# {'query_type': 'conversion', 'from_time': '03:00 PM', 'to_time': '12:00 PM', ...}

# Via VirtualExpertAction (what CoT produces)
action = VirtualExpertAction(
    expert="time",
    operation="get_time",
    parameters={"timezone": "Asia/Tokyo"},
    confidence=0.95,
    reasoning="User asking for time in Tokyo"
)
result = expert.execute(action)
print(result.data)  # Structured result
print(result.success)  # True
```

## CoT Dispatch

The CoT dispatcher normalizes any query phrasing into a structured action:

```python
from chuk_virtual_expert import VirtualExpertRegistry, VirtualExpertDispatcher
from chuk_virtual_expert.dispatcher import VirtualExpertAction
from chuk_virtual_expert_time import TimeExpertPlugin

# Setup
registry = VirtualExpertRegistry()
registry.register(TimeExpertPlugin(use_mcp=False))
dispatcher = VirtualExpertDispatcher(registry)

# With an LLM extractor, these all produce the same structured action:
#   "What time is it in Tokyo?"
#   "Tokyo time please"
#   "I need to know the current time in Japan"
#   "時間は?" (with context)
#
# All → VirtualExpertAction(expert="time", operation="get_time",
#                           parameters={"timezone": "Asia/Tokyo"})
```

### VirtualExpertAction Format

```python
@dataclass
class VirtualExpertAction:
    expert: str           # "time", "weather", or "none"
    operation: str        # "get_time", "convert_time", etc.
    parameters: dict      # {"timezone": "Asia/Tokyo"}
    confidence: float     # 0.0 - 1.0
    reasoning: str        # "User asking for time in Tokyo"
```

### LLM Extraction Example

```python
from mlx_lm import load, generate
from chuk_virtual_expert.dispatcher import PromptBasedExtractor

# Load model
model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")

# Get extraction prompt
extractor = PromptBasedExtractor(registry)
prompt = extractor.get_prompt("What time is it in Tokyo?")

# LLM produces structured JSON
response = generate(model, tokenizer, prompt=prompt, max_tokens=200)
# {"expert": "time", "operation": "get_time",
#  "parameters": {"timezone": "Asia/Tokyo"}, "confidence": 0.9, ...}

# Parse into action
action = extractor.parse_response(response)
```

### End-to-End Results

| User Query | CoT Rewrite Output | Expert Result |
|------------|-------------------|---------------|
| "What time is it?" | `{"expert": "time", "operation": "get_time", "parameters": {}}` | `{"timezone": "UTC", "formatted": "2026-01-19 23:46:08"}` |
| "What time is it in Tokyo?" | `{"expert": "time", "operation": "get_time", "parameters": {"timezone": "Asia/Tokyo"}}` | `{"timezone": "Asia/Tokyo", "formatted": "2026-01-20 08:46:09 JST"}` |
| "Convert 3pm EST to PST" | `{"expert": "time", "operation": "convert_time", "parameters": {"time": "3pm", "from_timezone": "EST", "to_timezone": "PST"}}` | `{"from_time": "03:00 PM", "to_time": "12:00 PM"}` |
| "What timezone is Sydney in?" | `{"expert": "time", "operation": "get_timezone_info", "parameters": {"location": "sydney"}}` | `{"iana_timezone": "Australia/Sydney"}` |
| "Tell me a joke" | `{"expert": "none", "operation": "passthrough", "parameters": {}}` | *passes to base model* |

## Lazarus Integration

```python
from chuk_lazarus.inference.virtual_experts import VirtualDenseWrapper, VirtualExpertRegistry
from chuk_virtual_expert_time import TimeExpertPlugin
from chuk_virtual_expert import adapt_for_lazarus

# Create and adapt plugin (converts dict→str for Lazarus)
time_plugin = TimeExpertPlugin(use_mcp=False)
lazarus_plugin = adapt_for_lazarus(time_plugin)

# Register with Lazarus
registry = VirtualExpertRegistry()
registry.register(lazarus_plugin)

# Create wrapper
wrapper = VirtualDenseWrapper(model, tokenizer, model_id="...",
                               registry=registry, routing_threshold=0.2)
wrapper.calibrate()

# Use
result = wrapper.solve("What time is it?")
print(result.answer)  # "2026-01-19 23:43:43 (UTC)"
print(result.used_virtual_expert)  # True
```

## Creating a Virtual Expert

### 1. Define Operations Enum

```python
# my_expert/expert.py
from enum import Enum
from typing import Any, ClassVar
from pydantic import Field
from chuk_virtual_expert import VirtualExpert

class MyOperation(str, Enum):
    """Operations for this expert."""
    DO_THING = "do_thing"
    DO_OTHER = "do_other"

class MyQueryType(str, Enum):
    """Result types."""
    THING_RESULT = "thing_result"
    ERROR = "error"
```

### 2. Implement Expert Class

```python
class MyExpert(VirtualExpert):
    """My domain-specific expert."""

    # Class configuration
    name: ClassVar[str] = "my_expert"
    description: ClassVar[str] = "Does something specific"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 5

    # File paths (relative to module)
    cot_examples_file: ClassVar[str] = "cot_examples.json"
    schema_file: ClassVar[str] = "schema.json"

    # Instance config (Pydantic fields)
    some_option: bool = Field(default=False)

    def get_operations(self) -> list[str]:
        """List available operations."""
        return [op.value for op in MyOperation]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute operation by name."""
        op = MyOperation(operation)

        if op == MyOperation.DO_THING:
            return self.do_thing(**parameters)
        elif op == MyOperation.DO_OTHER:
            return self.do_other(**parameters)
        else:
            return {"query_type": MyQueryType.ERROR, "error": f"Unknown: {operation}"}

    def do_thing(self, param1: str, param2: int = 10) -> dict[str, Any]:
        """Actual operation implementation."""
        return {
            "query_type": MyQueryType.THING_RESULT,
            "result": f"Did thing with {param1}",
            "count": param2,
        }
```

### 3. CoT Examples File (cot_examples.json)

```json
{
  "expert_name": "my_expert",
  "examples": [
    {
      "query": "Do the thing with foo",
      "action": {
        "expert": "my_expert",
        "operation": "do_thing",
        "parameters": {"param1": "foo"},
        "confidence": 1.0,
        "reasoning": "User wants to do the thing with foo"
      }
    },
    {
      "query": "Tell me a joke",
      "action": {
        "expert": "none",
        "operation": "passthrough",
        "parameters": {},
        "confidence": 1.0,
        "reasoning": "Not related to my_expert"
      }
    }
  ]
}
```

### 4. Schema File (schema.json)

```json
{
  "name": "my_expert",
  "description": "Does something specific",
  "operations": {
    "do_thing": {
      "description": "Does the thing",
      "parameters": {
        "param1": {"type": "string", "description": "What to do", "required": true},
        "param2": {"type": "integer", "description": "How many times", "default": 10}
      }
    }
  }
}
```

### 5. Package Structure

```
my-virtual-expert/
├── pyproject.toml
└── src/my_virtual_expert/
    ├── __init__.py
    ├── expert.py          # Expert class with enums
    ├── cot_examples.json  # Query → action mappings for training
    └── schema.json        # Operation schema
```

### 6. pyproject.toml

```toml
[project]
name = "my-virtual-expert"
dependencies = ["chuk-virtual-expert>=2.0"]

[project.entry-points."chuk_virtual_expert.experts"]
my_expert = "my_virtual_expert:MyExpert"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Query (any phrasing)                     │
│         "What time is it in Tokyo?" / "Tokyo time?"              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CoT Rewrite (LLM)                           │
│                                                                  │
│  Normalizes query → VirtualExpertAction                          │
│  {"expert": "time", "operation": "get_time",                     │
│   "parameters": {"timezone": "Asia/Tokyo"}}                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Calibration Router (Lazarus)                        │
│                                                                  │
│  Trained on normalized action format                             │
│  Activations → Routing direction → Expert selection              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  VirtualExpertRegistry                           │
│         ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│         │  Time   │  │ Weather │  │ Solver  │                   │
│         │ Expert  │  │ Expert  │  │ Expert  │                   │
│         └────┬────┘  └────┬────┘  └────┬────┘                   │
└──────────────┼────────────┼────────────┼────────────────────────┘
               │            │            │
               ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Structured Results (dict)                       │
│                                                                  │
│  {"query_type": "current_time", "timezone": "Asia/Tokyo",        │
│   "iso8601": "2026-01-20T08:46:09+09:00", ...}                   │
└─────────────────────────────────────────────────────────────────┘
```

## API Reference

### VirtualExpert (Pydantic BaseModel)

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | ClassVar[str] | Unique identifier |
| `description` | ClassVar[str] | Human-readable description |
| `version` | ClassVar[str] | Expert version |
| `priority` | ClassVar[int] | Routing priority (higher = first) |
| `cot_examples_file` | ClassVar[str] | Path to cot_examples.json |
| `schema_file` | ClassVar[str] | Path to schema.json |

| Method | Returns | Description |
|--------|---------|-------------|
| `get_operations()` | list[str] | Available operation names |
| `execute_operation(op, params)` | dict | Execute named operation |
| `execute(action)` | VirtualExpertResult | Execute VirtualExpertAction |
| `get_cot_examples()` | CoTExamples | Load CoT training examples |
| `get_calibration_data()` | tuple[list, list] | (positive, negative) for training |
| `get_few_shot_prompt(n)` | str | Few-shot examples for prompt |

### VirtualExpertAction (Pydantic BaseModel)

| Field | Type | Description |
|-------|------|-------------|
| `expert` | str | Expert name or "none" |
| `operation` | str | Operation to call |
| `parameters` | dict[str, Any] | Extracted parameters |
| `confidence` | float | 0.0 - 1.0 |
| `reasoning` | str | CoT reasoning |

| Method | Returns | Description |
|--------|---------|-------------|
| `none_action(reasoning)` | VirtualExpertAction | Create passthrough action |
| `is_passthrough()` | bool | Check if should pass to base model |

### VirtualExpertResult (Pydantic BaseModel)

| Field | Type | Description |
|-------|------|-------------|
| `data` | dict \| None | Structured result data |
| `expert_name` | str | Expert that produced result |
| `success` | bool | Whether execution succeeded |
| `error` | str \| None | Error message if failed |
| `action` | VirtualExpertAction \| None | Action that was executed |

### Dispatcher (Pydantic BaseModel)

| Method | Description |
|--------|-------------|
| `dispatch(query)` | Extract action via CoT and execute |
| `dispatch_action(action)` | Execute pre-extracted action |
| `set_extractor(extractor)` | Set LLM-based action extractor |

### ExpertRegistry (Pydantic BaseModel)

| Method | Description |
|--------|-------------|
| `register(expert)` | Register an expert |
| `get(name)` | Get expert by name |
| `get_all()` | Get all experts (sorted by priority) |
| `expert_names` | List of registered names |

## Development

```bash
# Setup
cd virtual-experts
uv sync

# Run examples
uv run --package chuk-virtual-expert-time python examples/cot_dispatch_demo.py
uv run --package chuk-virtual-expert-time python examples/cot_llm_demo.py
uv run --package chuk-virtual-expert-time python examples/lazarus_integration.py --model mlx-community/Qwen2.5-0.5B-Instruct-4bit

# Run tests
uv run pytest packages/chuk-virtual-expert-time/tests/
```

## License

MIT
