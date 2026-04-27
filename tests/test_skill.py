"""Tests for skill.py entry point.

This module tests the skill entry point functionality:

- CLI argument parsing
- Mode preset selection
- Error handling for missing config
- ImportError handling for missing deerflow-harness
"""

import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest


class TestSkillEntryPoint:
    """Tests for skill.py entry point."""

    def test_import_skill_module(self):
        """Test that skill.py can be imported."""
        import skill

        assert hasattr(skill, "main")
        assert hasattr(skill, "parse_args")

    def test_parse_args_with_mode(self):
        """Test parse_args extracts mode flag."""
        import skill

        mode, prompt = skill.parse_args(["--flash", "hello world"])
        assert mode == "flash"
        assert prompt == "hello world"

    def test_parse_args_default_mode(self):
        """Test parse_args uses standard as default."""
        import skill

        mode, prompt = skill.parse_args(["hello world"])
        assert mode == "standard"
        assert prompt == "hello world"

    def test_parse_args_no_prompt_raises(self):
        """Test parse_args raises ValueError without prompt."""
        import skill

        with pytest.raises(ValueError, match="Usage"):
            skill.parse_args([])

    def test_parse_args_joins_multiple_words(self):
        """Test parse_args joins multiple words into prompt."""
        import skill

        mode, prompt = skill.parse_args(["hello", "world", "test"])
        assert prompt == "hello world test"

    def test_main_missing_config_shows_error(self, tmp_path, monkeypatch):
        """Test main shows clear error when config is missing."""
        import skill

        # Change to temp directory with no config
        monkeypatch.chdir(tmp_path)
        # Clear any DEER_FLOW_CONFIG_PATH
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["--flash", "test prompt"])

        # Should exit with error code 1
        assert exc_info.value.code == 1

    def test_skill_file_is_executable_entry_point(self):
        """Test skill.py has if __name__ == '__main__' block."""
        skill_path = Path(__file__).parent.parent / "skill.py"
        content = skill_path.read_text()
        assert "if __name__ ==" in content or 'if __name__ == "__main__"' in content


class TestSkillIntegration:
    """Integration tests for skill.py (require mocked deerflow)."""

    def test_skill_creates_example_config_on_missing(self, tmp_path, monkeypatch):
        """Test skill creates config.example.yaml when config is missing."""
        import skill

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        with pytest.raises(SystemExit):
            skill.main_with_args(["test prompt"])

        example_config = tmp_path / "config.example.yaml"
        assert example_config.exists()

    def test_skill_shows_usage_on_no_args(self):
        """Test skill shows usage error when no prompt provided."""
        import skill

        with pytest.raises(ValueError, match="Usage"):
            skill.parse_args([])


class TestModeFlags:
    """Tests for mode flag handling."""

    def test_all_mode_flags_recognized(self):
        """Test all mode flags are parsed correctly."""
        import skill

        for mode in ["flash", "standard", "pro", "ultra"]:
            parsed_mode, prompt = skill.parse_args([f"--{mode}", "test"])
            assert parsed_mode == mode

    def test_unknown_mode_passed_through(self):
        """Test unknown mode is passed to get_mode_config which raises."""
        import skill

        mode, prompt = skill.parse_args(["--unknown", "test"])
        assert mode == "unknown"
