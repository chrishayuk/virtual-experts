"""Tests for validation module."""

from typing import Any, ClassVar
from unittest.mock import Mock

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import CoTExample, CoTExamples, VirtualExpertAction
from chuk_virtual_expert.validation import (
    FewShotValidator,
    ValidationResult,
    ValidationSummary,
    validate_expert_few_shot,
)


class MockValidationExpert(VirtualExpert):
    """Mock expert for validation testing."""

    name: ClassVar[str] = "test"
    description: ClassVar[str] = "Test expert for validation"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 5

    def can_handle(self, prompt: str) -> bool:
        return "test" in prompt.lower()

    def get_operations(self) -> list[str]:
        return ["calculate"]

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        if op == "calculate":
            a = params.get("a", 0)
            b = params.get("b", 0)
            return {"answer": a + b, "verified": True}
        raise ValueError(f"Unknown operation: {op}")

    def get_cot_examples(self) -> CoTExamples:
        return CoTExamples(
            expert_name="test",
            examples=[
                CoTExample(
                    query="Add 1 and 2",
                    action=VirtualExpertAction(
                        expert="test",
                        operation="calculate",
                        parameters={"a": 1, "b": 2},
                    ),
                )
            ],
        )


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_basic_creation(self):
        result = ValidationResult(query="test", expected_answer=42)
        assert result.query == "test"
        assert result.expected_answer == 42

    def test_error_parse_error(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parse_error = "no_json"
        assert result.error == "parse:no_json"

    def test_error_not_routed(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parsed = True
        result.routed_to_expert = False
        assert result.error == "not_routed"

    def test_error_exec_error(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parsed = True
        result.routed_to_expert = True
        result.exec_error = "failed"
        assert result.error == "exec:failed"

    def test_error_invalid_trace(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parsed = True
        result.routed_to_expert = True
        result.executed = True
        result.verified = False
        assert result.error == "invalid_trace"

    def test_error_wrong_answer(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parsed = True
        result.routed_to_expert = True
        result.executed = True
        result.verified = True
        result.correct = False
        result.answer = 99
        assert result.error == "wrong:99"

    def test_no_error(self):
        result = ValidationResult(query="test", expected_answer=42)
        result.parsed = True
        result.routed_to_expert = True
        result.executed = True
        result.verified = True
        result.correct = True
        assert result.error is None


class TestValidationSummary:
    """Tests for ValidationSummary."""

    def test_basic_creation(self):
        summary = ValidationSummary()
        assert summary.total == 0
        assert summary.parsed == 0

    def test_rates_with_zero_total(self):
        summary = ValidationSummary()
        assert summary.parse_rate == 0
        assert summary.route_rate == 0
        assert summary.exec_rate == 0
        assert summary.valid_rate == 0
        assert summary.accuracy == 0

    def test_rates_with_data(self):
        summary = ValidationSummary(
            total=10,
            parsed=8,
            routed=7,
            executed=6,
            verified=5,
            correct=4,
        )
        assert summary.parse_rate == 0.8
        assert summary.route_rate == 0.7
        assert summary.exec_rate == 0.6
        assert summary.valid_rate == 0.5
        assert summary.accuracy == 0.4

    def test_print_summary_low_parse_rate(self, capsys):
        summary = ValidationSummary(total=10, parsed=3, routed=2, executed=1, verified=1, correct=0)
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Parse rate <50%" in captured.out

    def test_print_summary_low_valid_rate(self, capsys):
        summary = ValidationSummary(total=10, parsed=8, routed=7, executed=6, verified=3, correct=1)
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Valid rate <50%" in captured.out

    def test_print_summary_low_accuracy(self, capsys):
        summary = ValidationSummary(total=10, parsed=9, routed=8, executed=7, verified=6, correct=2)
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Fine-tuning will help" in captured.out

    def test_print_summary_medium_accuracy(self, capsys):
        summary = ValidationSummary(
            total=10, parsed=10, routed=10, executed=10, verified=10, correct=5
        )
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Few-shot shows promise" in captured.out

    def test_print_summary_good_accuracy(self, capsys):
        summary = ValidationSummary(
            total=10, parsed=10, routed=10, executed=10, verified=10, correct=7
        )
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Few-shot works well" in captured.out

    def test_print_summary_excellent_accuracy(self, capsys):
        summary = ValidationSummary(
            total=10, parsed=10, routed=10, executed=10, verified=10, correct=9
        )
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Few-shot is sufficient" in captured.out

    def test_print_summary_with_errors(self, capsys):
        summary = ValidationSummary(
            total=10,
            parsed=10,
            routed=10,
            executed=10,
            verified=10,
            correct=10,
            errors={"parse:no_json": 2, "exec:failed": 1},
        )
        summary.print_summary()
        captured = capsys.readouterr()
        assert "Error breakdown" in captured.out
        assert "parse:no_json" in captured.out


class TestFewShotValidator:
    """Tests for FewShotValidator."""

    def test_creation(self):
        expert = MockValidationExpert()
        generate_fn = Mock(
            return_value='{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}}'
        )
        validator = FewShotValidator(expert, generate_fn)
        assert validator.expert == expert
        assert validator.max_examples == 3

    def test_validate_single_success(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}, "confidence": 1.0}'

        validator = FewShotValidator(expert, mock_generate)
        result = validator.validate_single("Add 1 and 2", 3)

        assert result.parsed is True
        assert result.routed_to_expert is True
        assert result.executed is True
        assert result.answer == 3
        assert result.correct is True

    def test_validate_single_no_json(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return "I don't understand"

        validator = FewShotValidator(expert, mock_generate)
        result = validator.validate_single("Add 1 and 2", 3)

        assert result.parsed is False
        assert result.parse_error == "no_json"

    def test_validate_single_passthrough(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "none", "operation": "passthrough", "parameters": {}}'

        validator = FewShotValidator(expert, mock_generate)
        result = validator.validate_single("Hello", None)

        assert result.parsed is True
        assert result.routed_to_expert is False

    def test_validate_single_wrong_expert(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "other", "operation": "do_something", "parameters": {}}'

        validator = FewShotValidator(expert, mock_generate)
        result = validator.validate_single("Test query", 42)

        assert result.parsed is True
        assert result.routed_to_expert is False
        assert "wrong_expert" in result.parse_error

    def test_validate_single_execution_error(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "invalid_op", "parameters": {}}'

        validator = FewShotValidator(expert, mock_generate)
        result = validator.validate_single("Test", 42)

        assert result.parsed is True
        assert result.routed_to_expert is True
        assert result.exec_error is not None

    def test_validate_single_verbose(self, capsys):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}}'

        validator = FewShotValidator(expert, mock_generate, verbose=True)
        _result = validator.validate_single("Add 1 and 2", 3)

        captured = capsys.readouterr()
        assert "Query:" in captured.out
        assert "Output:" in captured.out
        assert "Status:" in captured.out

    def test_validate_multiple(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}}'

        validator = FewShotValidator(expert, mock_generate)
        summary = validator.validate(
            ["Add 1 and 2", "Another test"],
            [3, 3],
        )

        assert summary.total == 2
        assert summary.parsed == 2

    def test_extract_action_complex_json(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        # Test with nested braces in strings
        text = 'Some text {"expert": "test", "operation": "op", "parameters": {"nested": "}"}} more text'
        action = validator._extract_action(text)
        assert action is not None
        assert action.expert == "test"

    def test_default_answer_check_numeric(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        assert validator._default_answer_check(3.0, 3.0) is True
        assert validator._default_answer_check(3.005, 3.0) is True
        assert validator._default_answer_check(3.5, 3.0) is False

    def test_default_answer_check_string(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        assert validator._default_answer_check("hello", "hello") is True
        assert validator._default_answer_check("hello ", "hello") is True
        assert validator._default_answer_check("hello", "world") is False

    def test_custom_answer_checker(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}}'

        validator = FewShotValidator(expert, mock_generate)

        def custom_checker(answer: Any, expected: Any) -> bool:
            return answer >= expected

        result = validator.validate_single("Add", 2, answer_checker=custom_checker)
        assert result.correct is True


class TestValidateExpertFewShot:
    """Tests for validate_expert_few_shot convenience function."""

    def test_basic_usage(self):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return '{"expert": "test", "operation": "calculate", "parameters": {"a": 1, "b": 2}}'

        summary = validate_expert_few_shot(
            expert=expert,
            generate_fn=mock_generate,
            test_queries=["Add 1 and 2"],
            expected_answers=[3],
        )

        assert summary.total == 1
        assert summary.parsed == 1


class TestValidationResultVerboseOutput:
    """Tests for verbose mode output in validation."""

    def test_verbose_failure_output(self, capsys):
        expert = MockValidationExpert()

        def mock_generate(prompt: str, max_tokens: int) -> str:
            return "invalid json"

        validator = FewShotValidator(expert, mock_generate, verbose=True)
        _result = validator.validate_single("Test", 42)

        captured = capsys.readouterr()
        assert "Query:" in captured.out


class TestExtractActionEdgeCases:
    """Tests for _extract_action edge cases."""

    def test_invalid_json(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        result = validator._extract_action("{invalid json}")
        assert result is None

    def test_missing_required_fields(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        # Valid JSON but missing required fields for VirtualExpertAction
        # Pydantic raises ValidationError which is now caught
        result = validator._extract_action('{"foo": "bar"}')
        assert result is None

    def test_escaped_quotes(self):
        expert = MockValidationExpert()
        validator = FewShotValidator(expert, lambda p, m: "")

        text = '{"expert": "test", "operation": "op", "parameters": {"msg": "hello \\"world\\""}, "confidence": 1.0}'
        result = validator._extract_action(text)
        assert result is not None


class TestValidationSummaryErrorTracking:
    """Tests for error tracking in ValidationSummary."""

    def test_error_accumulation(self):
        expert = MockValidationExpert()

        call_count = 0

        def mock_generate(prompt: str, max_tokens: int) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "no json"
            return '{"expert": "none", "operation": "passthrough", "parameters": {}}'

        validator = FewShotValidator(expert, mock_generate)
        summary = validator.validate(["q1", "q2"], [1, 2])

        assert summary.total == 2
        assert "parse:no_json" in summary.errors
        assert "not_routed" in summary.errors
