# Chuk Virtual Expert Arithmetic - Architecture Guide

This document describes the complete architecture for generating diverse arithmetic word problems with verifiable step-by-step solutions.

## Overview

The system generates natural language math problems from declarative JSON specifications. It separates **mathematical structure** (schemas) from **natural language** (patterns) and **vocabulary** (vocab), enabling diverse problem generation without code changes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROBLEM GENERATION ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   SCHEMAS    │
                              │  (56 files)  │
                              └──────┬───────┘
                                     │ defines math structure
                                     ▼
┌──────────────┐            ┌──────────────────┐            ┌──────────────┐
│    VOCAB     │◄──────────►│ SCHEMA GENERATOR │◄──────────►│   PATTERNS   │
│  (9+ files)  │  samples   │                  │  selects   │  (38 files)  │
└──────────────┘            └────────┬─────────┘            └──────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  TraceExample    │
                            │  query + trace   │
                            │  + answer        │
                            └──────────────────┘
```

## Directory Structure

```
src/chuk_virtual_expert_arithmetic/
├── types.py                    # ExpertType enum and constants
├── ARCHITECTURE.md             # This file
│
├── schemas/                    # Problem definitions (56 files)
│   ├── __init__.py
│   ├── arithmetic/             # 41 schemas
│   ├── percentage/             # 4 schemas
│   ├── comparison/             # 4 schemas
│   ├── entity_track/           # 5 schemas
│   └── rate_equation/          # 2 schemas
│
├── vocab/                      # Vocabulary system
│   ├── __init__.py             # Vocab class (singleton)
│   ├── names.json              # Person names (304 names)
│   ├── items.json              # Countable objects
│   ├── phrases.json            # Complex phrase structures
│   ├── places.json             # Locations and stores
│   ├── colors.json             # Color names
│   ├── materials.json          # Fabrics, building materials
│   ├── containers.json         # Container types
│   ├── ordinals.json           # Paired letters/numbers
│   ├── animals.json            # Farm animals with verbs
│   ├── domains/                # 14 semantic domains
│   └── patterns/               # Natural language templates
│       ├── arithmetic/         # 36 pattern files
│       ├── percentage/         # 1 pattern file
│       ├── comparison/         # 1 pattern file
│       ├── entity_track/       # 1 pattern file
│       └── rate_equation/      # 1 pattern file
│
├── generators/                 # Problem generation
│   ├── __init__.py             # TraceGenerator class
│   ├── schema_generator.py     # Core generation logic
│   └── composition.py          # Multi-expert compositions
│
├── schema/                     # Data models
│   ├── problem.py              # ProblemSpec model
│   ├── trace.py                # Trace step models
│   └── verifier.py             # Trace verification
│
├── trace_generators/           # Expert-specific trace builders
│   ├── arithmetic.py
│   ├── comparison.py
│   ├── entity.py
│   ├── allocation.py
│   └── router.py
│
└── experts/                    # Expert implementations
    ├── arithmetic.py
    ├── comparison.py
    ├── entity_track.py
    ├── percentage.py
    └── rate_equation.py
