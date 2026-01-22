"""Tests for VirtualExpert base class."""

import json
from pathlib import Path
from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import VirtualExpertAction


class MockExpert(VirtualExpert):
    """Concrete implementation for testing."""

    name: ClassVar[str] = "mock"
    description: ClassVar[str] = "A mock expert for testing"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 10

    def can_handle(self, prompt: str) -> bool:
        return "mock" in prompt.lower() or "echo" in prompt.lower()

    def get_operations(self) -> list[str]:
        return ["echo", "reverse", "fail"]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if operation == "echo":
            return {"result": parameters.get("message", "hello")}
        elif operation == "reverse":
            msg = parameters.get("message", "")
            return {"result": msg[::-1]}
        elif operation == "fail":
            raise ValueError("Intentional failure")
        else:
            raise ValueError(f"Unknown operation: {operation}")


class TestVirtualExpertClassAttributes:
    """Tests for class-level attributes."""

    def test_name(self):
        expert = MockExpert()
        assert expert.name == "mock"

    def test_description(self):
        expert = MockExpert()
        assert expert.description == "A mock expert for testing"

    def test_version(self):
        expert = MockExpert()
        assert expert.version == "1.0.0"

    def test_priority(self):
        expert = MockExpert()
        assert expert.priority == 10

    def test_cot_examples_file_default(self):
        expert = MockExpert()
        assert expert.cot_examples_file == "cot_examples.json"

    def test_schema_file_default(self):
        expert = MockExpert()
        assert expert.schema_file == "schema.json"


class TestGetOperations:
    """Tests for get_operations method."""

    def test_returns_list(self):
        expert = MockExpert()
        ops = expert.get_operations()
        assert isinstance(ops, list)

    def test_contains_expected_operations(self):
        expert = MockExpert()
        ops = expert.get_operations()
        assert "echo" in ops
        assert "reverse" in ops


class TestExecuteOperation:
    """Tests for execute_operation method."""

    def test_echo_operation(self):
        expert = MockExpert()
        result = expert.execute_operation("echo", {"message": "test"})
        assert result == {"result": "test"}

    def test_echo_default_message(self):
        expert = MockExpert()
        result = expert.execute_operation("echo", {})
        assert result == {"result": "hello"}

    def test_reverse_operation(self):
        expert = MockExpert()
        result = expert.execute_operation("reverse", {"message": "hello"})
        assert result == {"result": "olleh"}

    def test_unknown_operation_raises(self):
        expert = MockExpert()
        with pytest.raises(ValueError, match="Unknown operation"):
            expert.execute_operation("invalid", {})


class TestExecute:
    """Tests for execute method (main entry point)."""

    def test_successful_execution(self):
        expert = MockExpert()
        action = VirtualExpertAction(
            expert="mock",
            operation="echo",
            parameters={"message": "hello world"},
        )
        result = expert.execute(action)

        assert result.success is True
        assert result.data == {"result": "hello world"}
        assert result.expert_name == "mock"
        assert result.action == action
        assert result.error is None

    def test_failed_execution(self):
        expert = MockExpert()
        action = VirtualExpertAction(
            expert="mock",
            operation="fail",
        )
        result = expert.execute(action)

        assert result.success is False
        assert result.data is None
        assert result.error == "Intentional failure"
        assert result.expert_name == "mock"

    def test_returns_virtualexpertresult(self):
        from chuk_virtual_expert.models import VirtualExpertResult

        expert = MockExpert()
        action = VirtualExpertAction(expert="mock", operation="echo")
        result = expert.execute(action)
        assert isinstance(result, VirtualExpertResult)


