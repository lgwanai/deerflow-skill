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


class TestStreamingErrorMessages:
    """Tests for streaming-specific error messages (ERRR-01, ERRR-02, ERRR-03, ERRR-04)."""

    def test_format_streaming_error_recursion(self):
        """Test 1: format_streaming_error formats GraphRecursionError."""
        from lib.errors import format_streaming_error, STREAMING_ERRORS
        # GraphRecursionError is from langgraph.errors
        # We'll use a mock class for testing
        class MockGraphRecursionError(Exception):
            pass

        error = MockGraphRecursionError("Recursion limit of 100 reached")
        result = format_streaming_error(error)

        # Should return the recursion error template
        assert result == STREAMING_ERRORS["recursion"]
        # Should contain actionable guidance
        assert "complex" in result.lower() or "simplif" in result.lower() or "pro" in result.lower()

    def test_format_streaming_error_timeout(self):
        """Test 2: format_streaming_error formats timeout errors."""
        from lib.errors import format_streaming_error, STREAMING_ERRORS

        error = TimeoutError("Request timed out after 30 seconds")
        result = format_streaming_error(error)

        # Should return the timeout template
        assert result == STREAMING_ERRORS["llm_timeout"]
        # Should mention timing/timeout
        assert "timeout" in result.lower() or "long" in result.lower() or "wait" in result.lower()

    def test_format_streaming_error_quota(self):
        """Test 3: format_streaming_error formats quota errors."""
        from lib.errors import format_streaming_error, STREAMING_ERRORS

        error = RuntimeError("quota exceeded for this billing period")
        result = format_streaming_error(error)

        # Should return the quota template
        assert result == STREAMING_ERRORS["llm_quota"]
        # Should mention provider dashboard
        assert "openai" in result.lower() or "anthropic" in result.lower() or "usage" in result.lower()

    def test_format_streaming_error_auth(self):
        """Test 4: format_streaming_error formats auth errors."""
        from lib.errors import format_streaming_error, STREAMING_ERRORS

        error = PermissionError("401 Unauthorized: invalid api key")
        result = format_streaming_error(error)

        # Should return the auth template
        assert result == STREAMING_ERRORS["llm_auth"]
        # Should mention API key guidance
        assert "api_key" in result.lower() or "key" in result.lower()

    def test_stateless_session_info_exists(self):
        """Test 5: STATELESS_SESSION_INFO message exists."""
        from lib.errors import STATELESS_SESSION_INFO

        # Should document stateless behavior
        assert STATELESS_SESSION_INFO is not None
        assert len(STATELESS_SESSION_INFO) > 50  # Should be substantive
        # Should mention key concepts
        info_lower = STATELESS_SESSION_INFO.lower()
        assert "stateless" in info_lower or "memory" in info_lower or "persistent" in info_lower

    def test_format_streaming_error_fallback(self):
        """Test 6: format_streaming_error falls back to raw message."""
        from lib.errors import format_streaming_error

        error = ValueError("Some random error")
        result = format_streaming_error(error)

        # Should include the raw error message
        assert "Some random error" in result

    def test_streaming_errors_dict_has_all_keys(self):
        """Test 7: STREAMING_ERRORS has all required keys."""
        from lib.errors import STREAMING_ERRORS

        required_keys = ["recursion", "llm_timeout", "llm_quota", "llm_auth"]
        for key in required_keys:
            assert key in STREAMING_ERRORS, f"Missing key: {key}"
            assert len(STREAMING_ERRORS[key]) > 20, f"Template for {key} is too short"

    def test_recursion_message_actionable(self):
        """ERRR-01: GraphRecursionError shows clear message with actionable guidance."""
        from lib.errors import STREAMING_ERRORS

        msg = STREAMING_ERRORS["recursion"]
        # Should explain what happened
        assert "recursion" in msg.lower() or "step" in msg.lower() or "limit" in msg.lower()
        # Should provide guidance
        assert "simpl" in msg.lower() or "pro" in msg.lower() or "complex" in msg.lower()

    def test_llm_timeout_message_actionable(self):
        """ERRR-02: Timeout errors show guidance."""
        from lib.errors import STREAMING_ERRORS

        msg = STREAMING_ERRORS["llm_timeout"]
        # Should explain what happened
        assert "timeout" in msg.lower() or "long" in msg.lower()
        # Should provide suggestions
        assert "wait" in msg.lower() or "simpl" in msg.lower() or "try" in msg.lower()

    def test_llm_quota_message_has_dashboard_links(self):
        """ERRR-02: Quota errors show dashboard links."""
        from lib.errors import STREAMING_ERRORS

        msg = STREAMING_ERRORS["llm_quota"]
        # Should mention checking usage/billing
        assert "usage" in msg.lower() or "billing" in msg.lower() or "account" in msg.lower()
        # Should link to provider dashboard
        assert "openai" in msg.lower() or "anthropic" in msg.lower() or "platform" in msg.lower()

    def test_llm_auth_message_actionable(self):
        """ERRR-02: Auth errors show API key guidance."""
        from lib.errors import STREAMING_ERRORS

        msg = STREAMING_ERRORS["llm_auth"]
        # Should explain authentication failure
        assert "auth" in msg.lower() or "api_key" in msg.lower() or "key" in msg.lower()
        # Should provide next steps
        assert "check" in msg.lower() or "set" in msg.lower() or "valid" in msg.lower()

    def test_stateless_session_info_documents_behavior(self):
        """ERRR-03: Session behavior documented."""
        from lib.errors import STATELESS_SESSION_INFO

        # Should explain stateless nature
        assert "stateless" in STATELESS_SESSION_INFO.lower() or "memory" in STATELESS_SESSION_INFO.lower()
        # Should mention no persistence
        assert "not" in STATELESS_SESSION_INFO.lower() or "no" in STATELESS_SESSION_INFO.lower()
        # Should provide context about thread_id purpose
        info_lower = STATELESS_SESSION_INFO.lower()
        assert "thread" in info_lower or "session" in info_lower

    def test_all_error_messages_are_actionable(self):
        """ERRR-04: All error messages are actionable."""
        from lib.errors import STREAMING_ERRORS

        for key, msg in STREAMING_ERRORS.items():
            # Each message should have some form of action guidance
            # Either suggestions, links, or next steps
            has_action = (
                "try" in msg.lower() or
                "check" in msg.lower() or
                "use" in msg.lower() or
                "visit" in msg.lower() or
                "http" in msg.lower() or
                "wait" in msg.lower() or
                "simpl" in msg.lower()
            )
            assert has_action, f"Error message for {key} lacks actionable guidance"