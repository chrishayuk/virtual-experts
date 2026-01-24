# chuk-virtual-expert-arithmetic

Arithmetic trace-solving virtual experts - math word problem solvers for LLM routing.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A virtual expert plugin providing 5 specialized trace-solving experts for different math problem types. Each expert executes structured trace steps to solve word problems with verifiable intermediate results.

**Features:**
- **Entity tracking** - Track quantities through consumption, addition, and transfers
- **Pure arithmetic** - Compute chains of add, subtract, multiply, divide
- **Percentages** - Discounts, increases, and proportions
- **Rate equations** - Speed/distance/time and work-rate problems
- **Comparisons** - Differences and ratios between quantities
- **Trace verification** - Every step is auditable and verifiable
- **Data generators** - Seed-based generation for training data
- **Async-native** - Built for async/await patterns
- **Pydantic-native** - Type-safe with structured responses

## Installation

```bash
pip install chuk-virtual-expert-arithmetic
```

For development:
```bash
pip install chuk-virtual-expert-arithmetic[dev]
```

## Quick Start

### Using execute_trace

```python
from chuk_virtual_expert_arithmetic import EntityTrackExpert

expert = EntityTrackExpert()

# Solve: Alice has 16 eggs, gives 3 away, eats 4. How many left?
result = expert.execute_trace([
    {"init": "eggs", "value": 16},
    {"consume": {"entity": "eggs", "amount": 3}},
    {"consume": {"entity": "eggs", "amount": 4}},
    {"query": "eggs"},
])

print(result.success)  # True
print(result.answer)   # 9
```

### Percentage Calculations

```python
from chuk_virtual_expert_arithmetic import PercentageExpert

expert = PercentageExpert()

# A $200 jacket is 25% off. What is the sale price?
result = expert.execute_trace([
    {"init": "price", "value": 200},
    {"percent_off": {"base": "price", "rate": 25, "var": "sale_price"}},
    {"query": "sale_price"},
])

print(result.answer)  # 150.0
```

### Rate Equations

```python
from chuk_virtual_expert_arithmetic import RateEquationExpert

expert = RateEquationExpert()

# A car travels at 60 km/h for 2.5 hours. Distance?
result = expert.execute_trace([
    {"given": {"speed": 60, "time": 2.5}},
    {"formula": "distance = speed * time"},
    {"compute": {"op": "mul", "args": ["speed", "time"], "var": "distance"}},
    {"query": "distance"},
])

print(result.answer)  # 150.0
```

### Using VirtualExpertAction

```python
from chuk_virtual_expert_arithmetic import ArithmeticExpert
from chuk_virtual_expert.models import VirtualExpertAction

expert = ArithmeticExpert()

action = VirtualExpertAction(
    expert="arithmetic",
    operation="execute_trace",
    parameters={
        "trace": [
            {"init": "price", "value": 12},
            {"init": "qty", "value": 5},
            {"compute": {"op": "mul", "args": ["price", "qty"], "var": "total"}},
            {"query": "total"},
        ]
    },
)
result = expert.execute(action)

print(result.success)  # True
print(result.data)     # TraceResult with answer=60
```

### Data Generation

```python
from chuk_virtual_expert_arithmetic import TraceGenerator

gen = TraceGenerator(seed=42)

# Generate 10 examples per expert type
examples = gen.generate_all(n_per_type=10)
print(len(examples))  # 50 (10 x 5 expert types)

# Generate specific types
entity_examples = gen.generate_entity_track(5)
percentage_examples = gen.generate_percentage(5)
```

## Experts

### EntityTrackExpert

Tracks entity quantities through operations.

**Trace Steps:**
- `init` - Initialize an entity: `{"init": "eggs", "value": 16}`
- `consume` - Reduce quantity: `{"consume": {"entity": "eggs", "amount": 3}}`
- `add` - Increase quantity: `{"add": {"entity": "eggs", "amount": 5}}`
- `transfer` - Move between entities: `{"transfer": {"from": "alice", "to": "bob", "amount": 7}}`
- `compute` - Arithmetic on variables: `{"compute": {"op": "mul", "args": ["eggs", 2], "var": "revenue"}}`
- `query` - Return a value: `{"query": "eggs"}`

### ArithmeticExpert

Pure arithmetic computation chains.

**Trace Steps:**
- `init` - Initialize a variable: `{"init": "price", "value": 100}`
- `compute` - Arithmetic operation: `{"compute": {"op": "add", "args": ["price", "tax"], "var": "total"}}`
- `query` - Return a value: `{"query": "total"}`

**Supported ops:** `add`, `sub`, `mul`, `div`

### PercentageExpert

Percentage calculations.

**Trace Steps:**
- `init` - Initialize a variable
- `percent_off` - Apply discount: `{"percent_off": {"base": "price", "rate": 25, "var": "sale"}}`
- `percent_increase` - Apply increase: `{"percent_increase": {"base": "rent", "rate": 10, "var": "new_rent"}}`
- `percent_of` - Calculate portion: `{"percent_of": {"base": "total", "rate": 15, "var": "portion"}}`
- `query` - Return a value

### RateEquationExpert

Rate-based calculations (distance, speed, time, work rates).

**Trace Steps:**
- `given` - Declare known quantities: `{"given": {"speed": 60, "time": 2.5}}`
- `formula` - State the relationship: `{"formula": "distance = speed * time"}`
- `compute` - Calculate result: `{"compute": {"op": "mul", "args": ["speed", "time"], "var": "distance"}}`
- `query` - Return a value

### ComparisonExpert

Differences and ratios between quantities.

**Trace Steps:**
- `init` - Initialize variables
- `compute` - Intermediate calculations
- `compare` - Compare values: `{"compare": {"op": "sub", "args": ["tom", "jerry"], "var": "difference"}}`
- `query` - Return a value

**Supported compare ops:** `sub` (difference), `div` (ratio)

## API Reference

### Expert Classes

All experts inherit from `TraceSolverExpert` and share:

**Methods:**
- `execute_trace(steps) -> TraceResult` - Execute a trace synchronously
- `execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction
- `can_handle(prompt) -> bool` - Check if prompt matches this expert
- `get_operations() -> list[str]` - Returns `["execute_trace"]`

**Class Attributes:**
- `name` - Expert identifier (e.g., "arithmetic", "entity_track")
- `description` - Human-readable description
- `version = "1.0.0"` - Expert version
- `priority = 10` - Routing priority

### TraceGenerator

Seed-based generator for training data.

**Methods:**
- `generate_entity_track(n) -> list[dict]` - Entity tracking examples
- `generate_arithmetic(n) -> list[dict]` - Pure arithmetic examples
- `generate_percentage(n) -> list[dict]` - Percentage examples
- `generate_rate_equation(n) -> list[dict]` - Rate equation examples
- `generate_comparison(n) -> list[dict]` - Comparison examples
- `generate_all(n_per_type) -> list[dict]` - All types combined

## Package Structure

```
src/chuk_virtual_expert_arithmetic/
  experts/        # TraceSolverExpert subclasses (5 experts)
  data/           # Training data (calibration, CoT examples, schema)
  generators/     # Data generation utilities
```

## Development

```bash
# Clone and install
git clone https://github.com/chrishayuk/virtual-experts
cd virtual-experts/packages/chuk-virtual-expert-arithmetic
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

- **chuk-virtual-expert** - Base virtual expert framework

## License

MIT License - see [LICENSE](LICENSE) for details.