```

---

## 1. Schemas

Schemas define the **mathematical skeleton** of problems - what computation to perform, with what constraints, and how to present it.

**Location:** `schemas/<expert_type>/<name>.json`

### Schema Structure

```json
{
  "name": "combined_rate",
  "description": "Two machines combined output over time",

  "variables": {
    "rate1": {"type": "int", "min": 5, "max": 20},
    "rate2": {"type": "int", "min": 5, "max": 20},
    "time": {"type": "int", "min": 2, "max": 6}
  },

  "derived": {
    "total_rate": "rate1 + rate2"
  },

  "constraints": {
    "rate1 - rate2": {"min": -10, "max": 10}
  },

  "vocab": {
    "agent_pair": {"path": "phrases.agent_pairs"},
    "item": {"path": "phrases.rate_items"},
    "production": {"path": "phrases.production"},
    "time_unit_pair": {"path": "phrases.time_unit_pairs"}
  },

  "template_vars": {
    "agent1": "agent_pair.first",
    "agent2": "agent_pair.second",
    "verb": "production.verb",
    "verbs": "production.continuous",
    "item": "item",
    "time_unit": "time_unit_pair.singular",
    "time_units": "time_unit_pair.plural"
  },

  "pattern": "combined_rate",

  "trace": [
    {"op": "init", "var": "rate1", "value": "rate1"},
    {"op": "init", "var": "rate2", "value": "rate2"},
    {"op": "init", "var": "time", "value": "time"},
    {"op": "compute", "compute_op": "add", "args": ["rate1", "rate2"], "var": "step1"},
    {"op": "compute", "compute_op": "mul", "args": ["step1", "time"], "var": "result"},
    {"op": "query", "var": "result"}
  ],

  "answer": "(rate1 + rate2) * time"
}
```

### Schema Fields Reference

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Unique identifier |
| `description` | No | Human-readable description |
| `variables` | Yes | Random value specifications |
| `derived` | No | Computed from base variables |
| `constraints` | No | Validation bounds for regeneration |
| `vocab` | No | Vocabulary items to sample |
| `template_vars` | No | Maps vocab to template placeholders |
| `pattern` | No | Which pattern file to use |
| `variant` | No | Which variant within pattern |
| `trace` | Yes | Step-by-step computation |
| `answer` | Yes | Math expression for final result |

### Variable Types

```json
"variables": {
  "count": {
    "type": "int",
    "min": 5,
    "max": 20,
    "multiple_of": 5
  },
  "rate": {
    "type": "float",
    "min": 0.5,
    "max": 2.5,
    "precision": 2
  },
  "option": {
    "type": "choice",
    "options": [0.25, 0.5, 0.75, 1.5]
  },
  "flag": {
    "type": "bool"
  }
}
```

### Trace Operations

| Operation | Purpose | Example |
|-----------|---------|---------|
| `init` | Initialize variable | `{"op": "init", "var": "x", "value": "x"}` |
| `compute` | Arithmetic operation | `{"op": "compute", "compute_op": "mul", "args": ["a", "b"], "var": "result"}` |
| `query` | Return final value | `{"op": "query", "var": "result"}` |
| `transfer` | Entity transfer | `{"op": "transfer", "from_entity": "A", "to_entity": "B", "amount": 5}` |
| `consume` | Remove from entity | `{"op": "consume", "entity": "inventory", "amount": 3}` |
| `add_entity` | Create entity | `{"op": "add_entity", "entity": "new", "amount": 10}` |
| `percent_off` | Discount | `{"op": "percent_off", "base": "price", "rate": 20, "var": "result"}` |
| `percent_increase` | Growth | `{"op": "percent_increase", "base": "value", "rate": 50, "var": "result"}` |
| `percent_of` | Percentage | `{"op": "percent_of", "base": "whole", "rate": 25, "var": "result"}` |

**Compute Operations:** `add`, `sub`, `mul`, `div`, `mod`, `pow`, `floor_div`

---

## 2. Vocabulary System

The vocab system provides **diverse, reusable vocabulary** for natural language generation.

**Location:** `vocab/`

### Core Vocab Files

**names.json** - Person names with pronoun support:
```json
{
  "male": ["Alex", "Benjamin", "Christopher", ...],
  "female": ["Alice", "Bella", "Catherine", ...],
  "neutral": ["Casey", "Drew", "Jordan", ...],
  "people": ["Alex", "Alice", "Benjamin", ...],
  "pronouns": {
    "male": {
      "subject": "he",
      "object": "him",
      "possessive": "his",
      "reflexive": "himself"
    },
    "female": {
      "subject": "she",
      "object": "her",
      "possessive": "her",
      "reflexive": "herself"
    },
    "neutral": {
      "subject": "they",
      "object": "them",
      "possessive": "their",
      "reflexive": "themselves"
    }
  }
}
```

**items.json** - Countable objects by category:
```json
{
  "countable_singular": ["apple", "orange", "book", "coin", ...],
  "countable_plural": ["apples", "oranges", "books", ...],
  "vehicles": ["car", "bus", "train", "truck", ...],
  "produce": ["tomatoes", "cucumbers", "carrots", ...],
  "fruits": ["apples", "oranges", "bananas", ...],
  "baked_goods": ["cookies", "muffins", "cupcakes", ...],
  "manufactured": ["widgets", "parts", "units", ...],
  "school_supplies": ["pencils", "pens", "notebooks", ...]
}
```

**phrases.json** - Complex phrase structures:
```json
{
  "production": [
    {"verb": "produce", "continuous": "produces"},
    {"verb": "make", "continuous": "makes"},
    {"verb": "bake", "continuous": "bakes"}
  ],
  "agent_pairs": [
    {"first": "Machine A", "second": "Machine B", "domain": "factory"},
    {"first": "Alice", "second": "Bob", "domain": "people"},
    {"first": "Oven 1", "second": "Oven 2", "domain": "kitchen"}
  ],
  "distribution_targets": [
    {"plural": "trucks", "singular": "truck"},
    {"plural": "boxes", "singular": "box"}
  ],
  "time_unit_pairs": [
    {"singular": "minute", "plural": "minutes"},
    {"singular": "hour", "plural": "hours"},
    {"singular": "day", "plural": "days"}
  ],
  "expense_categories": [
    "lunch", "dinner", "groceries", "transport", "entertainment"
  ],
  "multiplier_words": {
    "2": ["doubled", "grew 2 times"],
    "3": ["tripled", "grew 3 times"],
    "4": ["quadrupled", "grew 4 times"]
  }
}
```

### Vocab Class API

```python
class Vocab:
    # Core access methods
    def get(self, path: str) -> Any:
        """Get by dot path: vocab.get('items.fruits')"""

    def random(self, path: str) -> Any:
        """Random item: vocab.random('names.people') → 'Sarah'"""

    def sample(self, path: str, k: int) -> list:
        """K random items: vocab.sample('items.fruits', 3)"""

    # Special generators
    def person_with_pronouns(self) -> dict:
        """Returns: {name, subject, object, possessive, reflexive, verb_s}"""

    def container_pair(self) -> tuple:
        """Returns: (singular, plural) like ('box', 'boxes')"""

    # Template methods
    def substitute(self, template: str, **kwargs) -> str:
        """Replace ${var} placeholders in template"""

    def pattern(self, name: str, variant: str = None, **kwargs) -> str:
        """Load pattern, select template, substitute variables"""
