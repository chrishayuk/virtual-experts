# chuk-virtual-expert-time

Time virtual expert - accurate time and timezone operations for LLM routing.

[![PyPI version](https://badge.fury.io/py/chuk-virtual-expert-time.svg)](https://badge.fury.io/py/chuk-virtual-expert-time)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A virtual expert plugin that provides accurate time and timezone operations for LLM routing systems. Works with Lazarus MoE models or as a standalone expert.

**Features:**
- **Current time** - Get UTC or local time for any timezone
- **Timezone conversion** - Convert times between IANA timezones
- **Timezone info** - Look up timezone details for locations
- **20+ timezone aliases** - Common cities and abbreviations
- **Pydantic-native** - Type-safe with structured responses
- **CoT training data** - Ready for few-shot prompting and calibration

## Installation

```bash
pip install chuk-virtual-expert-time
```

With MCP server support (NTP consensus accuracy):
```bash
pip install chuk-virtual-expert-time[mcp]
```

For development:
```bash
pip install chuk-virtual-expert-time[dev]
```

## Quick Start

### Direct Usage

```python
from chuk_virtual_expert_time import TimeExpert
from chuk_virtual_expert import VirtualExpertAction

# Create expert
expert = TimeExpert()

# Get current UTC time
action = VirtualExpertAction(
    expert="time",
    operation="get_time",
    parameters={},
)
result = expert.execute(action)
print(result.data)
# {'query_type': 'current_time', 'timezone': 'UTC', 'iso8601': '2024-01-15T12:00:00+00:00', ...}

# Get time in Tokyo
action = VirtualExpertAction(
    expert="time",
    operation="get_time",
    parameters={"timezone": "Asia/Tokyo"},
)
result = expert.execute(action)
print(result.data["formatted"])  # "2024-01-15 21:00:00 JST"

# Convert time between zones
action = VirtualExpertAction(
    expert="time",
    operation="convert_time",
    parameters={
        "time": "3pm",
        "from_timezone": "EST",
        "to_timezone": "PST",
    },
)
result = expert.execute(action)
print(f"{result.data['from_time']} EST = {result.data['to_time']} PST")
```

### With Lazarus

```python
from chuk_lazarus.inference.virtual_experts import (
    VirtualDenseWrapper,
    FewShotCoTRewriter,
)
from chuk_virtual_expert import LazarusAdapter
from chuk_virtual_expert_time import TimeExpert

# Load your model
from mlx_lm import load
model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")

# Create CoT rewriter and wrapper
rewriter = FewShotCoTRewriter(model, tokenizer, max_examples_per_expert=10)
wrapper = VirtualDenseWrapper(
    model=model,
    tokenizer=tokenizer,
    model_id="Qwen2.5-0.5B",
    cot_rewriter=rewriter,
    routing_threshold=0.1,
)

# Register time expert
expert = TimeExpert()
adapter = LazarusAdapter(expert)
rewriter.set_expert_info(
    expert_name=adapter.name,
    description=adapter.description,
    examples=adapter.get_cot_examples(),
)
wrapper.register_plugin(adapter)
wrapper.calibrate(use_cot=True)

# Use it
result = wrapper.solve("What time is it in Tokyo?")
print(result.answer)  # "2024-01-15 21:00:00 JST (Asia/Tokyo)"
```

## Operations

### get_time

Get current time in a timezone.

**Parameters:**
- `timezone` (optional): IANA timezone or alias. Default: "UTC"

**Returns:**
```python
{
    "query_type": "current_time",
    "timezone": "Asia/Tokyo",
    "iana_timezone": "Asia/Tokyo",
    "iso8601": "2024-01-15T21:00:00+09:00",
    "formatted": "2024-01-15 21:00:00 JST",
    "epoch_ms": 1705320000000,
    "utc_offset": "+0900",
}
```

### convert_time

Convert time between timezones.

**Parameters:**
- `time`: Time string (e.g., "3pm", "15:00", "3:30 PM")
- `from_timezone`: Source timezone
- `to_timezone`: Target timezone

**Returns:**
```python
{
    "query_type": "conversion",
    "from_timezone": "America/New_York",
    "to_timezone": "America/Los_Angeles",
    "from_time": "03:00 PM",
    "to_time": "12:00 PM",
    "from_iso8601": "2024-01-15T15:00:00-05:00",
    "to_iso8601": "2024-01-15T12:00:00-08:00",
}
```

### get_timezone_info

Get timezone information for a location.

**Parameters:**
- `location`: Location name

**Returns:**
```python
{
    "query_type": "timezone_info",
    "location": "Tokyo",
    "iana_timezone": "Asia/Tokyo",
}
```

## Timezone Aliases

Common location names and abbreviations are automatically resolved:

| Alias | IANA Timezone |
|-------|---------------|
| tokyo | Asia/Tokyo |
| london | Europe/London |
| new york, nyc | America/New_York |
| la, los angeles | America/Los_Angeles |
| paris | Europe/Paris |
| sydney | Australia/Sydney |
| berlin | Europe/Berlin |
| moscow | Europe/Moscow |
| beijing, shanghai | Asia/Shanghai |
| singapore | Asia/Singapore |
| dubai | Asia/Dubai |
| mumbai | Asia/Kolkata |
| EST | America/New_York |
| PST | America/Los_Angeles |
| CST | America/Chicago |
| MST | America/Denver |
| GMT | Europe/London |
| CET | Europe/Paris |
| JST | Asia/Tokyo |
| UTC | UTC |

## CoT Training Examples

The package includes `cot_examples.json` with 20 training examples:

```json
{
  "expert_name": "time",
  "examples": [
    {
      "query": "What time is it in Tokyo?",
      "action": {
        "expert": "time",
        "operation": "get_time",
        "parameters": {"timezone": "Asia/Tokyo"},
        "confidence": 1.0,
        "reasoning": "User asking for current time in Tokyo"
      }
    },
    {
      "query": "Convert 3pm EST to PST",
      "action": {
        "expert": "time",
        "operation": "convert_time",
        "parameters": {
          "time": "3pm",
          "from_timezone": "America/New_York",
          "to_timezone": "America/Los_Angeles"
        },
        "confidence": 1.0,
        "reasoning": "Time conversion from Eastern to Pacific"
      }
    }
  ]
}
```

## Configuration

```python
expert = TimeExpert(
    use_mcp=True,                    # Use MCP server for NTP accuracy
    mcp_server="chuk-mcp-time",      # MCP server name
)
```

## Development

```bash
# Clone and install
git clone https://github.com/chrishayuk/virtual-experts
cd virtual-experts/packages/chuk-virtual-expert-time
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

## API Reference

### TimeExpert

Main expert class for time operations.

**Class Attributes:**
- `name = "time"` - Expert identifier
- `description` - Human-readable description
- `version = "2.0.0"` - Expert version
- `priority = 5` - Routing priority

**Instance Attributes:**
- `use_mcp: bool` - Whether to use MCP server
- `mcp_server: str` - MCP server name

**Methods:**
- `get_operations() -> list[str]` - Returns ["get_time", "convert_time", "get_timezone_info"]
- `execute_operation(operation, parameters) -> dict` - Execute an operation
- `execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction
- `get_time(timezone="UTC") -> dict` - Get current time
- `convert_time(time, from_timezone, to_timezone) -> dict` - Convert time
- `get_timezone_info(location) -> dict` - Get timezone info

### TimeOperation

Enum of available operations.

```python
class TimeOperation(str, Enum):
    GET_TIME = "get_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"
```

### TimeQueryType

Enum of result query types.

```python
class TimeQueryType(str, Enum):
    CURRENT_TIME = "current_time"
    CONVERSION = "conversion"
    TIMEZONE_INFO = "timezone_info"
    ERROR = "error"
```

## Dependencies

- **chuk-virtual-expert** - Base virtual expert specification
- **python-dateutil** - Date/time parsing and manipulation

## License

MIT License - see [LICENSE](LICENSE) for details.
