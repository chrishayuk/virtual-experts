# Vocabulary & Domain System Architecture

## Overview

This system generates diverse, semantically coherent training data for math word problems. It separates concerns into reusable components that can be combined to produce technical specifications, which are then expanded to natural language by an LLM.

**Design Goals:**
- Expert-agnostic: Works for arithmetic, time, weather, or any future expert type
- No hardcoded values: Names, items, and other vocab come from shared pools
- Domain coherence: Agents, items, verbs, and time units make semantic sense together
- Verifiable: Every spec includes a computation trace for answer verification

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VOCABULARY LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                        │
│  │  Shared Vocab   │     │     Domains     │                        │
│  │                 │     │                 │                        │
│  │  names.json     │◄────│  kitchen.json   │                        │
│  │  items.json     │     │  factory.json   │                        │
│  │  colors.json    │     │  travel.json    │                        │
│  │  ...            │     │  ...            │                        │
│  └─────────────────┘     └─────────────────┘                        │
│         │                        │                                   │
└─────────┼────────────────────────┼───────────────────────────────────┘
          │                        │
          │    ┌───────────────────┼───────────────────┐
          │    │                   │                   │
          ▼    ▼                   ▼                   │
┌─────────────────────────────────────────────────────────────────────┐
│                         SCHEMA LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   arithmetic/   │  │   percentage/   │  │  entity_track/  │     │
│  │                 │  │                 │  │                 │     │
│  │  combined_rate  │  │  percent_off    │  │  simple_transfer│     │
│  │  work_rate      │  │  percent_tip    │  │  find_lose      │     │
│  │  multiply_add   │  │  ...            │  │  ...            │     │
│  │  ...            │  │                 │  │                 │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SPEC GENERATOR                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Load schema (variables, formula, trace)                         │
│  2. Generate random variable values                                  │
│  3. Compute derived variables                                        │
│  4. Sample domain (agents, items, verbs, time_units)                │
│  5. Compute answer from formula                                      │
│  6. Build technical specification                                    │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TECHNICAL SPEC                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  {                                                                   │
│    "schema": "combined_rate",                                        │
│    "domain": "kitchen",                                              │
│    "agent1": "Sarah", "agent2": "Mike",                             │
│    "item": "cookies", "verb": "bake",                               │
│    "rate1": 12, "rate2": 8, "time": 3,                              │
│    "formula": "(rate1 + rate2) * time",                             │
│    "answer": 60,                                                     │
│    "trace": [...]                                                    │
│  }                                                                   │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       LLM EXPANSION                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Input: Technical spec                                               │
│  Output: Natural language word problem                               │
│                                                                      │
│  "Sarah bakes 12 cookies per hour while Mike bakes 8 cookies        │
│   per hour. If they both bake for 3 hours, how many cookies         │
│   do they make in total?"                                            │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TRAINING EXAMPLE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Question: [Natural language from LLM]                               │
│  Answer: 60                                                          │
│  Trace: [Step-by-step computation in YAML/CoT format]               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Shared Vocabulary

Reusable vocabulary pools that can be referenced by any domain or expert type.

**Location:** `vocab/*.json`

| File | Contents | Example |
|------|----------|---------|
| `names.json` | Person names with pronouns | 304 names (male, female, neutral) |
| `items.json` | Countable/uncountable items | apples, books, gallons |
| `colors.json` | Color names | red, blue, green |
| `materials.json` | Fabrics, building materials | cotton, brick, wood |
| `containers.json` | Container types | box, basket, tank |
| `ordinals.json` | Letter/number pairs | A/B, 1/2, first/second |
| `places.json` | Locations, stores | grocery store, farm |
| `animals.json` | Animals with produce/verbs | chickens → eggs, lay |
| `phrases.json` | Common phrase patterns | "half of", "twice as" |

**Access Pattern:**
```json
{"source": "names.people", "pattern": "${name}"}
```

---

### 2. Domains

Domains bundle coherent vocabulary for a specific context. They ensure semantic coherence - a kitchen domain produces "Sarah bakes cookies" not "Server A processes cookies".