```

### Vocab Access in Schemas

```json
"vocab": {
  "person": {"type": "person_with_pronouns"},
  "item": {"path": "items.countable_singular"},
  "agent_pair": {"path": "phrases.agent_pairs"},
  "expense": {"path": "phrases.expense_categories"}
}
```

| Access Type | Syntax | Result |
|-------------|--------|--------|
| `person_with_pronouns` | `{"type": "person_with_pronouns"}` | Full person object with pronouns |
| `path` | `{"path": "items.fruits"}` | Random item from that vocab path |
| `choice` | `{"type": "choice", "values": [...]}` | Random from provided list |

---

## 3. Patterns

Patterns define **how to phrase problems** using `${variable}` placeholders.

**Location:** `vocab/patterns/<expert_type>/<name>.json`

### Pattern Structure

**Simple pattern (templates list):**
```json
{
  "templates": [
    "${agent1} ${verbs} ${rate1} ${item} per ${time_unit}, while ${agent2} ${verbs} ${rate2} ${item} per ${time_unit}. If both run for ${time} ${time_units}, how many ${item} in total?",
    "${agent1} and ${agent2} each ${verb} ${item}. ${agent1} ${verbs} ${rate1} per ${time_unit}, ${agent2} ${verbs} ${rate2} per ${time_unit}. Total ${item} after ${time} ${time_units}?"
  ]
}
```

**Pattern with variants:**
```json
{
  "weekly_sprints": [
    "${name} decides to run ${sprints_per_session} sprints ${sessions_per_week} times a week. How many total meters?",
    "${name} does ${sprints_per_session} sprints ${sessions_per_week} times weekly. What's the total distance?"
  ],
  "weekly_laps": [
    "${name} swims ${laps_per_session} laps ${sessions_per_week} times a week. How many meters weekly?"
  ],
  "repeated_value": [
    "${name} does ${count} sprints ${count} times a week. Each sprint is ${meters} meters. Total?"
  ]
}
```

### Pattern-Schema Connection

The schema's `pattern` and `variant` fields select which templates to use:

```
Schema                              Pattern File
──────                              ────────────
pattern: "activity_patterns"   ──►  vocab/patterns/arithmetic/activity_patterns.json
variant: "weekly_sprints"      ──►  selects the "weekly_sprints" key from that file
```

### Diversity Through Variants

Each pattern file can have multiple variants, and each variant has multiple template phrasings:

```json
{
  "farm": [
    "${name} owns a farm with ${count} ${animals}...",
    "On ${name}'s family farm, there are ${count} ${animals}..."
  ],
  "orchard": [
    "${name} owns an orchard with ${count} ${fruit} trees...",
    "In ${name}'s orchard, there are ${count} trees..."
  ],
  "bakery": [
    "${name} spent the morning baking ${count} batches...",
    "For a charity bake sale, ${name} made ${count} batches..."
  ]
}
```

---

## 4. Template Variables

Template variables **bridge schema data to pattern placeholders**.

### Resolution Flow

```
Schema vocab section        Schema template_vars         Pattern template
────────────────────        ────────────────────         ────────────────
"person": {type: ...}  ──►  "name": "person.name"   ──►  "${name} bought..."
                            "subject": "person.subject"   "${subject} paid..."
                            "his_her": "person.possessive"
