"""Tests for mode preset mapping.

This module tests the mode presets defined in lib/modes.py:

- flash: thinking=false, plan_mode=false, subagent=false (fastest)
- standard: thinking=true, plan_mode=false, subagent=false (default)
- pro: thinking=true, plan_mode=true, subagent=false
- ultra: thinking=true, plan_mode=true, subagent=true
"""

import pytest


class TestModePresets:
    """Tests for mode preset definitions."""

    def test_flash_mode(self):
        """Test that flash mode returns correct settings."""
        from lib.modes import get_mode_config

        config = get_mode_config("flash")

        assert config["thinking_enabled"] is False
        assert config["plan_mode"] is False
        assert config["subagent_enabled"] is False

    def test_standard_mode(self):
        """Test that standard mode returns correct settings."""
        from lib.modes import get_mode_config

        config = get_mode_config("standard")

        assert config["thinking_enabled"] is True
        assert config["plan_mode"] is False
        assert config["subagent_enabled"] is False

    def test_pro_mode(self):
        """Test that pro mode returns correct settings."""
        from lib.modes import get_mode_config

        config = get_mode_config("pro")

        assert config["thinking_enabled"] is True
        assert config["plan_mode"] is True
        assert config["subagent_enabled"] is False

    def test_ultra_mode(self):
        """Test that ultra mode returns correct settings."""
        from lib.modes import get_mode_config

        config = get_mode_config("ultra")

        assert config["thinking_enabled"] is True
        assert config["plan_mode"] is True
        assert config["subagent_enabled"] is True

    def test_unknown_mode_raises(self):
        """Test that unknown mode raises ValueError."""
        from lib.modes import get_mode_config

        with pytest.raises(ValueError, match="Unknown mode"):
            get_mode_config("unknown")

    def test_mode_presets_dict_exists(self):
        """Test that MODE_PRESETS dict is available."""
        from lib.modes import MODE_PRESETS

        assert "flash" in MODE_PRESETS
        assert "standard" in MODE_PRESETS
        assert "pro" in MODE_PRESETS
        assert "ultra" in MODE_PRESETS

    def test_mode_config_dataclass(self):
        """Test that ModeConfig dataclass has required fields."""
        from lib.modes import ModeConfig

        config = ModeConfig(thinking_enabled=True, plan_mode=False, subagent_enabled=False)

        assert config.thinking_enabled is True
        assert config.plan_mode is False
        assert config.subagent_enabled is False

    def test_get_mode_config_returns_dict(self):
        """Test that get_mode_config returns a dict suitable for kwargs."""
        from lib.modes import get_mode_config

        config = get_mode_config("standard")

        assert isinstance(config, dict)
        # Should have exactly the keys needed for DeerFlowClient
        assert set(config.keys()) == {"thinking_enabled", "plan_mode", "subagent_enabled"}