**Location:** `vocab/domains/*.json`

**Available Domains (14):**

| Domain | Agent Types | Items | Verbs |
|--------|-------------|-------|-------|
| kitchen | appliance, person | cookies, cakes, pies | bakes |
| factory | machine, line | widgets, parts, units | produces |
| travel | vehicle, person | miles, kilometers | travels |
| office | equipment, person | pages, documents | processes |
| farm | equipment, person | bales, bushels, crops | harvests |
| garden | plant, person | tomatoes, flowers | produces |
| tech | server, person | requests, queries, tasks | processes |
| sports | team, person | points, goals, laps | scores |
| reading | person | pages, chapters, books | reads |
| school | person, classroom | students, problems | completes |
| shopping | person | apples, books, toys | buys |
| construction | crew, person | bricks, walls | completes |
| plumbing | fixture | gallons, liters | delivers |
| poultry | coop, person | eggs, chicks | lays |

**Domain Structure:**
```json
{
  "name": "kitchen",
  "description": "Cooking and baking",

  "agent_types": ["appliance", "person"],
  "agent_templates": {
    "appliance": {
      "pattern": "Oven ${number}",
      "numbers": [1, 2, 3]
    },
    "person": {
      "source": "names.people",
      "pattern": "${name}"
    }
  },

  "items": ["cookies", "loaves", "cakes", "muffins", "pies"],
  "verbs": {"singular": "bakes", "plural": "bake"},
  "time_units": [
    {"singular": "hour", "plural": "hours"},
    {"singular": "minute", "plural": "minutes"}
  ]
}
```

**Agent Template Types:**

| Type | Example | Output |
|------|---------|--------|
| Shared vocab reference | `{"source": "names.people"}` | "Sarah", "Mike" |
| Letter pattern | `{"pattern": "Machine ${letter}", "letters": ["A","B"]}` | "Machine A" |
| Number pattern | `{"pattern": "Oven ${number}", "numbers": [1,2,3]}` | "Oven 2" |

---

### 3. Schemas

Schemas define the mathematical structure of a problem - variables, formulas, and computation traces. They are domain-agnostic.

**Location:** `schemas/<category>/*.json`

**Categories:**
- `arithmetic/` - Basic operations (45 schemas)
- `comparison/` - Comparisons (4 schemas)
- `percentage/` - Percent calculations (4 schemas)
- `entity_track/` - Entity state tracking (5 schemas)
- `rate_equation/` - Rate problems (4 schemas)

**Schema Structure:**
```json
{
  "name": "combined_rate",
  "description": "Two agents combined output over time",

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

**Schema Fields (only these are allowed):**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Schema identifier |
| `description` | Yes | Human-readable description |
| `variables` | Yes | Variable definitions with types and ranges |
| `constraints` | No | Constraints on variable combinations |
| `derived` | No | Computed variables (math-only, no vocab) |
| `trace` | Yes | Step-by-step computation trace |
| `answer` | Yes | Formula to compute the answer |

**Note:** Schemas must NOT contain: `pattern`, `vocab`, `template_vars`, `templates`, `variant`, `expert`. These are legacy fields from the old architecture.

**Variable Types:**
| Type | Example | Description |
|------|---------|-------------|
| `int` | `{"type": "int", "min": 5, "max": 20}` | Random integer in range |
| `float` | `{"type": "float", "min": 0.1, "max": 1.0, "precision": 2}` | Random float |
| `choice` | `{"type": "choice", "options": [0.25, 0.5, 0.75]}` | Random from list |

---

### 4. Technical Spec Format

The spec generator combines schema + domain to produce a technical specification.

**Full Spec Example:**
```json
{
  "schema": "combined_rate",
  "domain": "kitchen",
  "description": "Two agents combined output over time",

  "rate1": 12,
  "rate2": 8,
  "time": 3,

  "agent1": "Sarah",
  "agent2": "Mike",
  "item": "cookies",
  "time_unit": "hour",
  "time_units": "hours",
  "verb": "bake",
  "verbs": "bakes",

  "formula": "(rate1 + rate2) * time",
  "answer": 60.0,

  "trace": [
    {"op": "init", "var": "rate1", "value": "rate1"},
    {"op": "init", "var": "rate2", "value": "rate2"},
    {"op": "init", "var": "time", "value": "time"},
    {"op": "compute", "compute_op": "add", "args": ["rate1", "rate2"], "var": "step1"},
    {"op": "compute", "compute_op": "mul", "args": ["step1", "time"], "var": "result"},
    {"op": "query", "var": "result"}
  ]
}
```

**Spec Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Schema name |
| `domain` | string | Domain name |
| `description` | string | Human-readable description |
| `agent1`, `agent2` | string | Agent names (from domain) |
| `item` | string | Item being counted (from domain) |
| `time_unit`, `time_units` | string | Singular/plural time unit |
| `verb`, `verbs` | string | Plural/singular verb forms |
| `rate1`, `rate2`, `time`, ... | number | Variable values |
| `formula` | string | Answer formula |
| `answer` | number | Computed answer |
| `trace` | array | Step-by-step computation trace |

---

### 5. Spec Generator Usage

```python
from spec_generator import SpecGenerator