```

### Template Spec Types

| Spec Format | Example | Resolution |
|-------------|---------|------------|
| Direct variable | `"count"` | Value from variables dict |
| Vocab reference | `"item"` | Sampled vocab item |
| Dot notation | `"person.name"` | Nested object access |
| Pipe transform | `"item\|pluralize"` | Apply transformation |
| Literal | `"delivery"` | Returns unchanged |

### Available Transforms

| Transform | Input | Output |
|-----------|-------|--------|
| `capitalize` | "apple" | "Apple" |
| `pluralize` | "apple" | "apples" |
| `singularize` | "apples" | "apple" |
| `with_article` | "apple" | "an apple" |
| `has_have` | (verb_s="s") | "has" |
| `does_do` | (verb_s="s") | "does" |

### Example template_vars Section

```json
"template_vars": {
  "name": "person.name",
  "subject": "person.subject",
  "subj": "person.subject|capitalize",
  "his_her": "person.possessive",
  "items": "item|pluralize",
  "a_item": "item|with_article",
  "container": "container.singular",
  "containers": "container.plural"
}
```

---

## 5. Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMPLETE GENERATION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: LOAD SCHEMA
        └── Read JSON from schemas/<expert>/<name>.json

Step 2: GENERATE VARIABLES
        ├── For each variable spec:
        │   ├── int: random.randint(min, max)
        │   ├── float: random.uniform(min, max)
        │   ├── choice: random.choice(options)
        │   └── Apply multiple_of if specified
        └── Result: {rate1: 12, rate2: 8, time: 3}

Step 3: COMPUTE DERIVED (optional)
        ├── Evaluate each formula in order
        └── Result: {total_rate: 20, ...}

Step 4: VALIDATE CONSTRAINTS (optional)
        ├── Check each constraint expression
        └── Regenerate if any fail (up to 10 retries)

Step 5: SAMPLE VOCAB
        ├── For each vocab spec:
        │   ├── person_with_pronouns → full person object
        │   ├── path → vocab.random(path)
        │   └── choice → random.choice(values)
        └── Result: {agent_pair: {first: "Sarah", ...}, item: "cookies", ...}

Step 6: BUILD TEMPLATE VARS
        ├── Resolve each template_var spec:
        │   ├── Dot notation: "agent_pair.first" → "Sarah"
        │   ├── Transforms: "item|pluralize" → "cookies"
        │   └── Literals: "delivery" → "delivery"
        ├── Add numeric variables
        └── Result: {agent1: "Sarah", agent2: "Mike", item: "cookies", ...}

Step 7: SELECT & FILL PATTERN
        ├── Load pattern file: vocab/patterns/<expert>/<pattern>.json
        ├── Select variant (if specified)
        ├── Pick random template from list
        ├── Substitute all ${variable} placeholders
        └── Result: "Sarah bakes 12 cookies per hour, while Mike bakes 8..."

Step 8: WORD NUMBER CONVERSION (optional, 30% probability)
        └── Result: "Sarah bakes twelve cookies per hour..."

Step 9: BUILD TRACE
        ├── Parse each trace operation
        └── Create Step objects (InitStep, ComputeStep, QueryStep, ...)

Step 10: COMPUTE ANSWER
         ├── Evaluate answer expression with all variables
         └── Result: (12 + 8) * 3 = 60

Step 11: RETURN TraceExample
         └── TraceExample(expert="arithmetic", query="...", trace=[...], answer=60)
```

---

## 6. Expert Types

Defined in `types.py`:

```python
class ExpertType(StrEnum):
    ENTITY_TRACK = "entity_track"
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    PERCENTAGE = "percentage"
    RATE_EQUATION = "rate_equation"
```

| Expert | Schemas | Description |
|--------|---------|-------------|
| `arithmetic` | 41 | Basic operations, chains, multi-step |
| `percentage` | 4 | Discount, increase, tip, simple percent |
| `comparison` | 4 | "X times as many", "half as much" |
| `entity_track` | 5 | Transfer, consume, find/lose |
| `rate_equation` | 2 | Distance, earning (rate × time) |

---

## 7. Complete Example

### Schema: `combined_rate.json`

