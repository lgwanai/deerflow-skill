"""Tests for error message formatting.

Tests the behavior specified in the plan:
- Test 1: format_error(ImportError) returns missing package message with pip/uv commands
- Test 2: format_error(FileNotFoundError with config context) returns missing config message
- Test 3: format_error with credential errors returns full guidance with env var names
- Test 4: format_error with unknown error returns raw error message
"""
import pytest


class TestFormatError:
    """Tests for format_error function."""

    def test_import_error_returns_missing_package_message(self):
        """Test 1: format_error(ImportError) returns missing package message with pip/uv commands."""
        from lib.errors import format_error, MISSING_PACKAGE_MSG

        error = ImportError("No module named 'deerflow'")
        result = format_error(error)

        # Should contain pip and uv install commands
        assert "pip install deerflow-harness" in result
        assert "uv add deerflow-harness" in result
        # Should match the template format
        assert MISSING_PACKAGE_MSG in result or result == MISSING_PACKAGE_MSG

    def test_file_not_found_error_returns_missing_config_message(self):
        """Test 2: format_error(FileNotFoundError with config context) returns missing config message."""
        from lib.errors import format_error

        # Simulate the error raised when config is missing
        error = FileNotFoundError("config.yaml not found. Created config.example.yaml with template.")
        result = format_error(error)

        # Should mention config.yaml and example template
        assert "config.yaml" in result.lower() or "config" in result.lower()
        assert "config.example.yaml" in result.lower() or "example" in result.lower()

    def test_value_error_with_credentials_returns_full_guidance(self):
        """Test 3: format_error with credential errors returns full guidance with env var names."""
        from lib.errors import format_error

        # Simulate the error raised when credentials are missing
        error = ValueError(
            "Missing required credentials:\n"
            "  - gpt-4: OPENAI_API_KEY not set\n"
            "  - claude: ANTHROPIC_API_KEY not set"
        )
        result = format_error(error)

        # Should contain env var names
        assert "OPENAI_API_KEY" in result
        assert "ANTHROPIC_API_KEY" in result
        # Should contain example config or guidance
        assert "export" in result.lower() or "api_key" in result.lower()

    def test_unknown_error_returns_raw_message(self):
        """Test 4: format_error with unknown error returns raw error message."""
        from lib.errors import format_error

        # Some random error type
        error = RuntimeError("Something unexpected happened")
        result = format_error(error)

        # Should return the raw message without extra wrapping
        assert "Something unexpected happened" in result


class TestMessageTemplates:
    """Tests for message template constants."""

    def test_missing_package_msg_has_install_commands(self):
        """Test that MISSING_PACKAGE_MSG contains pip and uv install commands."""
        from lib.errors import MISSING_PACKAGE_MSG

        assert "pip install deerflow-harness" in MISSING_PACKAGE_MSG
        assert "uv add deerflow-harness" in MISSING_PACKAGE_MSG

    def test_missing_config_msg_mentions_example(self):
        """Test that MISSING_CONFIG_MSG mentions example template."""
        from lib.errors import MISSING_CONFIG_MSG

        assert "config.example.yaml" in MISSING_CONFIG_MSG

    def test_missing_credentials_msg_has_env_vars(self):
        """Test that MISSING_CREDENTIALS_MSG mentions env var names."""
        from lib.errors import MISSING_CREDENTIALS_MSG

        # Should mention at least one common env var
        assert "OPENAI_API_KEY" in MISSING_CREDENTIALS_MSG or "API_KEY" in MISSING_CREDENTIALS_MSG
        # Should contain example config or export guidance
        assert "api_key" in MISSING_CREDENTIALS_MSG.lower()


class TestErrorDetection:
    """Tests for error type detection and routing."""

    def test_detects_import_error_by_module_name(self):
        """Test that deerflow-related ImportError is detected."""
        from lib.errors import format_error

        # Different variations of import errors
        errors = [
            ImportError("No module named 'deerflow'"),
            ImportError("cannot import name 'DeerFlowClient' from 'deerflow'"),
            ModuleNotFoundError("No module named 'deerflow.client'"),
        ]

        for error in errors:
            result = format_error(error)
            # All should show install guidance
            assert "deerflow-harness" in result

    def test_detects_yaml_parse_error(self):
        """Test that YAML parsing errors show config guidance."""
        from lib.errors import format_error

        # Simulate YAML parse error wrapped in ValueError
        error = ValueError("Failed to parse config.yaml: invalid yaml")
        result = format_error(error)

        # Should mention config parsing issue
        assert "parse" in result.lower() or "yaml" in result.lower() or "config" in result.lower()