gen = SpecGenerator()

# List available schemas and domains
print(gen.schema_names)   # ['combined_rate', 'work_rate', ...]
print(gen.domain_names)   # ['kitchen', 'factory', ...]

# Generate single spec
spec = gen.generate_spec("combined_rate", "kitchen")

# Generate batch (balanced across domains)
specs = gen.generate_batch(
    schema_names=["combined_rate", "work_rate"],
    n=100,
    balance_domains=True
)

# Convert spec to LLM prompt
prompt = gen.spec_to_prompt(spec)
```

---

### 6. LLM Expansion Prompt

The spec generator produces prompts for LLM expansion:

```
Convert this technical specification into a natural word problem:

SPECIFICATION:
- Domain: kitchen
- Agent 1: Sarah
- Agent 2: Mike
- Item: cookies
- Rate 1: 12 cookies per hour
- Rate 2: 8 cookies per hour
- Duration: 3 hours
- Operation: (rate1 + rate2) * time
- Answer: 60

REQUIREMENTS:
1. Write a natural word problem that a human would write
2. Include context and narrative (who, why, where)
3. The answer must be exactly 60
4. Use the exact agents and items from the spec
5. Make it sound like a real-world scenario

OUTPUT: Just the word problem, nothing else.
```

---

## Design Principles

### 1. Separation of Concerns
- **Shared vocab**: Reusable across all experts
- **Domains**: Define semantic coherence
- **Schemas**: Define mathematical structure

### 2. No Hardcoded Names
Names and cross-cutting vocabulary live in shared files.

❌ Bad:
```json
{"agents": [{"first": "Alice", "second": "Bob"}]}
```

✅ Good:
```json
{"agent_templates": {"person": {"source": "names.people"}}}
```

### 3. Domain Coherence
Each domain ensures semantic coherence:
- ✅ Kitchen: "Sarah bakes cookies"
- ❌ Kitchen: "Server A processes cookies"

### 4. Extensibility
Adding a new expert type requires:
1. New schemas in `schemas/<expert>/`
2. Optionally new domains or shared vocab
3. The spec generator works unchanged

---

## File Structure

```
vocab/
├── ARCHITECTURE.md          # This documentation
├── names.json               # Shared: 304 person names
├── items.json               # Shared: countable items
├── colors.json              # Shared: colors
├── materials.json           # Shared: materials
├── containers.json          # Shared: containers
├── ordinals.json            # Shared: A/B, 1/2 pairs
├── places.json              # Shared: locations
├── animals.json             # Shared: farm animals
├── phrases.json             # Shared: phrase patterns
│
├── domains/                 # Domain-specific bundles
│   ├── kitchen.json         # Cooking context
│   ├── factory.json         # Manufacturing context
│   ├── travel.json          # Transportation context
│   └── ... (14 total)
│
└── patterns/                # Template patterns (legacy)
    └── arithmetic/
        └── ...

