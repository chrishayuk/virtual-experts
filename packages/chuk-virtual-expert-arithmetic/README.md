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
- **Async-only** - All execution is async (`await expert.execute_operation(...)`)
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
from chuk_virtual_expert_arithmetic.generators import TraceGenerator, SchemaGenerator

# TraceGenerator - High-level API with balanced distribution
gen = TraceGenerator(seed=42)

# Generate balanced examples across all expert types
examples = gen.generate_balanced(n=100)
# Distribution: arithmetic 30%, entity_track 20%, comparison 15%,
#               composition 15%, percentage 10%, rate_equation 10%

# Generate specific expert types
entity_examples = gen.generate_entity_track(10)
arithmetic_examples = gen.generate_arithmetic(10)
percentage_examples = gen.generate_percentage(10)

# SchemaGenerator - Low-level schema-based generation
schema_gen = SchemaGenerator()
print(schema_gen.schema_names)  # List all 33 available schemas

# Generate from specific schema
example = schema_gen.generate("price_chain")
print(example.query)   # The word problem
print(example.trace)   # The structured trace steps
print(example.answer)  # The computed answer
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
- `await execute_operation(operation, parameters) -> dict` - Execute an operation (async)
- `await execute(action) -> VirtualExpertResult` - Execute a VirtualExpertAction (async)
- `can_handle(prompt) -> bool` - Check if prompt matches this expert
- `get_operations() -> list[str]` - Returns `["execute_trace"]`

**Class Attributes:**
- `name` - Expert identifier (e.g., "arithmetic", "entity_track")
- `description` - Human-readable description
- `version = "1.0.0"` - Expert version
- `priority = 10` - Routing priority

### TraceGenerator

Seed-based generator for training data. All methods use schema-based generation internally.

**Methods:**
- `generate_entity_track(n) -> list[TraceExample]` - Entity tracking examples (5 schemas)
- `generate_arithmetic(n) -> list[TraceExample]` - Pure arithmetic examples (16 schemas)
- `generate_percentage(n) -> list[TraceExample]` - Percentage examples (4 schemas)
- `generate_rate_equation(n) -> list[TraceExample]` - Rate equation examples (4 schemas)
- `generate_comparison(n) -> list[TraceExample]` - Comparison examples (4 schemas)
- `generate_composition(n) -> list[dict]` - Multi-expert composition examples
- `generate_all(n_per_type) -> list[TraceExample]` - Equal distribution across types
- `generate_balanced(n) -> list` - Weighted distribution (recommended for training)
- `generate_from_schemas(n, schema_names) -> list[TraceExample]` - From specific schemas

### SchemaGenerator

Low-level schema-based generator.

**Methods:**
- `generate(schema_name) -> TraceExample` - Generate from a specific schema
- `generate_batch(schema_names, n) -> list[TraceExample]` - Generate batch from schemas
- `schema_names -> list[str]` - List available schema names (33 total)

## Package Structure

```
src/chuk_virtual_expert_arithmetic/
  experts/           # TraceSolverExpert subclasses (5 experts)
  generators/        # Data generation (TraceGenerator, SchemaGenerator)
  schemas/           # JSON schema definitions (organized by expert)
    arithmetic/      # 16 arithmetic schemas
    entity_track/    # 5 entity tracking schemas
    rate_equation/   # 4 rate equation schemas
    comparison/      # 4 comparison schemas
    percentage/      # 4 percentage schemas
  vocab/             # Vocabulary JSON files for template generation
    patterns/        # Question templates (organized by expert)
      arithmetic/
      entity_track/
      rate_equation/
      comparison/
      percentage/
    names.json       # Person names and pronouns
    items.json       # Countable items, products
    places.json      # Stores, cities, locations
    phrases.json     # Verbs, units, expressions
    ...
  data/              # Training data (calibration, CoT examples)
```

## Schema-Based Generation

All data generation uses a **schema-driven approach** where patterns are defined in JSON files rather than hardcoded Python.

### Schema Structure

Each schema defines:
- **Variables** - Random values with ranges and constraints
- **Vocab** - Vocabulary items to sample (names, items, verbs)
- **Pattern** - Template name for question generation
- **Trace** - Structured trace steps to build
- **Answer** - Expression to compute the answer

Example schema (`schemas/arithmetic/price_chain.json`):
```json
{
  "name": "price_chain",
  "expert": "arithmetic",
  "pattern": "price_chain",
  "variables": {
    "base": {"type": "int", "min": 10, "max": 100},
    "tax": {"type": "float", "min": 1.0, "max": 10.0, "precision": 2},
    "shipping": {"type": "int", "min": 2, "max": 15}
  },
  "vocab": {
    "person": {"type": "person_with_pronouns"},
    "item": {"path": "items.countable_singular"},
    "store": {"path": "places.stores"}
  },
  "trace": [
    {"op": "init", "var": "price", "value": "base"},
    {"op": "init", "var": "tax", "value": "tax"},
    {"op": "init", "var": "shipping", "value": "shipping"},
    {"op": "compute", "compute_op": "add", "args": ["price", "tax"], "var": "with_tax"},
    {"op": "compute", "compute_op": "add", "args": ["with_tax", "shipping"], "var": "total"},
    {"op": "query", "var": "total"}
  ],
  "answer": "base + tax + shipping"
}
```

### Pattern Templates

Patterns define question templates with variable substitution:

```json
{
  "templates": [
    "${name} bought ${a_item} at ${store} for $${base}. With $${tax} tax and $${shipping} ${fee}, what's the total?",
    "At ${store}, ${name} found ${a_item} for $${base}. After adding $${tax} tax and $${shipping} shipping, how much did ${subject} pay?"
  ]
}
```

### Adding New Schemas

1. Create a JSON file in the appropriate `schemas/{expert}/` directory
2. Create a pattern file in `vocab/patterns/{expert}/` if needed
3. The schema will be automatically loaded by `SchemaGenerator`

```python
# Your new schema is immediately available
from chuk_virtual_expert_arithmetic.generators import SchemaGenerator

gen = SchemaGenerator()
example = gen.generate("my_new_schema")
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
