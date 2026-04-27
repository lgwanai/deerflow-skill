"""Tests for tool registry exposure (TOOL-01 through TOOL-05).

Tests verify:
- TOOL-01: Built-in tools (bash, read, write, str_replace) are exposed
- TOOL-02: MCP tools loaded from extensions_config.json
- TOOL-03: Tools deduplicated by name
- TOOL-04: MCP tool initialization logged clearly
- TOOL-05: Warning when expected MCP tools unavailable
"""
import pytest


class TestBuiltinTools:
    """Tests for TOOL-01: Built-in tool exposure."""

    @pytest.mark.skip(reason="Wave 0 stub - implementation pending")
    def test_builtin_tools_available(self):
        """TOOL-01: Verify built-in tools are exposed."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub - implementation pending")
    def test_tool_deduplication(self):
        """TOOL-03: Verify tools deduplicated by name."""
        pass


class TestMCPTools:
    """Tests for TOOL-02, TOOL-04, TOOL-05: MCP tool handling."""

    @pytest.mark.skip(reason="Wave 0 stub - implementation pending")
    def test_mcp_tools_loaded(self):
        """TOOL-02: Verify MCP tools loaded from extensions_config.json."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub - implementation pending")
    def test_mcp_status_logging(self, caplog):
        """TOOL-04: Verify MCP tool initialization is logged clearly."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub - implementation pending")
    def test_mcp_unavailable_warning(self, caplog):
        """TOOL-05: Verify warning when expected MCP tools unavailable."""
        pass
