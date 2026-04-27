"""Tests for subagent delegation configuration (Phase 4).

Tests:
- SUBA-01: Skill enables task_tool for subagent delegation
- SUBA-02: Skill configures subagent timeout with clear default (900s)
- SUBA-03: Skill reports which subagent timed out on timeout error
- SUBA-04: Skill exposes MAX_CONCURRENT_SUBAGENTS limit
"""
import os
import pytest
from unittest.mock import patch, Mock


class TestSubagentEnabled:
    """Tests for SUBA-01: Subagent delegation is enabled in ultra mode."""

    def test_subagent_enabled_in_ultra_mode(self):
        """Ultra mode preset should have subagent_enabled=True."""
        from lib.modes import get_mode_config

        config = get_mode_config("ultra")
        assert config["subagent_enabled"] is True

    def test_other_modes_have_subagent_disabled(self):
        """Flash, standard, pro modes should have subagent_enabled=False."""
        from lib.modes import get_mode_config

        for mode in ["flash", "standard", "pro"]:
            config = get_mode_config(mode)
            assert config["subagent_enabled"] is False


class TestSubagentTimeout:
    """Tests for SUBA-02: Subagent timeout configuration."""

    def test_default_timeout_is_900_seconds(self):
        """Default subagent timeout should be 900 seconds (15 min)."""
        from lib.subagent import DEFAULT_SUBAGENT_TIMEOUT

        assert DEFAULT_SUBAGENT_TIMEOUT == 900

    def test_get_subagent_config_returns_default_timeout(self):
        """get_subagent_config should return 900s timeout by default."""
        from lib.subagent import get_subagent_config

        with patch.dict(os.environ, {}, clear=True):
            config = get_subagent_config()
            assert config["subagent_timeout"] == 900

    def test_get_subagent_config_respects_env_var(self):
        """get_subagent_config should read DEER_FLOW_SUBAGENT_TIMEOUT from env."""
        from lib.subagent import get_subagent_config

        with patch.dict(os.environ, {"DEER_FLOW_SUBAGENT_TIMEOUT": "1800"}):
            config = get_subagent_config()
            assert config["subagent_timeout"] == 1800


class TestSubagentTimeoutError:
    """Tests for SUBA-03: Timeout error identifies which subagent timed out."""

    def test_format_timeout_error_includes_agent_name(self):
        """Timeout error should include subagent name in message."""
        from lib.subagent import format_subagent_timeout_error

        # Simulate timeout error with agent context
        error = Exception("Subagent 'research_agent' timed out")
        message = format_subagent_timeout_error(error, 900)

        assert "research_agent" in message
        assert "900" in message

    def test_format_timeout_error_with_unknown_agent(self):
        """Timeout error without agent name should show 'unknown'."""
        from lib.subagent import format_subagent_timeout_error

        error = TimeoutError("Operation timed out")
        message = format_subagent_timeout_error(error, 900)

        assert "unknown" in message.lower() or "subagent" in message.lower()

    def test_format_timeout_error_includes_guidance(self):
        """Timeout error should include actionable guidance."""
        from lib.subagent import format_subagent_timeout_error

        error = Exception("Subagent 'agent' timed out")
        message = format_subagent_timeout_error(error, 900)

        # Should include suggestions
        assert "DEER_FLOW_SUBAGENT_TIMEOUT" in message or "try" in message.lower()


class TestMaxConcurrentSubagents:
    """Tests for SUBA-04: MAX_CONCURRENT_SUBAGENTS limit is exposed."""

    def test_default_max_concurrent_is_3(self):
        """Default max concurrent subagents should be 3."""
        from lib.subagent import DEFAULT_MAX_CONCURRENT_SUBAGENTS

        assert DEFAULT_MAX_CONCURRENT_SUBAGENTS == 3

    def test_get_max_concurrent_subagents_returns_default(self):
        """get_max_concurrent_subagents should return 3 by default."""
        from lib.subagent import get_max_concurrent_subagents

        with patch.dict(os.environ, {}, clear=True):
            assert get_max_concurrent_subagents() == 3

    def test_get_max_concurrent_subagents_respects_env_var(self):
        """get_max_concurrent_subagents should read MAX_CONCURRENT_SUBAGENTS from env."""
        from lib.subagent import get_max_concurrent_subagents

        with patch.dict(os.environ, {"MAX_CONCURRENT_SUBAGENTS": "5"}):
            assert get_max_concurrent_subagents() == 5

    def test_get_max_concurrent_subagents_handles_invalid_value(self):
        """get_max_concurrent_subagents should handle non-integer env vars gracefully."""
        from lib.subagent import get_max_concurrent_subagents

        with patch.dict(os.environ, {"MAX_CONCURRENT_SUBAGENTS": "invalid"}):
            # Should return default instead of crashing
            assert get_max_concurrent_subagents() == 3

    def test_get_subagent_config_includes_max_concurrent(self):
        """get_subagent_config should include max_concurrent_subagents."""
        from lib.subagent import get_subagent_config

        with patch.dict(os.environ, {"MAX_CONCURRENT_SUBAGENTS": "7"}):
            config = get_subagent_config()
            assert config["max_concurrent_subagents"] == 7