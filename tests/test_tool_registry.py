"""Tests for tool registry exposure (TOOL-01 through TOOL-05).

Tests verify:
- TOOL-01: Built-in tools (bash, read, write, str_replace) are exposed
- TOOL-02: MCP tools loaded from extensions_config.json
- TOOL-03: Tools deduplicated by name
- TOOL-04: MCP tool initialization logged clearly
- TOOL-05: Warning when expected MCP tools unavailable
"""
import sys
from dataclasses import dataclass
from typing import Any
import pytest


@dataclass(frozen=True)
class MockTool:
    """Mock tool for testing MCP tool naming."""
    name: str


@pytest.fixture
def mock_extensions_config():
    """Factory fixture for mock extensions config.

    Returns a function that creates mock server configs.
    """
    def _create_server_config(
        name: str,
        server_type: str = "stdio",
        enabled: bool = True,
        **kwargs: Any
    ) -> dict[str, Any]:
        return {
            "type": server_type,
            "enabled": enabled,
            **kwargs
        }
    return _create_server_config


@pytest.fixture
def mock_mcp_tools():
    """Factory fixture for mock MCP tools.

    Returns a function that creates mock MCP tools with proper naming.
    MCP tools follow convention: mcp__{server}__{tool}
    """
    def _create_tools(server_tools: dict[str, list[str]]) -> list[MockTool]:
        tools = []
        for server, tool_names in server_tools.items():
            for tool_name in tool_names:
                full_name = f"mcp__{server}__{tool_name}"
                tools.append(MockTool(name=full_name))
        return tools
    return _create_tools


class TestBuiltinTools:
    """Tests for TOOL-01: Built-in tool exposure."""

    def test_builtin_tools_available(self, capsys):
        """TOOL-01: Verify built-in tools are exposed.

        Expected: log_available_tools prints built-in tool names:
        - bash, read, write, str_replace
        """
        from lib.tools import log_available_tools

        # Create mock tools simulating deerflow.tools.get_available_tools output
        tools = [
            MockTool(name="bash"),
            MockTool(name="read"),
            MockTool(name="write"),
            MockTool(name="str_replace"),
        ]

        log_available_tools(tools)

        captured = capsys.readouterr()
        # Should print tool names (to stderr for logging)
        assert "bash" in captured.out or "bash" in captured.err
        assert "read" in captured.out or "read" in captured.err
        assert "write" in captured.out or "write" in captured.err
        assert "str_replace" in captured.out or "str_replace" in captured.err

    def test_tool_deduplication(self):
        """TOOL-03: Verify tools deduplicated by name.

        Expected: If multiple tools have same name, only one appears.
        This test verifies the deerflow-harness behavior (not our implementation).
        """
        from lib.tools import get_unique_tool_names

        # Create tools with duplicate names
        tools = [
            MockTool(name="bash"),
            MockTool(name="bash"),  # Duplicate
            MockTool(name="read"),
        ]

        names = get_unique_tool_names(tools)
        # Should have unique names only
        assert len(names) == 2
        assert "bash" in names
        assert "read" in names


class TestMCPTools:
    """Tests for TOOL-02, TOOL-04, TOOL-05: MCP tool handling."""

    def test_mcp_tools_loaded(self, mock_mcp_tools):
        """TOOL-02: Verify MCP tools loaded from extensions_config.json.

        Expected: MCP tools are visible with server-prefixed names.
        """
        from lib.tools import get_mcp_tool_names

        mcp_tools = mock_mcp_tools(server_tools={
            "filesystem": ["read", "write"],
            "github": ["search", "create_issue"]
        })

        names = get_mcp_tool_names(mcp_tools)

        # Should have MCP-prefixed names
        assert "mcp__filesystem__read" in names
        assert "mcp__filesystem__write" in names
        assert "mcp__github__search" in names
        assert "mcp__github__create_issue" in names
        # Total 4 tools
        assert len(names) == 4

    def test_mcp_status_logging(self, mock_mcp_tools, capsys):
        """TOOL-04: Verify MCP tool initialization is logged clearly.

        Expected: log_mcp_status prints:
        - Configured MCP servers count
        - Each server name and transport type
        - Loaded MCP tools count
        """
        from lib.tools import log_mcp_status

        servers = {"filesystem": {"type": "stdio", "enabled": True}}
        mcp_tools = mock_mcp_tools(server_tools={"filesystem": ["read", "write"]})

        log_mcp_status(servers, mcp_tools)

        captured = capsys.readouterr()
        # Should print MCP server info
        assert "MCP" in captured.out or "MCP" in captured.err
        assert "filesystem" in captured.out or "filesystem" in captured.err
        assert "stdio" in captured.out or "stdio" in captured.err
        # Should print loaded tools count
        assert "2" in captured.out or "2" in captured.err

    def test_mcp_status_no_servers(self, capsys):
        """TOOL-04: Verify graceful handling when no MCP servers configured."""
        from lib.tools import log_mcp_status

        log_mcp_status({}, [])

        captured = capsys.readouterr()
        assert "No MCP servers" in captured.out or "No MCP servers" in captured.err

    def test_mcp_unavailable_warning(self, mock_mcp_tools, capsys):
        """TOOL-05: Verify warning when expected MCP tools unavailable.

        Expected: If MCP server enabled but no tools loaded, warn user.
        """
        from lib.tools import check_mcp_tool_availability

        servers = {
            "filesystem": {"type": "stdio", "enabled": True},
            "broken-server": {"type": "stdio", "enabled": True}
        }
        # filesystem has tools, broken-server has none
        mcp_tools = mock_mcp_tools(server_tools={"filesystem": ["read"]})

        warnings = check_mcp_tool_availability(servers, mcp_tools)

        # Should return warning for broken-server
        assert len(warnings) == 1
        assert "broken-server" in warnings[0]
        assert "no tools loaded" in warnings[0]

        captured = capsys.readouterr()
        # Should print warning to stderr
        assert "warning" in captured.err.lower() or "Warning" in captured.err
