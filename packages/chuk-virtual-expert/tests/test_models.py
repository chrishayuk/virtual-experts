"""Tests for Pydantic models."""

import json

import pytest
from pydantic import ValidationError

from chuk_virtual_expert.models import (
    NONE_EXPERT,
    CommonOperation,
    CoTExample,
    CoTExamples,
    DispatchResult,
    ExpertSchema,
    OperationSchema,
    ParameterSchema,
    VirtualExpertAction,
    VirtualExpertResult,
)


class TestCommonOperation:
    """Tests for CommonOperation enum."""

    def test_execute_value(self):
        assert CommonOperation.EXECUTE == "execute"
        assert CommonOperation.EXECUTE.value == "execute"

    def test_passthrough_value(self):
        assert CommonOperation.PASSTHROUGH == "passthrough"
        assert CommonOperation.PASSTHROUGH.value == "passthrough"

    def test_is_string_enum(self):
        assert isinstance(CommonOperation.EXECUTE, str)


class TestNoneExpert:
    """Tests for NONE_EXPERT constant."""

    def test_value(self):
        assert NONE_EXPERT == "none"


class TestVirtualExpertAction:
    """Tests for VirtualExpertAction model."""

    def test_basic_creation(self):
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
        )
        assert action.expert == "time"
        assert action.operation == "get_time"
        assert action.parameters == {}
        assert action.confidence == 1.0
        assert action.reasoning == ""

    def test_full_creation(self):
        action = VirtualExpertAction(
            expert="time",
            operation="convert_time",
            parameters={"from_tz": "EST", "to_tz": "PST"},
            confidence=0.95,
            reasoning="User wants timezone conversion",
        )
        assert action.parameters == {"from_tz": "EST", "to_tz": "PST"}
        assert action.confidence == 0.95
        assert action.reasoning == "User wants timezone conversion"

    def test_none_action_factory(self):
        action = VirtualExpertAction.none_action("Not handled")
        assert action.expert == NONE_EXPERT
        assert action.operation == CommonOperation.PASSTHROUGH
        assert action.confidence == 1.0
        assert action.reasoning == "Not handled"

    def test_none_action_without_reasoning(self):
        action = VirtualExpertAction.none_action()
        assert action.reasoning == ""

    def test_is_passthrough_with_none_expert(self):
        action = VirtualExpertAction(expert=NONE_EXPERT, operation="get_time")
        assert action.is_passthrough()

    def test_is_passthrough_with_passthrough_operation(self):
        action = VirtualExpertAction(
            expert="time",
            operation=CommonOperation.PASSTHROUGH,
        )
        assert action.is_passthrough()

    def test_is_not_passthrough(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        assert not action.is_passthrough()

    def test_confidence_validation_min(self):
        with pytest.raises(ValidationError):
            VirtualExpertAction(
                expert="time",
                operation="get_time",
                confidence=-0.1,
            )

    def test_confidence_validation_max(self):
        with pytest.raises(ValidationError):
            VirtualExpertAction(
                expert="time",
                operation="get_time",
                confidence=1.5,
            )

    def test_confidence_boundary_values(self):
        action_min = VirtualExpertAction(expert="time", operation="get_time", confidence=0.0)
        action_max = VirtualExpertAction(expert="time", operation="get_time", confidence=1.0)
        assert action_min.confidence == 0.0
        assert action_max.confidence == 1.0

    def test_json_serialization(self):
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"tz": "UTC"},
        )
        json_str = action.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["expert"] == "time"
        assert parsed["operation"] == "get_time"
        assert parsed["parameters"] == {"tz": "UTC"}


class TestVirtualExpertResult:
    """Tests for VirtualExpertResult model."""

    def test_basic_creation(self):
        result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
        )
        assert result.data == {"time": "12:00"}
        assert result.expert_name == "time"
        assert result.success is True
        assert result.error is None

    def test_error_result(self):
        result = VirtualExpertResult(
            data=None,
            expert_name="time",
            success=False,
            error="Connection failed",
        )
        assert result.success is False
        assert result.error == "Connection failed"

    def test_with_action(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
            action=action,
        )
        assert result.action == action

    def test_query_type_property(self):
        result = VirtualExpertResult(
            data={"query_type": "current_time", "time": "12:00"},
            expert_name="time",
        )
        assert result.query_type == "current_time"

    def test_query_type_missing(self):
        result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
        )
        assert result.query_type is None

    def test_query_type_no_data(self):
        result = VirtualExpertResult(
            data=None,
            expert_name="time",
        )
        assert result.query_type is None