schemas/
├── arithmetic/              # 45 schemas
│   ├── combined_rate.json
│   ├── work_rate.json
│   └── ...
├── comparison/              # 4 schemas
├── percentage/              # 4 schemas
├── entity_track/            # 5 schemas
└── rate_equation/           # 4 schemas
```

---

## Adding New Components

### Adding a New Domain
1. Create `vocab/domains/<name>.json`
2. Define `agent_types` and `agent_templates`
3. Add domain-specific `items`, `verbs`, `time_units`

### Adding a New Schema
1. Create `schemas/<category>/<name>.json`
2. Define `variables`, `answer` formula, `trace`
3. Schema works with all compatible domains automatically

### Adding Shared Vocabulary
1. Add to existing file (e.g., more names in `names.json`)
2. Or create new shared file for new vocab category
3. Reference in domains via `"source": "filename.key"`

### Adding a New Expert Type
1. Create new schema category: `schemas/<expert>/`
2. Add expert-specific schemas
3. Optionally add new domains if needed
4. Spec generator works unchanged

---

## Metrics

| Component | Count |
|-----------|-------|
| Shared vocab files | 9 |
| Total vocab items | ~1,320 |
| Person names | 304 |
| Domains | 14 |
| Schemas | 62 |
| Schema categories | 5 |

**Diversity per Domain:**
- Person-enabled domains: ~304 agent name options
- Equipment-only domains: 10-14 agent name options

---

## Core Module Architecture

The `core/` module provides the foundational building blocks for problem generation. This modular design replaces the monolithic `SchemaGenerator` with focused, composable components.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CORE MODULE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐     ┌───────────────┐ │
│  │  SchemaLoader   │────▶│  SchemaComposer │────▶│  Pydantic     │ │
│  │                 │     │                 │     │  Validation   │ │
│  │  - load schemas │     │  - mixins       │     │               │ │
│  │  - cache        │     │  - extends      │     │  SchemaSpec   │ │
│  │  - validate     │     │  - merge        │     │  VariableSpec │ │
│  └─────────────────┘     └─────────────────┘     └───────────────┘ │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌───────────────┐ │
│  │ VariableGenerator│────▶│ConstraintValid │────▶│ SafeEvaluator │ │
│  │                 │     │                 │     │               │ │
│  │  - int/float    │     │  - check bounds │     │  - AST-based  │ │
│  │  - difficulty   │     │  - retry logic  │     │  - no eval()  │ │
│  │  - avoid_round  │     │  - expressions  │     │  - secure     │ │
│  └─────────────────┘     └─────────────────┘     └───────────────┘ │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌───────────────┐ │
│  │  DomainSampler  │────▶│  VocabSampler   │────▶│TransformReg   │ │
│  │                 │     │                 │     │               │ │
│  │  - agents       │     │  - names        │     │  - pluralize  │ │
│  │  - items        │     │  - items        │     │  - capitalize │ │
│  │  - verbs        │     │  - pronouns     │     │  - article    │ │
│  └─────────────────┘     └─────────────────┘     └───────────────┘ │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐     ┌─────────────────┐                       │
│  │TemplateResolver │────▶│TemplatePerturbator│                     │
│  │                 │     │                 │                       │
│  │  - specs        │     │  - reorder      │                       │
│  │  - transforms   │     │  - fillers      │                       │
│  │  - substitution │     │  - synonyms     │                       │
│  └─────────────────┘     └─────────────────┘                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | File | Responsibility |
|-----------|------|----------------|
| `SafeEvaluator` | `core/expression.py` | Secure math evaluation (no `eval()`) |
| `SchemaLoader` | `core/loader.py` | Load, validate, cache schemas |
| `SchemaComposer` | `core/composer.py` | Schema composition (mixins/extends) |
| `VariableGenerator` | `core/variables.py` | Generate random variables |
| `ConstraintValidator` | `core/constraints.py` | Validate & retry logic |
| `TransformRegistry` | `core/transforms.py` | Pluggable text transforms |
| `VocabSampler` | `core/sampler.py` | Sample vocabulary items |
| `DomainSampler` | `core/domains.py` | Domain-first vocab sampling |
| `TemplateResolver` | `core/resolver.py` | Resolve template specs |
| `ContractValidator` | `core/contracts.py` | Validate pattern contracts |
| `TemplatePerturbator` | `core/perturbation.py` | GSM-8K generalization |
| `NumericDiversifier` | `core/perturbation.py` | Numeric diversity |

---

## Safe Expression Evaluation

The `SafeEvaluator` replaces `eval()` with an AST-based approach that is secure and extensible.

### Supported Operations

| Operator | Symbol | Example |
|----------|--------|---------|
| Addition | `+` | `a + b` |
| Subtraction | `-` | `a - b` |
| Multiplication | `*` | `a * b` |
| True Division | `/` | `a / b` → float |
| Floor Division | `//` | `a // b` → int |
| Modulo | `%` | `a % b` |
| Power | `**` | `a ** b` |
| Unary Negative | `-` | `-a` |

