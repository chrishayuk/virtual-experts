# chuk-virtual-expert-time

Time virtual expert backed by MCP server - accurate time and timezone operations for LLM routing.

[![CI](https://github.com/chrishayuk/virtual-experts/actions/workflows/ci-time-expert.yml/badge.svg)](https://github.com/chrishayuk/virtual-experts/actions/workflows/ci-time-expert.yml)
[![PyPI version](https://badge.fury.io/py/chuk-virtual-expert-time.svg)](https://badge.fury.io/py/chuk-virtual-expert-time)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/chrishayuk/virtual-experts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A virtual expert plugin that provides NTP-accurate time and timezone operations via the hosted MCP server at `https://time.chukai.io/mcp`. Works with Lazarus MoE models or as a standalone expert.

**Features:**
- **NTP-accurate time** - Uses MCP server with NTP consensus
- **Current time** - Get UTC or local time for any timezone
- **Timezone conversion** - Convert times between IANA timezones
- **Timezone info** - Look up timezone details with DST transitions
- **20+ timezone aliases** - Common cities and abbreviations
- **Async-only** - All execution is async (`await expert.execute_operation(...)`)
- **Pydantic-native** - Type-safe with structured responses
- **No magic strings** - Uses enums throughout

## Installation

```bash
pip install chuk-virtual-expert-time
```

For development:
```bash
pip install chuk-virtual-expert-time[dev]
```

## Quick Start

```python
import asyncio
from chuk_virtual_expert_time import TimeExpert, TimeOperation

async def main():
    expert = TimeExpert()

    # Get current UTC time
    result = await expert.execute_operation(
        TimeOperation.GET_TIME.value,
        {"timezone": "UTC"}
    )
    print(result)
    # {'query_type': 'current_time', 'timezone': 'UTC', 'iso8601': '2024-01-15T12:00:00+00:00', ...}

    # Get time in Tokyo (using alias)
    result = await expert.execute_operation(
        TimeOperation.GET_TIME.value,
        {"timezone": "tokyo"}
    )
    print(result["iso8601"])  # "2024-01-15T21:00:00+09:00"

    # Convert time between zones
    result = await expert.execute_operation(
        TimeOperation.CONVERT_TIME.value,
        {
            "time": "2024-01-15T15:00:00",
            "from_timezone": "est",
            "to_timezone": "pst",
        }
    )
    print(f"{result['from_time']} -> {result['to_time']}")

asyncio.run(main())
```

### Using VirtualExpertAction

```python
import asyncio
from chuk_virtual_expert_time import TimeExpert, TimeOperation
from chuk_virtual_expert.models import VirtualExpertAction

async def main():
    expert = TimeExpert()

    action = VirtualExpertAction(
        expert="time",
        operation=TimeOperation.GET_TIME.value,
        parameters={"timezone": "Asia/Tokyo"},
    )
    result = await expert.execute(action)

    print(result.success)  # True
    print(result.data)     # {'query_type': 'current_time', ...}

asyncio.run(main())
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
print(result.answer)
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
    "formatted": "2024-01-15T21:00:00+09:00",
    "utc_offset": "+09:00",
    "is_dst": False,
    "abbreviation": "JST",
    "source_utc": "2024-01-15T12:00:00+00:00",
    "estimated_error_ms": 50.0,
}
```

### convert_time

Convert time between timezones.

**Parameters:**
- `time`: ISO 8601 datetime string
- `from_timezone`: Source timezone (IANA or alias)
- `to_timezone`: Target timezone (IANA or alias)

**Returns:**
```python
{
    "query_type": "conversion",
    "from_timezone": "America/New_York",
    "to_timezone": "America/Los_Angeles",
    "from_time": "2024-01-15T15:00:00-05:00",
    "to_time": "2024-01-15T12:00:00-08:00",
    "from_iso8601": "2024-01-15T15:00:00-05:00",
    "to_iso8601": "2024-01-15T12:00:00-08:00",
    "explanation": "America/Los_Angeles is 3.0 hours behind America/New_York",
}
```

### get_timezone_info

Get timezone information for a location.

**Parameters:**
- `location`: Location name or IANA timezone

**Returns:**
```python
{
    "query_type": "timezone_info",
    "location": "Asia/Tokyo",
    "iana_timezone": "Asia/Tokyo",
    "utc_offset": "+09:00",
    "is_dst": False,
    "abbreviation": "JST",
    "transitions": [...]  # Upcoming DST transitions
}
```

## Enums

### TimeOperation

```python
from chuk_virtual_expert_time import TimeOperation

TimeOperation.GET_TIME           # "get_time"
TimeOperation.CONVERT_TIME       # "convert_time"
TimeOperation.GET_TIMEZONE_INFO  # "get_timezone_info"
```

### TimeMCPTool

MCP tool names on the server:

```python
from chuk_virtual_expert_time import TimeMCPTool

TimeMCPTool.GET_LOCAL_TIME       # "get_local_time"
TimeMCPTool.CONVERT_TIME         # "convert_time"
TimeMCPTool.GET_TIMEZONE_INFO    # "get_timezone_info"
TimeMCPTool.GET_TIME_UTC         # "get_time_utc"
TimeMCPTool.LIST_TIMEZONES       # "list_timezones"
TimeMCPTool.COMPARE_SYSTEM_CLOCK # "compare_system_clock"
```

### TimeQueryType

```python
from chuk_virtual_expert_time import TimeQueryType

TimeQueryType.CURRENT_TIME   # "current_time"
TimeQueryType.CONVERSION     # "conversion"
TimeQueryType.TIMEZONE_INFO  # "timezone_info"
TimeQueryType.ERROR          # "error"
```

### AccuracyMode

```python
from chuk_virtual_expert_time import AccuracyMode

AccuracyMode.FAST      # "fast" - 4 NTP servers
AccuracyMode.ACCURATE  # "accurate" - 7 NTP servers
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

## API Reference

### TimeExpert

Main expert class for time operations.

**Class Attributes:**
- `name = "time"` - Expert identifier
- `description` - Human-readable description
- `version = "3.0.0"` - Expert version
- `priority = 5` - Routing priority
- `mcp_server_url = "https://time.chukai.io/mcp"` - MCP server endpoint
- `mcp_timeout = 30.0` - Request timeout in seconds

**Methods:**
- `get_operations() -> list[str]` - Returns available operations
- `await execute_operation(operation, parameters) -> dict` - Execute an operation (async)
- `await execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction (async)
- `await list_mcp_tools() -> list[dict]` - List available MCP tools

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

# Run all checks (lint, format, mypy, bandit, tests)
make check

# Format code
make format

# Build package
make build
```

## Dependencies

- **chuk-virtual-expert[mcp]** - Base virtual expert with MCP support
- **chuk-mcp** - MCP client library

## License

MIT License - see [LICENSE](LICENSE) for details.
