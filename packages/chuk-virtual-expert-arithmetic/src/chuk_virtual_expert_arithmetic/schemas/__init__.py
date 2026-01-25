"""Schema definitions for arithmetic problem generation.

Each .json file defines a problem schema with:
- name: Schema identifier
- description: Human-readable description
- pattern: Template pattern from patterns.json
- variant: Optional variant within the pattern
- variables: Random variables to generate (type, min, max)
- derived: Computed variables from expressions
- constraints: Validation rules
- vocab: Vocabulary items to sample
- template_vars: Mappings from vocab to template placeholders
- trace: Sequence of trace operations
- answer: Expression to compute the answer
"""

from pathlib import Path

SCHEMA_DIR = Path(__file__).parent


def list_schemas() -> list[str]:
    """List all available schema names."""
    return [f.stem for f in SCHEMA_DIR.glob("*.json")]
