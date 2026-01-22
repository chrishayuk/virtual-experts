"""
Base class for MCP-backed virtual experts.

Async-native, Pydantic-based expert that delegates to an MCP server.
Uses the chuk-mcp client library for protocol handling.
No magic strings - uses typed models and enums throughout.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar

from pydantic import Field

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import VirtualExpertAction, VirtualExpertResult


class MCPTransportType(str, Enum):
    """Supported MCP transport types."""

    HTTP = "http"
    STDIO = "stdio"


class MCPExpert(VirtualExpert):
    """
    Base class for virtual experts backed by MCP servers.

    Provides async-native MCP communication using the chuk-mcp client library.
    Subclasses define operation-to-tool mapping and result transformation.

    Example:
        class TimeExpert(MCPExpert):
            name = "time"
            mcp_server_url = "https://time.chukai.io/mcp"

            class Operation(str, Enum):
                GET_TIME = "get_time"

            def get_mcp_tool_name(self, operation: str) -> str:
                if operation == self.Operation.GET_TIME.value:
                    return "get_local_time"
                raise ValueError(f"Unknown operation: {operation}")
    """

    # MCP server configuration (override in subclasses)
    mcp_server_url: ClassVar[str] = ""
    mcp_server_command: ClassVar[str] = ""
    mcp_server_args: ClassVar[list[str]] = []
    mcp_transport_type: ClassVar[MCPTransportType] = MCPTransportType.HTTP
    mcp_timeout: ClassVar[float] = 30.0
    mcp_bearer_token: ClassVar[str | None] = None

    # Instance-level config overrides
    server_url: str | None = Field(default=None, description="Override server URL")
    bearer_token: str | None = Field(default=None, description="Override bearer token")
    timeout: float | None = Field(default=None, description="Override timeout")

    @abstractmethod
    def get_mcp_tool_name(self, operation: str) -> str:
        """
        Map a virtual expert operation to an MCP tool name.

        Args:
            operation: The operation name from VirtualExpertAction

        Returns:
            The MCP tool name to call
        """
        ...

    def transform_parameters(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Transform virtual expert parameters to MCP tool arguments.

        Override in subclass if parameter names differ between
        virtual expert interface and MCP tool.

        Args:
            operation: The operation name
            parameters: Parameters from VirtualExpertAction

        Returns:
            Arguments for the MCP tool call
        """
        return parameters

    @abstractmethod
    def transform_result(self, operation: str, tool_result: dict[str, Any]) -> dict[str, Any]:
        """
        Transform MCP tool result to virtual expert result format.

        Args:
            operation: The operation name
            tool_result: Parsed result from MCP tool call

        Returns:
            Structured data for VirtualExpertResult
        """
        ...

    def _get_effective_url(self) -> str:
        """Get the effective server URL."""
        return self.server_url or self.mcp_server_url

    def _get_effective_token(self) -> str | None:
        """Get the effective bearer token."""
        return self.bearer_token or self.mcp_bearer_token

    def _get_effective_timeout(self) -> float:
        """Get the effective timeout."""
        return self.timeout or self.mcp_timeout

    async def execute_operation_async(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute an operation by calling the MCP server.

        Args:
            operation: Operation name
            parameters: Operation parameters

        Returns:
            Transformed result data
        """
        from chuk_mcp.protocol.messages import send_initialize
        from chuk_mcp.protocol.messages.tools import send_tools_call
        from chuk_mcp.transports.http import (
            StreamableHTTPParameters,
            http_client,
        )

        # Map operation to MCP tool
        tool_name = self.get_mcp_tool_name(operation)
        tool_args = self.transform_parameters(operation, parameters)

        url = self._get_effective_url()
        if not url:
            raise ValueError(
                f"No MCP server URL configured for {self.name}. "
                "Set mcp_server_url class variable or server_url instance variable."
            )

        # Create HTTP parameters
        params = StreamableHTTPParameters(
            url=url,
            bearer_token=self._get_effective_token(),
            timeout=self._get_effective_timeout(),
        )

        # Call MCP tool
        async with http_client(params) as (read_stream, write_stream):
            # Initialize connection
            await send_initialize(read_stream, write_stream)

            # Call the tool
            result = await send_tools_call(
                read_stream,
                write_stream,
                name=tool_name,
                arguments=tool_args,
                timeout=self._get_effective_timeout(),
            )

        # Parse result content
        tool_result = self._parse_tool_result(result)

        # Transform result
        return self.transform_result(operation, tool_result)

    def _parse_tool_result(self, result: Any) -> dict[str, Any]:
        """
        Parse MCP ToolResult into a dict.

        Handles both JSON and Pydantic model repr formats.

        Args:
            result: The ToolResult from MCP

        Returns:
            Parsed result data
        """
        # Handle error results
        if hasattr(result, "isError") and result.isError:
            error_text = ""
            if hasattr(result, "content") and result.content:
                for block in result.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        error_text = block.get("text", "")
                        break
                    elif hasattr(block, "text"):
                        error_text = block.text
                        break
            return {"error": error_text or "Unknown error"}

        # Parse successful result
        if hasattr(result, "content") and result.content:
            for block in result.content:
                # Extract text from block
                text = ""
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                elif hasattr(block, "text"):
                    text = block.text

                if text:
                    return self._parse_text_content(text)

        return {}

    def _parse_text_content(self, text: str) -> dict[str, Any]:
        """
        Parse text content as JSON.

        Args:
            text: Text content from MCP tool result

        Returns:
            Parsed dict
        """
        try:
            result: dict[str, Any] = json.loads(text)
            return result
        except json.JSONDecodeError:
            return {"text": text}

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Sync wrapper for execute_operation_async.

        For async contexts, prefer execute_operation_async directly.
        """
        import asyncio

        return asyncio.run(self.execute_operation_async(operation, parameters))

    async def execute_async(self, action: VirtualExpertAction) -> VirtualExpertResult:
        """
        Execute a VirtualExpertAction asynchronously.

        This is the preferred entry point for async contexts.
        """
        try:
            data = await self.execute_operation_async(action.operation, action.parameters)
            return VirtualExpertResult(
                data=data,
                expert_name=self.name,
                success=True,
                action=action,
            )
        except Exception as e:
            return VirtualExpertResult(
                data=None,
                expert_name=self.name,
                success=False,
                error=str(e),
                action=action,
            )

    def execute(self, action: VirtualExpertAction) -> VirtualExpertResult:
        """
        Sync wrapper for execute_async.

        For async contexts, prefer execute_async directly.
        """
        import asyncio

        return asyncio.run(self.execute_async(action))

    async def list_mcp_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        from chuk_mcp.protocol.messages import send_initialize
        from chuk_mcp.protocol.messages.tools import send_tools_list
        from chuk_mcp.transports.http import (
            StreamableHTTPParameters,
            http_client,
        )

        url = self._get_effective_url()
        if not url:
            raise ValueError(f"No MCP server URL configured for {self.name}")

        params = StreamableHTTPParameters(
            url=url,
            bearer_token=self._get_effective_token(),
            timeout=self._get_effective_timeout(),
        )

        async with http_client(params) as (read_stream, write_stream):
            await send_initialize(read_stream, write_stream)
            result = await send_tools_list(read_stream, write_stream)

        return [
            {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "input_schema": getattr(tool, "inputSchema", {}),
            }
            for tool in result.tools
        ]
