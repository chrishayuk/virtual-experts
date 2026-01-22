"""
Generic Few-Shot Validation for Virtual Experts.

Validates that an expert's schema works with LLM few-shot prompting
before investing in fine-tuning.

Usage:
    from chuk_virtual_expert.validation import FewShotValidator

    validator = FewShotValidator(expert, model, tokenizer)
    results = validator.validate(test_queries, expected_answers)
    results.print_summary()
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .expert import VirtualExpert
from .models import VirtualExpertAction


class LLMProtocol(Protocol):
    """Protocol for LLM generation."""

    def generate(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class ValidationResult:
    """Result of validating a single query."""

    query: str
    expected_answer: Any
    raw_output: str = ""

    # Parsing
    parsed: bool = False
    parse_error: str | None = None

    # Action extraction
    action: VirtualExpertAction | None = None
    routed_to_expert: bool = False

    # Execution
    executed: bool = False
    exec_error: str | None = None
    result_data: dict | None = None

    # Verification
    verified: bool = False

    # Correctness
    answer: Any = None
    correct: bool = False

    @property
    def error(self) -> str | None:
        """Get the first error in the pipeline."""
        if self.parse_error:
            return f"parse:{self.parse_error}"
        if not self.routed_to_expert:
            return "not_routed"
        if self.exec_error:
            return f"exec:{self.exec_error}"
        if not self.verified:
            return "invalid_trace"
        if not self.correct:
            return f"wrong:{self.answer}"
        return None


@dataclass
class ValidationSummary:
    """Summary of validation results."""

    total: int = 0
    parsed: int = 0
    routed: int = 0
    executed: int = 0
    verified: int = 0
    correct: int = 0

    errors: dict[str, int] = field(default_factory=dict)
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def parse_rate(self) -> float:
        return self.parsed / self.total if self.total > 0 else 0

    @property
    def route_rate(self) -> float:
        return self.routed / self.total if self.total > 0 else 0

    @property
    def exec_rate(self) -> float:
        return self.executed / self.total if self.total > 0 else 0

    @property
    def valid_rate(self) -> float:
        return self.verified / self.total if self.total > 0 else 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0

    def print_summary(self) -> None:
        """Print validation summary."""
        print(f"\n{'=' * 60}")
        print("FEW-SHOT VALIDATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total queries: {self.total}")
        print()
        print("Pipeline metrics:")
        print(f"  Parsed:   {self.parsed:3d}/{self.total} ({self.parse_rate:5.1%})")
        print(f"  Routed:   {self.routed:3d}/{self.total} ({self.route_rate:5.1%})")
        print(f"  Executed: {self.executed:3d}/{self.total} ({self.exec_rate:5.1%})")
        print(f"  Valid:    {self.verified:3d}/{self.total} ({self.valid_rate:5.1%})")
        print(f"  Correct:  {self.correct:3d}/{self.total} ({self.accuracy:5.1%})")

        if self.errors:
            print("\nError breakdown:")
            for error, count in sorted(self.errors.items(), key=lambda x: -x[1]):
                print(f"  {error}: {count}")

        # Decision guidance
        print(f"\n{'=' * 60}")
        print("DECISION GUIDANCE")
        print(f"{'=' * 60}")

        if self.parse_rate < 0.5:
            print("⚠️  Parse rate <50%: Redesign trace format or simplify schema")
        elif self.valid_rate < 0.5:
            print("⚠️  Valid rate <50%: Simplify trace schema or add more examples")
        elif self.accuracy < 0.3:
            print("📈 Model can format but not reason well → Fine-tuning will help significantly")
        elif self.accuracy < 0.6:
            print("✓ Few-shot shows promise → Fine-tune for production quality")
        elif self.accuracy < 0.8:
            print("✓ Few-shot works well → Fine-tune for polish")
        else:
            print("✓ Few-shot is sufficient → Consider skipping fine-tune")


class FewShotValidator:
    """
    Generic few-shot validator for virtual experts.

    Uses the expert's CoT examples to build few-shot prompts,
    then validates that the expert can execute the outputs.
    """

    def __init__(
        self,
        expert: VirtualExpert,
        generate_fn: Callable[[str, int], str],
        max_examples: int = 3,
        verbose: bool = False,
    ):
        """
        Initialize validator.

        Args:
            expert: The virtual expert to validate
            generate_fn: Function that takes (prompt, max_tokens) and returns text
            max_examples: Number of few-shot examples to use
            verbose: Print detailed output
        """
        self.expert = expert
        self.generate = generate_fn
        self.max_examples = max_examples
        self.verbose = verbose

        # Build prompt template from expert's CoT examples
        self._build_prompt_template()

    def _build_prompt_template(self) -> None:
        """Build few-shot prompt template from expert's examples."""
        cot_examples = self.expert.get_cot_examples()

        examples_text = ""
        for ex in cot_examples.examples[: self.max_examples]:
            examples_text += f'Query: "{ex.query}"\n'
            examples_text += f"Action: {ex.action.model_dump_json(indent=2)}\n\n"

        schema = self.expert.get_schema()
        ops_summary = schema.get_operations_summary() if schema.operations else ""

        self.prompt_template = f"""You extract structured actions from user queries.

## Expert: {self.expert.name}
{self.expert.description}

{ops_summary}

## Output Format
Respond with ONLY a valid JSON object:
{{"expert": "{self.expert.name}", "operation": "<op>", "parameters": {{...}}, "confidence": <0-1>, "reasoning": "<brief>"}}

If the query is NOT for this expert, respond:
{{"expert": "none", "operation": "passthrough", "parameters": {{}}, "confidence": 1.0, "reasoning": "<why not this expert>"}}

## Examples

{examples_text}
Query: "%s"
Action:"""

    def validate_single(
        self,
        query: str,
        expected_answer: Any,
        answer_checker: Callable[[Any, Any], bool] | None = None,
    ) -> ValidationResult:
        """
        Validate a single query.

        Args:
            query: The query to process
            expected_answer: Expected answer for correctness check
            answer_checker: Optional function to compare answers (default: equality)

        Returns:
            ValidationResult with all pipeline stages
        """
        result = ValidationResult(query=query, expected_answer=expected_answer)

        # 1. Generate with few-shot prompt
        prompt = self.prompt_template % query
        result.raw_output = self.generate(prompt, 500)

        if self.verbose:
            print(f"\nQuery: {query[:60]}...")
            print(f"Output: {result.raw_output[:200]}...")

        # 2. Parse JSON
        action = self._extract_action(result.raw_output)
        if action is None:
            result.parse_error = "no_json"
            return result

        result.parsed = True
        result.action = action

        # 3. Check routing
        if action.expert == "none" or action.is_passthrough():
            result.routed_to_expert = False
            return result

        if action.expert != self.expert.name:
            result.routed_to_expert = False
            result.parse_error = f"wrong_expert:{action.expert}"
            return result

        result.routed_to_expert = True

        # 4. Execute via expert
        try:
            exec_result = self.expert.execute(action)
            result.executed = True

            if not exec_result.success:
                result.exec_error = exec_result.error or "unknown"
                return result

            result.result_data = exec_result.data

        except Exception as e:
            result.exec_error = str(e)[:100]
            return result

        # 5. Check verification (if expert provides it)
        if result.result_data:
            result.verified = result.result_data.get("verified", True)
            result.answer = result.result_data.get("answer")

        # 6. Check correctness
        if result.answer is not None and expected_answer is not None:
            if answer_checker:
                result.correct = answer_checker(result.answer, expected_answer)
            else:
                result.correct = self._default_answer_check(result.answer, expected_answer)

        if self.verbose:
            status = "✓" if result.correct else f"✗ {result.error}"
            print(f"Status: {status}")

        return result

    def validate(
        self,
        queries: list[str],
        expected_answers: list[Any],
        answer_checker: Callable[[Any, Any], bool] | None = None,
    ) -> ValidationSummary:
        """
        Validate multiple queries.

        Args:
            queries: List of queries to process
            expected_answers: Expected answers for each query
            answer_checker: Optional function to compare answers

        Returns:
            ValidationSummary with aggregate metrics
        """
        summary = ValidationSummary()

        for query, expected in zip(queries, expected_answers, strict=True):
            result = self.validate_single(query, expected, answer_checker)
            summary.results.append(result)

            summary.total += 1
            if result.parsed:
                summary.parsed += 1
            if result.routed_to_expert:
                summary.routed += 1
            if result.executed:
                summary.executed += 1
            if result.verified:
                summary.verified += 1
            if result.correct:
                summary.correct += 1

            if result.error:
                summary.errors[result.error] = summary.errors.get(result.error, 0) + 1

        return summary

    def _extract_action(self, text: str) -> VirtualExpertAction | None:
        """Extract VirtualExpertAction from text."""
        try:
            start = text.find("{")
            if start == -1:
                return None

            depth = 0
            end = start
            in_string = False
            escape_next = False

            for i, char in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            json_str = text[start:end]
            data = json.loads(json_str)
            return VirtualExpertAction(**data)

        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def _default_answer_check(self, answer: Any, expected: Any) -> bool:
        """Default answer comparison with numeric tolerance."""
        try:
            # Try numeric comparison
            a = float(answer)
            e = float(expected)
            return abs(a - e) < 0.01
        except (ValueError, TypeError):
            # Fall back to string comparison
            return str(answer).strip() == str(expected).strip()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def validate_expert_few_shot(
    expert: VirtualExpert,
    generate_fn: Callable[[str, int], str],
    test_queries: list[str],
    expected_answers: list[Any],
    max_examples: int = 3,
    verbose: bool = False,
) -> ValidationSummary:
    """
    Convenience function to validate an expert with few-shot prompting.

    Args:
        expert: The virtual expert to validate
        generate_fn: Function that takes (prompt, max_tokens) and returns text
        test_queries: List of test queries
        expected_answers: Expected answers for each query
        max_examples: Number of few-shot examples
        verbose: Print detailed output

    Returns:
        ValidationSummary with metrics and guidance
    """
    validator = FewShotValidator(
        expert=expert,
        generate_fn=generate_fn,
        max_examples=max_examples,
        verbose=verbose,
    )
    return validator.validate(test_queries, expected_answers)