### Built-in Functions

| Function | Description | Example |
|----------|-------------|---------|
| `abs()` | Absolute value | `abs(-5)` → `5` |
| `min()` | Minimum | `min(a, b)` |
| `max()` | Maximum | `max(a, b)` |
| `round()` | Round to precision | `round(3.14159, 2)` → `3.14` |

### Division Behavior

The `/` operator (true division) always returns a float:
```python
10 / 2   # Returns 5.0, not 5
10 // 2  # Returns 5 (floor division)
```

### Usage

```python
from chuk_virtual_expert_arithmetic.core import SafeEvaluator

evaluator = SafeEvaluator()
result = evaluator.evaluate("(rate1 + rate2) * time", {
    "rate1": 12,
    "rate2": 8,
    "time": 3
})
# result = 60.0
```

---

## Schema Composition

Schemas support inheritance (`extends`) and mixins for code reuse.

### Mixins

Mixins provide reusable vocabulary and template variable definitions.

**Location:** `schemas/mixins/*.json`

| Mixin | Provides |
|-------|----------|
| `person_vocab` | Person names and pronouns |
| `item_vocab` | Item vocabulary |

**Example mixin** (`person_vocab.json`):
```json
{
  "name": "person_vocab",
  "vocab": {
    "person": {"type": "person_with_pronouns"}
  },
  "template_vars": {
    "name": "person.name",
    "subject": "person.subject",
    "subj": "person.subject|capitalize",
    "his_her": "person.possessive",
    "him_her": "person.object"
  }
}
```

### Using Mixins

Schemas reference mixins by name:

```json
{
  "name": "multiply_add",
  "mixins": ["person_vocab", "item_vocab"],
  "variables": {
    "base": {"type": "int", "min": 2, "max": 10}
  },
  "template_vars": {
    "item_singular": "item"
  },
  "trace": [...],
  "answer": "base * mult + addend"
}
```

### Inheritance

Schemas can extend a base schema:

```json
{
  "name": "custom_rate",
  "extends": "combined_rate",
  "variables": {
    "rate1": {"type": "int", "min": 10, "max": 30}
  }
}
```

### Composition Order

1. Load base schema (if `extends` specified)
2. Apply mixins in order
3. Apply schema's own definitions (overrides)

---

## Variable Generation

The `VariableGenerator` creates random values based on variable specifications.

### Variable Specification

```python
from chuk_virtual_expert_arithmetic.models import VariableSpec

spec = VariableSpec(
    type="int",
    min=1,
    max=100,
    multiple_of=5,        # Optional: divisible by 5
    avoid_round=True,     # Optional: not divisible by 10
    difficulty="hard"     # Optional: easy/medium/hard
)
```

### Difficulty Profiles