```json
{
  "name": "combined_rate",
  "pattern": "combined_rate",
  "vocab": {
    "agent_pair": {"path": "phrases.agent_pairs"},
    "item": {"path": "phrases.rate_items"},
    "production": {"path": "phrases.production"},
    "time_unit_pair": {"path": "phrases.time_unit_pairs"}
  },
  "template_vars": {
    "agent1": "agent_pair.first",
    "agent2": "agent_pair.second",
    "verb": "production.verb",
    "verbs": "production.continuous",
    "item": "item",
    "time_unit": "time_unit_pair.singular",
    "time_units": "time_unit_pair.plural"
  },
  "variables": {
    "rate1": {"type": "int", "min": 5, "max": 20},
    "rate2": {"type": "int", "min": 5, "max": 20},
    "time": {"type": "int", "min": 2, "max": 6}
  },
  "trace": [
    {"op": "init", "var": "rate1", "value": "rate1"},
    {"op": "init", "var": "rate2", "value": "rate2"},
    {"op": "init", "var": "time", "value": "time"},
    {"op": "compute", "compute_op": "add", "args": ["rate1", "rate2"], "var": "step1"},
    {"op": "compute", "compute_op": "mul", "args": ["step1", "time"], "var": "result"},
    {"op": "query", "var": "result"}
  ],
  "answer": "(rate1 + rate2) * time"
}
```

### Pattern: `vocab/patterns/arithmetic/combined_rate.json`

```json
{
  "templates": [
    "${agent1} ${verbs} ${rate1} ${item} per ${time_unit}, while ${agent2} ${verbs} ${rate2} ${item} per ${time_unit}. If both run for ${time} ${time_units}, how many ${item} in total?"
  ]
}
```

### Generated Output

```python
TraceExample(
    expert="arithmetic",
    query="Sarah bakes 12 cookies per hour, while Mike bakes 8 cookies per hour. If both run for 3 hours, how many cookies in total?",
    trace=[
        InitStep(var="rate1", value=12),
        InitStep(var="rate2", value=8),
        InitStep(var="time", value=3),
        ComputeStep(compute_op="add", args=["rate1", "rate2"], var="step1"),
        ComputeStep(compute_op="mul", args=["step1", "time"], var="result"),
        QueryStep(var="result")
    ],
    answer=60.0,
    expected_operation="execute_trace"
)
```

---

## 8. Adding New Content

### Adding a New Schema

1. Create `schemas/<expert>/<name>.json`
2. Define `variables`, `trace`, and `answer`
3. Optionally add `vocab`, `template_vars`, `pattern`, `variant`

### Adding a New Pattern

1. Create `vocab/patterns/<expert>/<name>.json`
2. Add templates list or variant-keyed templates
3. Use `${variable}` placeholders

### Adding New Vocabulary

1. Edit existing JSON file or create new one in `vocab/`
2. Access via `vocab.random("file.path")`

### Adding a New Variant

1. Open existing pattern file
2. Add new key with list of templates
3. Reference in schema with `"variant": "new_variant"`

---

## 9. Design Principles

| Principle | Implementation |
|-----------|----------------|
| **No hardcoded values** | All names, items, verbs from JSON files |
| **Separation of concerns** | Schema (math) / Pattern (language) / Vocab (words) |
| **Diversity through variants** | Multiple patterns per schema type |
| **Extensibility** | Add JSON files, no Python changes needed |
| **Semantic coherence** | Domains bundle compatible vocab items |
| **Composability** | Schemas + any compatible pattern + any vocab |
| **Verifiability** | Trace provides step-by-step solution |

---

## 10. Statistics

| Component | Count |
|-----------|-------|
| Expert types | 5 |
| Total schemas | 56 |
| Total patterns | 38 |
| Vocab files | 9 |
| Domain files | 14 |
| Person names | 304 |
| Unique vocab items | ~1,320 |

---

## Usage

```python
from chuk_virtual_expert_arithmetic.generators import TraceGenerator

# Create generator with seed for reproducibility
gen = TraceGenerator(seed=42)

# Generate balanced examples from all expert types
examples = gen.generate_balanced(10)

# Generate from specific schemas
examples = gen.generate_from_schemas(n=5, schema_names=["combined_rate", "multiply_add"])

# Generate by expert type
examples = gen.generate_arithmetic(10)
examples = gen.generate_percentage(10)
examples = gen.generate_entity_track(10)

for ex in examples:
    print(f"[{ex.expert}] {ex.query}")
    print(f"Answer: {ex.answer}")
```
