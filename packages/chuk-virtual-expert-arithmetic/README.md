# chuk-virtual-expert-arithmetic

Arithmetic trace-solving virtual experts for the chuk-virtual-expert framework.

## Experts

- **ArithmeticExpert**: Pure arithmetic chains (cost totals, sums, products)
- **EntityTrackExpert**: Entity state tracking (gives, loses, transfers)
- **PercentageExpert**: Percentage calculations (discounts, increases)
- **RateEquationExpert**: Rate/formula-based problems (speed, distance, time)
- **ComparisonExpert**: Comparison and difference calculations

## Package Structure

- `experts/` - Inference code (TraceSolverExpert subclasses)
- `data/` - Training data (calibration prompts, CoT examples)
- `generators/` - Data generation utilities