| Profile | Max Digits | Round Numbers | Range Scaling |
|---------|------------|---------------|---------------|
| `easy` | 2 | Preferred (×5) | Limited to 30 |
| `medium` | 3 | Allowed | Full range |
| `hard` | 4 | Avoided | Full range |

**Example:**
```python
from chuk_virtual_expert_arithmetic.core import VariableGenerator, DifficultyProfile

generator = VariableGenerator(seed=42)

# Easy generates small, round numbers
spec_easy = VariableSpec(type="int", min=1, max=100, difficulty="easy")
# Values like 5, 10, 15, 20, 25, 30

# Hard generates larger, non-round numbers
spec_hard = VariableSpec(type="int", min=1, max=100, difficulty="hard")
# Values like 37, 63, 84, 91
```

### Numeric Diversity

The `avoid_round` flag ensures numbers aren't divisible by 10:

```python
spec = VariableSpec(type="int", min=1, max=100, avoid_round=True)
# Never generates: 10, 20, 30, 40, ...
# Generates: 12, 37, 84, 91, ...
```

---

## Constraint Validation

The `ConstraintValidator` ensures generated variables satisfy mathematical constraints.

### Constraint Format

```json
{
  "constraints": {
    "start - cost1 - cost2": {"min": 10},
    "total": {"min": 1, "max": 1000}
  }
}
```

### Behavior

1. Generate initial variables
2. Evaluate constraint expressions
3. If violated, regenerate (up to 10 attempts)
4. Log warning if constraints cannot be satisfied

### Logging

When constraints fail after max attempts:
```
WARNING: Constraint validation failed after 10 attempts.
Violated constraints: ['start - cost1 - cost2']. Returning best effort.
```

---

## Transform System

The `TransformRegistry` provides pluggable text transformations.

### Built-in Transforms

| Transform | Description | Example |
|-----------|-------------|---------|
| `pluralize` | Singular → Plural | `apple` → `apples` |
| `singularize` | Plural → Singular | `cookies` → `cookie` |
| `capitalize` | First letter uppercase | `sarah` → `Sarah` |
| `with_article` | Add a/an | `apple` → `an apple` |

### Usage in Template Vars

```json
{
  "template_vars": {
    "item_plural": "item|pluralize",
    "name_cap": "person.name|capitalize",
    "item_with_article": "item|with_article"
  }
}
```

### Custom Transforms

```python
from chuk_virtual_expert_arithmetic.core import TransformRegistry

# Register custom transform
TransformRegistry.register("uppercase", str.upper)

# Now usable in schemas
# "word|uppercase" → "WORD"
```

---

## GSM-8K Generalization (Perturbation)

The perturbation system helps synthetic data generalize to real benchmarks like GSM-8K.

### TemplatePerturbator

Applies random variations to break template regularity:

```python
from chuk_virtual_expert_arithmetic.core import TemplatePerturbator

perturbator = TemplatePerturbator(seed=42)

original = "Sarah has 5 apples. She buys 3 more. How many apples does Sarah have?"
perturbed = perturbator.perturb(original, level=0.3)
# "Now, Sarah has 5 apples. She buys 3 more apples. What's the total number of apples?"
```

### Perturbation Types

| Type | Description | Example |
|------|-------------|---------|
| Clause Reorder | Move clauses around | "X. Y. Z?" → "Y. X. Z?" |
| Filler Phrases | Add natural fillers | "So, " / "Now, " / "Here's the thing: " |
| Question Variation | Vary question form | "How many" → "What's the total" |
| Synonym Substitution | Replace common words | "buys" → "purchases" |

### NumericDiversifier

Generates diverse number representations:

```python
from chuk_virtual_expert_arithmetic.core import NumericDiversifier

diversifier = NumericDiversifier(seed=42)

# Vary how numbers appear
diversifier.diversify(12)  # "12", "twelve", "a dozen"
```

---

## Usage Examples

### Basic Problem Generation

```python
from chuk_virtual_expert_arithmetic.generators import TraceGenerator

gen = TraceGenerator(seed=42)
examples = gen.generate_balanced(100)

for ex in examples:
    print(f"Expert: {ex.expert}")
    print(f"Query: {ex.query}")
    print(f"Answer: {ex.answer}")
    print()
```

