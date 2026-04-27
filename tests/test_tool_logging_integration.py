"""Integration tests for tool logging in skill.py.

Tests verify that skill.py correctly calls lib.tools functions.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestToolLoggingIntegration:
    """Tests for tool logging integration in skill.py."""

    def test_log_tools_function_exists(self):
        """Verify _log_tools function exists in skill module."""
        from skill import _log_tools
        assert callable(_log_tools)

    def test_log_tools_handles_import_error(self):
        """Verify _log_tools handles ImportError gracefully."""
        from skill import _log_tools

        # Should not raise even if deerflow imports fail
        with patch.dict('sys.modules', {
            'deerflow.tools': None,
            'deerflow.mcp': None,
            'deerflow.mcp.cache': None,
            'deerflow.config': None,
            'deerflow.config.extensions_config': None,
        }):
            # This should not crash
            _log_tools({})

    def test_log_tools_calls_logging_functions(self):
        """Verify _log_tools calls lib.tools functions when imports succeed."""
        from skill import _log_tools

        mock_tool = MagicMock()
        mock_tool.name = "bash"

        # Create mock modules for deerflow (doesn't exist in test env)
        mock_deerflow_tools = MagicMock()
        mock_deerflow_tools.get_available_tools.return_value = [mock_tool]

        mock_deerflow_mcp = MagicMock()
        mock_deerflow_mcp.get_cached_mcp_tools.return_value = []

        mock_extensions = MagicMock()
        mock_extensions.from_file.return_value.get_enabled_mcp_servers.return_value = {}

        # Patch sys.modules to inject mock deerflow modules
        with patch.dict('sys.modules', {
            'deerflow.tools': mock_deerflow_tools,
            'deerflow.mcp': MagicMock(),
            'deerflow.mcp.cache': mock_deerflow_mcp,
            'deerflow.config': MagicMock(),
            'deerflow.config.extensions_config': mock_extensions,
        }):
            with patch('skill.log_available_tools') as mock_log:
                _log_tools({})

                # Verify logging was called
                mock_log.assert_called_once()

    def test_main_with_args_calls_log_tools(self):
        """Verify main_with_args calls _log_tools after client creation."""
        from skill import main_with_args

        mock_client_instance = MagicMock()
        mock_client_instance.stream.return_value = iter([])

        with patch('skill.resolve_and_validate_config') as mock_config:
            with patch('skill.get_mode_config') as mock_mode:
                with patch('skill._get_deerflow_client') as mock_client_class:
                    with patch('skill._log_tools') as mock_log_tools:
                        with patch('skill.stream_with_error_handling'):
                            mock_config.return_value = "/mock/config.yaml"
                            mock_mode.return_value = {"model_name": "flash"}
                            mock_client_class.return_value.return_value = mock_client_instance

                            main_with_args(['test prompt'])

                            # Verify _log_tools was called with client_kwargs
                            mock_log_tools.assert_called_once_with({"model_name": "flash"})
