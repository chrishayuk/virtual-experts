"""Tests for Dispatcher and action extraction."""

from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.dispatch import (
    CalibrationData,
    Dispatcher,
    FewShotExtractor,
)
from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import VirtualExpertAction
from chuk_virtual_expert.registry_v2 import ExpertRegistry


class MockExpert(VirtualExpert):
    """Mock expert for testing dispatch."""

    name: ClassVar[str] = "mock"
    description: ClassVar[str] = "Mock expert for testing"
    priority: ClassVar[int] = 5

    def can_handle(self, prompt: str) -> bool:
        return "mock" in prompt.lower() or "echo" in prompt.lower()

    def get_operations(self) -> list[str]:
        return ["echo"]

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"message": params.get("text", "hello")}


class MockExtractor:
    """Mock extractor that returns predefined actions."""

    def __init__(self, action: VirtualExpertAction | None = None):
        self._action = action or VirtualExpertAction.none_action()

    def extract(self, query: str, available_experts: list[str]) -> VirtualExpertAction:
        return self._action


class TestFewShotExtractor:
    """Tests for FewShotExtractor."""

    @pytest.fixture
    def extractor(self):
        return FewShotExtractor(
            experts={"mock": MockExpert()},
            max_examples_per_expert=3,
        )

    def test_creation(self, extractor):
        assert isinstance(extractor, FewShotExtractor)
        assert extractor.max_examples_per_expert == 3

    def test_get_prompt_includes_query(self, extractor):
        prompt = extractor.get_prompt("Test query")
        assert "Test query" in prompt

    def test_get_prompt_includes_expert_info(self, extractor):
        prompt = extractor.get_prompt("Test query")
        assert "mock" in prompt
        assert "Mock expert" in prompt

    def test_get_prompt_includes_output_format(self, extractor):
        prompt = extractor.get_prompt("Test query")
        assert '"expert"' in prompt
        assert '"operation"' in prompt
        assert '"parameters"' in prompt

    def test_get_prompt_structure(self, extractor):
        prompt = extractor.get_prompt("Test query")
        assert "## Available Experts" in prompt
        assert "## Output Format" in prompt
        assert "## Query" in prompt


class TestFewShotExtractorParseResponse:
    """Tests for FewShotExtractor.parse_response method."""

    @pytest.fixture
    def extractor(self):
        return FewShotExtractor()

    def test_parse_valid_json(self, extractor):
        response = '{"expert": "time", "operation": "get_time", "parameters": {}}'
        action = extractor.parse_response(response)
        assert action.expert == "time"
        assert action.operation == "get_time"

    def test_parse_json_with_surrounding_text(self, extractor):
        response = 'Here is the action: {"expert": "time", "operation": "get"} done.'
        action = extractor.parse_response(response)
        assert action.expert == "time"

    def test_parse_json_with_nested_objects(self, extractor):
        response = (
            '{"expert": "time", "operation": "convert", "parameters": {"from": "EST", "to": "PST"}}'
        )
        action = extractor.parse_response(response)
        assert action.parameters == {"from": "EST", "to": "PST"}

    def test_parse_no_json_returns_none_action(self, extractor):
        response = "I cannot find any JSON here"
        action = extractor.parse_response(response)
        assert action.is_passthrough()
        assert "No JSON" in action.reasoning

    def test_parse_invalid_json_returns_none_action(self, extractor):
        response = '{"expert": "time", "operation": '  # incomplete
        action = extractor.parse_response(response)
        assert action.is_passthrough()

    def test_parse_with_string_containing_braces(self, extractor):
        response = (
            '{"expert": "time", "operation": "get_time", "reasoning": "Use { or } carefully"}'
        )
        action = extractor.parse_response(response)
        assert action.expert == "time"

    def test_parse_with_escaped_quotes(self, extractor):
        response = '{"expert": "time", "operation": "get_time", "reasoning": "He said \\"hello\\""}'
        action = extractor.parse_response(response)
        assert action.expert == "time"


class TestDispatcher:
    """Tests for Dispatcher class."""

    @pytest.fixture
    def registry(self):
        reg = ExpertRegistry()
        reg.register(MockExpert())
        return reg

    @pytest.fixture
    def dispatcher(self, registry):
        return Dispatcher(registry=registry)

    def test_creation(self, dispatcher):
        assert isinstance(dispatcher, Dispatcher)
        assert dispatcher.extractor is None

    def test_set_extractor(self, dispatcher):
        extractor = MockExtractor()
        dispatcher.set_extractor(extractor)
        assert dispatcher.extractor is extractor

    def test_dispatch_without_extractor_raises(self, dispatcher):
        with pytest.raises(ValueError, match="No extractor set"):
            dispatcher.dispatch("test query")

    def test_dispatch_with_extractor(self, dispatcher):
        action = VirtualExpertAction(
            expert="mock",
            operation="echo",
            parameters={"text": "hello"},
        )
        dispatcher.set_extractor(MockExtractor(action))

        result = dispatcher.dispatch("test query")

        assert result.action == action
        assert result.result is not None
        assert result.result.success

    def test_dispatch_passthrough(self, dispatcher):
        action = VirtualExpertAction.none_action("Not handled")
        dispatcher.set_extractor(MockExtractor(action))

        result = dispatcher.dispatch("test query")

        assert result.action == action
        assert result.result is None
        assert not result.was_handled


class TestDispatchAction:
    """Tests for Dispatcher.dispatch_action method."""

    @pytest.fixture
    def registry(self):
        reg = ExpertRegistry()
        reg.register(MockExpert())
        return reg

    @pytest.fixture
    def dispatcher(self, registry):
        return Dispatcher(registry=registry)

    def test_dispatch_action_success(self, dispatcher):
        action = VirtualExpertAction(
            expert="mock",
            operation="echo",
            parameters={"text": "test"},
        )
        result = dispatcher.dispatch_action(action)

        assert result.action == action
        assert result.result is not None
        assert result.result.data == {"message": "test"}
        assert result.was_handled

    def test_dispatch_action_passthrough(self, dispatcher):
        action = VirtualExpertAction.none_action()
        result = dispatcher.dispatch_action(action)

        assert result.action == action
        assert result.result is None
        assert not result.was_handled

    def test_dispatch_action_unknown_expert(self, dispatcher):
        action = VirtualExpertAction(
            expert="unknown",
            operation="something",
        )
        result = dispatcher.dispatch_action(action)

        assert result.action == action
        assert result.result is None  # Expert not found


class TestCalibrationData:
    """Tests for CalibrationData model."""

    def test_creation(self):
        data = CalibrationData(
            expert_name="time",
            positive_actions=['{"expert": "time"}'],
            negative_actions=['{"expert": "none"}'],
        )
        assert data.expert_name == "time"
        assert len(data.positive_actions) == 1
        assert len(data.negative_actions) == 1

    def test_from_expert(self):
        expert = MockExpert()
        data = CalibrationData.from_expert(expert)

        assert data.expert_name == "mock"
        assert isinstance(data.positive_actions, list)
        assert isinstance(data.negative_actions, list)
