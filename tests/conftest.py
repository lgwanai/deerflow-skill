"""Pytest fixtures for Phase 2 streaming and error handling tests.

Provides mock fixtures that simulate DeerFlowClient.stream() behavior
without requiring the actual deerflow-harness package.
"""
from typing import Iterator
from unittest.mock import Mock, MagicMock
import pytest


@pytest.fixture
def mock_stream_event():
    """Factory fixture to create StreamEvent-like mock objects.

    StreamEvent types from deerflow:
    - "values": Contains accumulated state values
    - "messages-tuple": Contains message delta tuples
    - "custom": Custom events like retry progress
    - "end": Stream termination event

    Args:
        event_type: One of "values", "messages-tuple", "custom", "end"
        data: Dictionary containing event data

    Returns:
        Mock object with type and data attributes
    """
    def _factory(event_type: str, data: dict) -> Mock:
        event = Mock()
        event.type = event_type
        event.data = data
        return event
    return _factory


@pytest.fixture
def mock_deerflow_client(mock_stream_event):
    """Mock DeerFlowClient with configurable stream() method.

    The mock has spec=['stream', 'chat'] for proper attribute checking
    and will raise AttributeError for undefined methods.

    Args:
        events: List of (type, data) tuples to yield from stream()
        error: Optional exception to raise during iteration

    Returns:
        Mock DeerFlowClient instance
    """
    def _factory(events=None, error=None):
        client = Mock(spec=['stream', 'chat'])

        if error:
            # Create an iterator that raises error
            def error_stream(*args, **kwargs):
                if events:
                    for event_type, data in events:
                        yield mock_stream_event(event_type, data)
                raise error
            client.stream.side_effect = error_stream
        elif events:
            def event_stream(*args, **kwargs):
                for event_type, data in events:
                    yield mock_stream_event(event_type, data)
            client.stream.return_value = event_stream()
        else:
            client.stream.return_value = iter([])

        return client
    return _factory


@pytest.fixture
def simple_text_stream(mock_stream_event):
    """Pre-built fixture for basic text streaming scenario.

    Yields events simulating:
    - Token-by-token text output (messages-tuple events)
    - Final end event

    Returns:
        List of (type, data) tuples for simple text streaming
    """
    return [
        ("messages-tuple", {"content": "Hello"}),
        ("messages-tuple", {"content": " world"}),
        ("messages-tuple", {"content": "!"}),
        ("end", {}),
    ]


@pytest.fixture
def tool_call_stream(mock_stream_event):
    """Pre-built fixture for tool call notifications.

    Yields events simulating:
    - Tool call start notification
    - Tool execution result
    - Response tokens
    - End event

    Returns:
        List of (type, data) tuples for tool call streaming
    """
    return [
        ("values", {"tool_calls": [{"name": "search", "args": {"query": "test"}}]}),
        ("values", {"tool_results": [{"name": "search", "result": "Found 3 items"}]}),
        ("messages-tuple", {"content": "I found"}),
        ("messages-tuple", {"content": " 3 items"}),
        ("messages-tuple", {"content": " for you."}),
        ("end", {}),
    ]


@pytest.fixture
def error_stream(mock_stream_event):
    """Pre-built fixture for error scenario.

    Yields events before raising an exception to test partial output handling.

    Returns:
        List of (type, data) tuples before error occurs
    """
    return [
        ("messages-tuple", {"content": "Partial"}),
        ("messages-tuple", {"content": " output"}),
    ]


@pytest.fixture
def retry_stream(mock_stream_event):
    """Pre-built fixture for LLM retry custom events.

    Yields events simulating:
    - Retry progress notifications
    - Successful response after retries

    Returns:
        List of (type, data) tuples for retry scenario
    """
    return [
        ("custom", {"event": "retry", "attempt": 1, "max_attempts": 3}),
        ("custom", {"event": "retry", "attempt": 2, "max_attempts": 3}),
        ("messages-tuple", {"content": "Success"}),
        ("messages-tuple", {"content": " after retry"}),
        ("end", {}),
    ]


# =============================================================================
# Phase 3: Tool Registry Exposure fixtures
# =============================================================================

@pytest.fixture
def mock_tool():
    """Factory fixture to create BaseTool-like mock objects.

    Args:
        name: Tool name (e.g., "bash", "read", "mcp__filesystem__read")
        description: Tool description

    Returns:
        Mock object with name and description attributes
    """
    def _factory(name: str, description: str = "Test tool") -> Mock:
        tool = Mock()
        tool.name = name
        tool.description = description
        return tool
    return _factory


@pytest.fixture
def mock_get_available_tools(mock_tool):
    """Mock for deerflow.tools.get_available_tools function.

    Args:
        tools: List of tool names to return
        include_builtins: If True, include bash/read/write/str_replace

    Returns:
        Mock function returning list of tools
    """
    def _factory(tools: list[str] | None = None, include_builtins: bool = True):
        result = []
        if include_builtins:
            result.extend([
                mock_tool("bash", "Execute bash commands"),
                mock_tool("read", "Read file contents"),
                mock_tool("write", "Write to file"),
                mock_tool("str_replace", "Replace text in file"),
            ])
        if tools:
            result.extend([mock_tool(name) for name in tools])
        return result
    return _factory


@pytest.fixture
def mock_mcp_tools(mock_tool):
    """Mock for deerflow.mcp.cache.get_cached_mcp_tools function.

    Args:
        server_tools: Dict of {server_name: [tool_names]}

    Returns:
        Mock function returning list of MCP-prefixed tools
    """
    def _factory(server_tools: dict[str, list[str]] | None = None):
        if not server_tools:
            return []

        result = []
        for server, tools in server_tools.items():
            for tool_name in tools:
                # MCP tools are prefixed: mcp__{server}__{tool}
                result.append(mock_tool(f"mcp__{server}__{tool_name}"))
        return result
    return _factory


@pytest.fixture
def mock_extensions_config():
    """Mock for deerflow.config.extensions_config.ExtensionsConfig.

    Args:
        enabled_servers: Dict of {server_name: {"type": "stdio"|"sse", "enabled": True}}

    Returns:
        Mock ExtensionsConfig with get_enabled_mcp_servers method
    """
    def _factory(enabled_servers: dict[str, dict] | None = None):
        config = Mock()
        config.get_enabled_mcp_servers.return_value = enabled_servers or {}
        return config
    return _factory