class TestExecuteAsync:
    """Tests for execute_async method (async entry point)."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        expert = MockExpert()
        action = VirtualExpertAction(
            expert="mock",
            operation="echo",
            parameters={"message": "hello async"},
        )
        result = await expert.execute_async(action)

        assert result.success is True
        assert result.data == {"result": "hello async"}
        assert result.expert_name == "mock"
        assert result.action == action
        assert result.error is None

    @pytest.mark.asyncio
    async def test_failed_execution(self):
        expert = MockExpert()
        action = VirtualExpertAction(
            expert="mock",
            operation="fail",
        )
        result = await expert.execute_async(action)

        assert result.success is False
        assert result.data is None
        assert result.error == "Intentional failure"
        assert result.expert_name == "mock"

    @pytest.mark.asyncio
    async def test_returns_virtualexpertresult(self):
        from chuk_virtual_expert.models import VirtualExpertResult

        expert = MockExpert()
        action = VirtualExpertAction(expert="mock", operation="echo")
        result = await expert.execute_async(action)
        assert isinstance(result, VirtualExpertResult)


class TestExecuteOperationAsync:
    """Tests for execute_operation_async method."""

    @pytest.mark.asyncio
    async def test_echo_operation(self):
        expert = MockExpert()
        result = await expert.execute_operation_async("echo", {"message": "test"})
        assert result == {"result": "test"}

    @pytest.mark.asyncio
    async def test_reverse_operation(self):
        expert = MockExpert()
        result = await expert.execute_operation_async("reverse", {"message": "hello"})
        assert result == {"result": "olleh"}

    @pytest.mark.asyncio
    async def test_unknown_operation_raises(self):
        expert = MockExpert()
        with pytest.raises(ValueError, match="Unknown operation"):
            await expert.execute_operation_async("invalid", {})


class TestGetCotExamples:
    """Tests for get_cot_examples method."""

    def test_returns_empty_when_no_file(self):
        expert = MockExpert()
        examples = expert.get_cot_examples()
        assert examples.expert_name == "mock"
        assert len(examples.examples) == 0

    def test_caching(self):
        expert = MockExpert()
        examples1 = expert.get_cot_examples()
        examples2 = expert.get_cot_examples()
        assert examples1 is examples2


class TestGetSchema:
    """Tests for get_schema method."""

    def test_returns_default_when_no_file(self):
        expert = MockExpert()
        schema = expert.get_schema()
        assert schema.name == "mock"
        assert schema.description == "A mock expert for testing"

    def test_caching(self):
        expert = MockExpert()
        schema1 = expert.get_schema()
        schema2 = expert.get_schema()
        assert schema1 is schema2


class TestGetCalibrationData:
    """Tests for get_calibration_data method."""

    def test_returns_tuple(self):
        expert = MockExpert()
        result = expert.get_calibration_data()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_lists(self):
        expert = MockExpert()
        positive, negative = expert.get_calibration_data()
        assert isinstance(positive, list)
        assert isinstance(negative, list)


class TestGetFewShotPrompt:
    """Tests for get_few_shot_prompt method."""

    def test_returns_string(self):
        expert = MockExpert()
        prompt = expert.get_few_shot_prompt()
        assert isinstance(prompt, str)

    def test_respects_max_examples(self):
        expert = MockExpert()
        prompt = expert.get_few_shot_prompt(max_examples=3)
        # With no examples, should return empty string
        assert prompt == ""


class TestRepr:
    """Tests for __repr__ method."""

    def test_repr_format(self):
        expert = MockExpert()
        repr_str = repr(expert)
        assert "MockExpert" in repr_str
        assert "mock" in repr_str


class TestLoadCotExamplesFromFile:
    """Tests for loading CoT examples from actual file."""

    def test_loads_from_file(self, tmp_path):
        # Create a temporary expert with examples file
        examples_data = {
            "expert_name": "test",
            "examples": [
                {
                    "query": "Test query",
                    "action": {
                        "expert": "test",
                        "operation": "test_op",
                        "parameters": {},
                        "confidence": 1.0,
                        "reasoning": "Test reasoning",
                    },
                }
            ],
        }

        # Write examples file
        examples_file = tmp_path / "cot_examples.json"
        with open(examples_file, "w") as f:
            json.dump(examples_data, f)

        # Create expert that uses this directory
        class TmpExpert(VirtualExpert):
            name: ClassVar[str] = "test"
            description: ClassVar[str] = "Test"

            def _get_package_dir(self) -> Path:
                return tmp_path

            def can_handle(self, prompt: str) -> bool:
                return "test" in prompt.lower()

            def get_operations(self) -> list[str]:
                return ["test_op"]

            def execute_operation(self, op: str, params: dict) -> dict:
                return {}

        expert = TmpExpert()
        examples = expert.get_cot_examples()

        assert len(examples.examples) == 1
        assert examples.examples[0].query == "Test query"
        assert examples.examples[0].action.expert == "test"


class TestLoadSchemaFromFile:
    """Tests for loading schema from actual file."""

    def test_loads_from_file(self, tmp_path):
        schema_data = {
            "name": "test",
            "description": "Test expert",
            "operations": {
                "test_op": {
                    "description": "A test operation",
                    "parameters": {
                        "param1": {
                            "type": "string",
                            "description": "First param",
                            "required": True,
                        }
                    },
                }
            },
        }

        # Write schema file
        schema_file = tmp_path / "schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        class TmpExpert(VirtualExpert):
            name: ClassVar[str] = "test"
            description: ClassVar[str] = "Test"

            def _get_package_dir(self) -> Path:
                return tmp_path

            def can_handle(self, prompt: str) -> bool:
                return "test" in prompt.lower()

            def get_operations(self) -> list[str]:
                return ["test_op"]

            def execute_operation(self, op: str, params: dict) -> dict:
                return {}

        expert = TmpExpert()
        schema = expert.get_schema()

        assert schema.name == "test"
        assert "test_op" in schema.operations
        assert schema.operations["test_op"].description == "A test operation"
        assert "param1" in schema.operations["test_op"].parameters