class TestDispatchResult:
    """Tests for DispatchResult model."""

    def test_basic_creation(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        result = DispatchResult(action=action)
        assert result.action == action
        assert result.result is None

    def test_with_result(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        expert_result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
        )
        result = DispatchResult(action=action, result=expert_result)
        assert result.result == expert_result

    def test_was_handled_true(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        expert_result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
        )
        result = DispatchResult(action=action, result=expert_result)
        assert result.was_handled is True

    def test_was_handled_false_no_result(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        result = DispatchResult(action=action)
        assert result.was_handled is False

    def test_was_handled_false_passthrough(self):
        action = VirtualExpertAction.none_action()
        expert_result = VirtualExpertResult(
            data={"time": "12:00"},
            expert_name="time",
        )
        result = DispatchResult(action=action, result=expert_result)
        assert result.was_handled is False


class TestCoTExample:
    """Tests for CoTExample model."""

    def test_creation(self):
        action = VirtualExpertAction(expert="time", operation="get_time")
        example = CoTExample(query="What time is it?", action=action)
        assert example.query == "What time is it?"
        assert example.action == action

    def test_to_few_shot_format(self):
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            confidence=1.0,
        )
        example = CoTExample(query="What time is it?", action=action)
        output = example.to_few_shot_format()
        assert 'Query: "What time is it?"' in output
        assert "Action:" in output
        assert '"expert":"time"' in output or '"expert": "time"' in output


class TestCoTExamples:
    """Tests for CoTExamples model."""

    @pytest.fixture
    def sample_examples(self):
        return CoTExamples(
            expert_name="time",
            examples=[
                CoTExample(
                    query="What time is it?",
                    action=VirtualExpertAction(
                        expert="time",
                        operation="get_time",
                    ),
                ),
                CoTExample(
                    query="Time in Tokyo",
                    action=VirtualExpertAction(
                        expert="time",
                        operation="get_time",
                        parameters={"tz": "Asia/Tokyo"},
                    ),
                ),
                CoTExample(
                    query="Tell me a joke",
                    action=VirtualExpertAction.none_action(),
                ),
            ],
        )

    def test_creation(self, sample_examples):
        assert sample_examples.expert_name == "time"
        assert len(sample_examples.examples) == 3

    def test_get_few_shot_prompt(self, sample_examples):
        prompt = sample_examples.get_few_shot_prompt(max_examples=2)
        assert "What time is it?" in prompt
        assert "Time in Tokyo" in prompt
        assert "Tell me a joke" not in prompt  # Limited to 2

    def test_get_few_shot_prompt_all(self, sample_examples):
        prompt = sample_examples.get_few_shot_prompt(max_examples=10)
        assert "Tell me a joke" in prompt

    def test_positive_actions(self, sample_examples):
        positive = sample_examples.positive_actions
        assert len(positive) == 2
        for action_json in positive:
            parsed = json.loads(action_json)
            assert parsed["expert"] == "time"

    def test_negative_actions(self, sample_examples):
        negative = sample_examples.negative_actions
        assert len(negative) == 1
        for action_json in negative:
            parsed = json.loads(action_json)
            assert parsed["expert"] != "time"


class TestParameterSchema:
    """Tests for ParameterSchema model."""

    def test_basic_creation(self):
        param = ParameterSchema(
            type="string",
            description="The timezone",
        )
        assert param.type == "string"
        assert param.description == "The timezone"
        assert param.required is False
        assert param.default is None

    def test_required_with_default(self):
        param = ParameterSchema(
            type="string",
            description="The timezone",
            required=True,
            default="UTC",
        )
        assert param.required is True
        assert param.default == "UTC"

    def test_with_enum(self):
        param = ParameterSchema(
            type="string",
            description="Format",
            enum=["json", "text", "xml"],
        )
        assert param.enum == ["json", "text", "xml"]


class TestOperationSchema:
    """Tests for OperationSchema model."""

    def test_basic_creation(self):
        op = OperationSchema(
            name="get_time",
            description="Get current time",
        )
        assert op.name == "get_time"
        assert op.description == "Get current time"
        assert op.parameters == {}

    def test_with_parameters(self):
        op = OperationSchema(
            name="get_time",
            description="Get current time",
            parameters={
                "timezone": ParameterSchema(
                    type="string",
                    description="IANA timezone",
                )
            },
        )
        assert "timezone" in op.parameters


class TestExpertSchema:
    """Tests for ExpertSchema model."""

    def test_basic_creation(self):
        schema = ExpertSchema(
            name="time",
            description="Time operations",
        )
        assert schema.name == "time"
        assert schema.description == "Time operations"

    def test_with_operations(self):
        schema = ExpertSchema(
            name="time",
            description="Time operations",
            operations={
                "get_time": OperationSchema(
                    name="get_time",
                    description="Get current time",
                    parameters={
                        "timezone": ParameterSchema(
                            type="string",
                            description="IANA timezone",
                            required=False,
                        )
                    },
                )
            },
        )
        assert "get_time" in schema.operations

    def test_get_operations_summary(self):
        schema = ExpertSchema(
            name="time",
            description="Time operations",
            operations={
                "get_time": OperationSchema(
                    name="get_time",
                    description="Get current time",
                    parameters={
                        "timezone": ParameterSchema(
                            type="string",
                            description="IANA timezone",
                            required=True,
                        )
                    },
                )
            },
        )
        summary = schema.get_operations_summary()
        assert "get_time" in summary
        assert "timezone*" in summary  # Required params have *
        assert "Get current time" in summary