### Using Core Components Directly

```python
from chuk_virtual_expert_arithmetic.core import (
    SchemaLoader,
    VariableGenerator,
    ConstraintValidator,
    SafeEvaluator,
)

# Load schema with mixin composition
loader = SchemaLoader()
schema = loader.get("multiply_add")

# Generate variables
var_gen = VariableGenerator(seed=42)
variables = var_gen.generate(schema["variables"])

# Validate constraints
validator = ConstraintValidator()
variables = validator.apply(
    schema.get("constraints", {}),
    variables,
    lambda: var_gen.generate(schema["variables"])
)

# Compute answer
evaluator = SafeEvaluator()
answer = evaluator.evaluate(schema["answer"], variables)
```

### With Difficulty Control

```python
from chuk_virtual_expert_arithmetic.core import VariableGenerator, DifficultyProfile
from chuk_virtual_expert_arithmetic.models import VariableSpec

generator = VariableGenerator(seed=42)

# Get difficulty parameters
profile = DifficultyProfile.get("hard")
print(profile)
# {'max_digits': 4, 'avoid_round': True, 'prefer_round': False, 'range_scale': 1.0}

# Generate with difficulty
spec = VariableSpec(type="int", min=1, max=100, difficulty="hard")
value = generator.generate_one(spec)  # e.g., 73
```

### With Perturbation

```python
from chuk_virtual_expert_arithmetic.generators import TraceGenerator
from chuk_virtual_expert_arithmetic.core import TemplatePerturbator

gen = TraceGenerator(seed=42)
perturbator = TemplatePerturbator(seed=42)

example = gen.generate_one("multiply_add")

# Original query
print(example.query)

# Perturbed for GSM-8K generalization
perturbed = perturbator.perturb(example.query, level=0.5)
print(perturbed)
```

---

## Testing

### Run All Tests

```bash
make test
# or
pytest tests/ -v
```

### Test Coverage

```bash
make test-cov
# or
pytest tests/ --cov=src --cov-report=term-missing
```

### Verify Generation

```python
from chuk_virtual_expert_arithmetic.generators import TraceGenerator

gen = TraceGenerator(seed=42)
examples = gen.generate_balanced(20)

for ex in examples:
    # Check no unresolved templates
    assert '${' not in ex.query, f"Unresolved in {ex.expert}"
    # Check answer computed
    assert ex.answer is not None
    print(f"{ex.expert}: OK")
```

---

## Migration Notes

### From Legacy SchemaGenerator

The old `SchemaGenerator` is still functional but delegates to new core components:

```python
# Old way (still works)
from chuk_virtual_expert_arithmetic.generators import SchemaGenerator
gen = SchemaGenerator(seed=42)

# New way (recommended)
from chuk_virtual_expert_arithmetic.core import SchemaLoader, VariableGenerator
loader = SchemaLoader()
var_gen = VariableGenerator(seed=42)
```

### Schema Updates for Mixins

Schemas using person or item vocabulary should add mixins:

```json
{
  "name": "my_schema",
  "mixins": ["person_vocab", "item_vocab"],
  ...
}
```

This automatically provides:
- `name`, `subject`, `his_her`, `him_her` from person
- `item` vocabulary

---

## Metrics (Updated)

| Component | Count |
|-----------|-------|
| Core modules | 12 |
| Shared vocab files | 9 |
| Total vocab items | ~1,320 |
| Person names | 304 |
| Domains | 14 |
| Schemas | 56 |
| Schema categories | 5 |
| Mixins | 2 |
| Tests | 479 |

---

## Future Work

1. **i18n Support** - Locale-aware vocabulary loading
2. **More Mixins** - Time units, rate vocabulary, entity constraints
3. **LLM Paraphrase** - Post-generation paraphrasing for variety
4. **Hybrid Training** - Mix synthetic with real GSM-8K data
5. **Linguistic Analysis** - Template fingerprint detection
