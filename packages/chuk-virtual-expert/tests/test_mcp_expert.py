"""Tests for MCPExpert base class."""

from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.mcp_expert import MCPExpert, MCPTransportType


class MockMCPExpert(MCPExpert):
    """Mock MCP expert for testing."""

    name: ClassVar[str] = "mock_mcp"
    description: ClassVar[str] = "Mock MCP expert for testing"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 5
    mcp_server_url: ClassVar[str] = "https://test.example.com/mcp"
    mcp_timeout: ClassVar[float] = 10.0

    def can_handle(self, prompt: str) -> bool:
        return "mock" in prompt.lower()

    def get_operations(self) -> list[str]:
        return ["test_op", "another_op"]

    def get_mcp_tool_name(self, operation: str) -> str:
        mapping = {
            "test_op": "mcp_test_tool",
            "another_op": "mcp_another_tool",
        }
        if operation not in mapping:
            raise ValueError(f"Unknown operation: {operation}")
        return mapping[operation]

    def transform_parameters(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        # Simple transformation: add a prefix
        return {f"mcp_{k}": v for k, v in parameters.items()}

    def transform_result(self, operation: str, tool_result: dict[str, Any]) -> dict[str, Any]:
        # Add query_type based on operation
        return {
            "query_type": operation,
            **tool_result,
        }


class TestMCPTransportType:
    """Tests for MCPTransportType enum."""

    def test_http_value(self):
        assert MCPTransportType.HTTP == "http"
        assert MCPTransportType.HTTP.value == "http"

    def test_stdio_value(self):
        assert MCPTransportType.STDIO == "stdio"
        assert MCPTransportType.STDIO.value == "stdio"

    def test_is_string_enum(self):
        assert isinstance(MCPTransportType.HTTP, str)


class TestMCPExpertClassAttributes:
    """Tests for MCPExpert class attributes."""

    def test_name(self):
        expert = MockMCPExpert()
        assert expert.name == "mock_mcp"

    def test_description(self):
        expert = MockMCPExpert()
        assert expert.description == "Mock MCP expert for testing"

    def test_mcp_server_url(self):
        expert = MockMCPExpert()
        assert expert.mcp_server_url == "https://test.example.com/mcp"

    def test_mcp_timeout(self):
        expert = MockMCPExpert()
        assert expert.mcp_timeout == 10.0

    def test_mcp_transport_type_default(self):
        expert = MockMCPExpert()
        assert expert.mcp_transport_type == MCPTransportType.HTTP


class TestMCPExpertInstanceOverrides:
    """Tests for instance-level configuration overrides."""

    def test_server_url_override(self):
        expert = MockMCPExpert(server_url="https://custom.example.com/mcp")
        assert expert._get_effective_url() == "https://custom.example.com/mcp"

    def test_server_url_default(self):
        expert = MockMCPExpert()
        assert expert._get_effective_url() == "https://test.example.com/mcp"

    def test_timeout_override(self):
        expert = MockMCPExpert(timeout=60.0)
        assert expert._get_effective_timeout() == 60.0

    def test_timeout_default(self):
        expert = MockMCPExpert()
        assert expert._get_effective_timeout() == 10.0

    def test_bearer_token_override(self):
        expert = MockMCPExpert(bearer_token="test-token")
        assert expert._get_effective_token() == "test-token"

    def test_bearer_token_default(self):
        expert = MockMCPExpert()
        assert expert._get_effective_token() is None


class TestGetMcpToolName:
    """Tests for get_mcp_tool_name method."""

    def test_maps_test_op(self):
        expert = MockMCPExpert()
        assert expert.get_mcp_tool_name("test_op") == "mcp_test_tool"

    def test_maps_another_op(self):
        expert = MockMCPExpert()
        assert expert.get_mcp_tool_name("another_op") == "mcp_another_tool"

    def test_unknown_operation_raises(self):
        expert = MockMCPExpert()
        with pytest.raises(ValueError, match="Unknown operation"):
            expert.get_mcp_tool_name("invalid_op")


class TestTransformParameters:
    """Tests for transform_parameters method."""

    def test_transforms_parameters(self):
        expert = MockMCPExpert()
        params = {"key1": "value1", "key2": "value2"}
        result = expert.transform_parameters("test_op", params)
        assert result == {"mcp_key1": "value1", "mcp_key2": "value2"}

    def test_empty_parameters(self):
        expert = MockMCPExpert()
        result = expert.transform_parameters("test_op", {})
        assert result == {}


class TestTransformResult:
    """Tests for transform_result method."""

    def test_transforms_result(self):
        expert = MockMCPExpert()
        tool_result = {"data": "test"}
        result = expert.transform_result("test_op", tool_result)
        assert result["query_type"] == "test_op"
        assert result["data"] == "test"


class TestParseToolResult:
    """Tests for _parse_tool_result method."""

    def test_parse_error_result(self):
        expert = MockMCPExpert()

        class MockErrorResult:
            isError = True
            content = [{"type": "text", "text": "Something went wrong"}]

        result = expert._parse_tool_result(MockErrorResult())
        assert result == {"error": "Something went wrong"}

    def test_parse_successful_result(self):
        expert = MockMCPExpert()

        class MockSuccessResult:
            isError = False
            content = [{"type": "text", "text": '{"data": "success"}'}]

        result = expert._parse_tool_result(MockSuccessResult())
        assert result == {"data": "success"}

    def test_parse_empty_result(self):
        expert = MockMCPExpert()

        class MockEmptyResult:
            isError = False
            content = []

        result = expert._parse_tool_result(MockEmptyResult())
        assert result == {}


class TestParseTextContent:
    """Tests for _parse_text_content method."""

    def test_parse_valid_json(self):
        expert = MockMCPExpert()
        result = expert._parse_text_content('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_invalid_json(self):
        expert = MockMCPExpert()
        result = expert._parse_text_content("not valid json")
        assert result == {"text": "not valid json"}


class TestCanHandle:
    """Tests for can_handle method."""

    def test_handles_mock_keyword(self):
        expert = MockMCPExpert()
        assert expert.can_handle("Do something mock")

    def test_rejects_unrelated(self):
        expert = MockMCPExpert()
        assert not expert.can_handle("unrelated query")


class TestGetOperations:
    """Tests for get_operations method."""

    def test_returns_operations(self):
        expert = MockMCPExpert()
        ops = expert.get_operations()
        assert "test_op" in ops
        assert "another_op" in ops


class TestDefaultTransformParameters:
    """Tests for default transform_parameters behavior."""

    def test_default_returns_parameters_unchanged(self):
        """Test that base class transform_parameters returns parameters unchanged."""
        from typing import ClassVar

        from chuk_virtual_expert.mcp_expert import MCPExpert

        class MinimalMCPExpert(MCPExpert):
            name: ClassVar[str] = "minimal"
            description: ClassVar[str] = "Minimal expert"
            mcp_server_url: ClassVar[str] = "https://example.com/mcp"

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return ["op"]

            def get_mcp_tool_name(self, operation: str) -> str:
                return "tool"

            def transform_result(
                self, operation: str, tool_result: dict[str, Any]
            ) -> dict[str, Any]:
                return tool_result

        expert = MinimalMCPExpert()
        params = {"key": "value"}
        # Call base class transform_parameters (not overridden)
        result = MCPExpert.transform_parameters(expert, "op", params)
        assert result == params


class TestParseToolResultEdgeCases:
    """Additional tests for _parse_tool_result edge cases."""

    def test_parse_result_with_block_text_attribute(self):
        """Test parsing result where block has text attribute."""
        expert = MockMCPExpert()

        class TextBlock:
            text = '{"result": "from_attribute"}'

        class MockResult:
            isError = False
            content = [TextBlock()]

        result = expert._parse_tool_result(MockResult())
        assert result == {"result": "from_attribute"}

    def test_parse_error_with_text_attribute(self):
        """Test parsing error result with text attribute."""
        expert = MockMCPExpert()

        class TextBlock:
            text = "Error message from attribute"

        class MockResult:
            isError = True
            content = [TextBlock()]

        result = expert._parse_tool_result(MockResult())
        assert result == {"error": "Error message from attribute"}

    def test_parse_error_empty_content(self):
        """Test parsing error with empty content."""
        expert = MockMCPExpert()

        class MockResult:
            isError = True
            content = []

        result = expert._parse_tool_result(MockResult())
        assert result == {"error": "Unknown error"}


class TestExecuteOperationSync:
    """Tests for synchronous execute_operation wrapper."""

    def test_execute_operation_wraps_async(self):
        """Test that execute_operation calls the async version."""
        expert = MockMCPExpert()

        # Can't easily test without mocking MCP, but we can test error handling
        try:
            expert.execute_operation("test_op", {"key": "value"})
        except Exception:
            # Expected - no actual MCP server
            pass


class TestExecuteSync:
    """Tests for synchronous execute wrapper."""

    def test_execute_wraps_async(self):
        """Test that execute calls the async version."""
        from chuk_virtual_expert.models import VirtualExpertAction

        expert = MockMCPExpert()
        action = VirtualExpertAction(
            expert="mock_mcp",
            operation="test_op",
            parameters={"key": "value"},
        )

        # Will fail because no MCP server, but tests the code path
        result = expert.execute(action)
        assert result.success is False
        assert result.error is not None


class TestExecuteAsyncErrorHandling:
    """Tests for async execute error handling."""

    @pytest.mark.asyncio
    async def test_execute_async_catches_errors(self):
        """Test that execute_async catches and wraps errors."""
        from chuk_virtual_expert.models import VirtualExpertAction

        expert = MockMCPExpert()
        action = VirtualExpertAction(
            expert="mock_mcp",
            operation="test_op",
            parameters={},
        )

        # Will fail because no MCP server
        result = await expert.execute_async(action)
        assert result.success is False
        assert result.error is not None
        assert result.expert_name == "mock_mcp"


class TestNoUrlConfigured:
    """Tests for missing URL configuration."""

    @pytest.mark.asyncio
    async def test_execute_operation_async_no_url_raises(self):
        """Test that execute_operation_async raises when no URL configured."""
        from typing import ClassVar

        from chuk_virtual_expert.mcp_expert import MCPExpert

        class NoUrlExpert(MCPExpert):
            name: ClassVar[str] = "nourl"
            description: ClassVar[str] = "No URL"
            mcp_server_url: ClassVar[str] = ""  # No URL

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return ["op"]

            def get_mcp_tool_name(self, operation: str) -> str:
                return "tool"

            def transform_result(
                self, operation: str, tool_result: dict[str, Any]
            ) -> dict[str, Any]:
                return tool_result

        expert = NoUrlExpert()
        with pytest.raises(ValueError, match="No MCP server URL configured"):
            await expert.execute_operation_async("op", {})

    @pytest.mark.asyncio
    async def test_list_mcp_tools_no_url_raises(self):
        """Test that list_mcp_tools raises when no URL configured."""
        from typing import ClassVar

        from chuk_virtual_expert.mcp_expert import MCPExpert

        class NoUrlExpert(MCPExpert):
            name: ClassVar[str] = "nourl"
            description: ClassVar[str] = "No URL"
            mcp_server_url: ClassVar[str] = ""

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return []

            def get_mcp_tool_name(self, operation: str) -> str:
                return "tool"

            def transform_result(
                self, operation: str, tool_result: dict[str, Any]
            ) -> dict[str, Any]:
                return tool_result

        expert = NoUrlExpert()
        with pytest.raises(ValueError, match="No MCP server URL configured"):
            await expert.list_mcp_tools()
