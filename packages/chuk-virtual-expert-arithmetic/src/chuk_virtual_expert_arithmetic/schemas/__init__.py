"""Schema definitions for trace problem generation.

Schemas are organized by expert type in subdirectories:
- arithmetic/     - 16 schemas for arithmetic problems
- entity_track/   - 5 schemas for entity tracking problems
- rate_equation/  - 4 schemas for rate/time/distance problems
- comparison/     - 4 schemas for comparison problems
- percentage/     - 4 schemas for percentage problems

Each .json file defines a problem schema with:
- name: Schema identifier
- expert: Expert type (arithmetic, entity_track, etc.)
- description: Human-readable description
- pattern: Template pattern name
- variant: Optional variant within the pattern
- variables: Random variables to generate (type, min, max, constraints)
- derived: Computed variables from expressions
- constraints: Validation rules for variable combinations
- vocab: Vocabulary items to sample from vocab/*.json
- template_vars: Mappings from vocab to template placeholders
- trace: Sequence of trace operations to build
- answer: Expression to compute the expected answer

Trace operations vary by expert type:
- All: init, compute, query
- entity_track: transfer, consume, add_entity
- percentage: percent_off, percent_increase, percent_of
"""

from pathlib import Path

SCHEMA_DIR = Path(__file__).parent

# Expert subdirectories
EXPERT_DIRS = ["arithmetic", "entity_track", "rate_equation", "comparison", "percentage"]


def list_schemas() -> list[str]:
    """List all available schema names from all subdirectories."""
    schemas: list[str] = []

    # Root level (for backwards compatibility)
    schemas.extend(f.stem for f in SCHEMA_DIR.glob("*.json"))

    # Subdirectories
    for expert in EXPERT_DIRS:
        expert_dir = SCHEMA_DIR / expert
        if expert_dir.exists():
            schemas.extend(f.stem for f in expert_dir.glob("*.json"))

    return schemas


def list_schemas_by_expert() -> dict[str, list[str]]:
    """List schemas grouped by expert type."""
    by_expert: dict[str, list[str]] = {}

    for expert in EXPERT_DIRS:
        expert_dir = SCHEMA_DIR / expert
        if expert_dir.exists():
            by_expert[expert] = [f.stem for f in expert_dir.glob("*.json")]

    return by_expert
