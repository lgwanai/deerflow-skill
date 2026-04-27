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


class TestStreamingIntegration:
    """Tests for streaming integration in skill.py."""

    def test_main_with_args_uses_stream_and_print(self, mock_deerflow_client, tmp_path, monkeypatch, capsys):
        """Test 1: main_with_args uses stream_and_print instead of chat."""
        import skill
        from pathlib import Path

        # Create a valid config.yaml
        config_content = """
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: test-key
default_model: gpt-4
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config_content)

        # Create events for streaming
        events = [
            ("messages-tuple", {"type": "ai", "content": "Hello ", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": "world!", "id": "msg-1"}),
            ("end", {}),
        ]

        # Mock the deerflow client
        mock_client = mock_deerflow_client(events=events)

        # Patch to use our mock
        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Call main_with_args
        try:
            skill.main_with_args(["test prompt"])
        except SystemExit as e:
            # Normal exit
            pass

        captured = capsys.readouterr()
        # Should have streamed output
        assert "Hello" in captured.out or "Hello" in captured.err
        # chat() should not have been called
        mock_client.chat.assert_not_called()
        # stream() should have been called
        mock_client.stream.assert_called_once()

    def test_graph_recursion_error_shows_clear_message(self, mock_deerflow_client, tmp_path, monkeypatch, capsys):
        """Test 2: GraphRecursionError caught and shows clear message."""
        import skill

        # Create a valid config
        config_content = """
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: test-key
default_model: gpt-4
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config_content)

        # Create a mock GraphRecursionError
        class MockGraphRecursionError(Exception):
            pass

        events = [
            ("messages-tuple", {"type": "ai", "content": "Partial", "id": "msg-1"}),
        ]
        mock_client = mock_deerflow_client(events=events, error=MockGraphRecursionError("Recursion limit exceeded"))

        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Should exit with error
        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["test prompt"])

        # Exit code should be 1
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        # Should show actionable message about recursion
        assert "recursion" in captured.err.lower() or "complex" in captured.err.lower()

    def test_keyboard_interrupt_shows_interrupt_message(self, mock_deerflow_client, tmp_path, monkeypatch, capsys):
        """Test 3: KeyboardInterrupt caught and shows interrupt message."""
        import skill

        config_content = """
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: test-key
default_model: gpt-4
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config_content)

        events = [
            ("messages-tuple", {"type": "ai", "content": "Partial", "id": "msg-1"}),
        ]
        mock_client = mock_deerflow_client(events=events, error=KeyboardInterrupt())

        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["test prompt"])

        # Exit code should be 130 (128 + SIGINT=2)
        assert exc_info.value.code == 130

        captured = capsys.readouterr()
        assert "interrupt" in captured.err.lower()

    def test_generic_exception_formatted_with_format_streaming_error(self, mock_deerflow_client, tmp_path, monkeypatch, capsys):
        """Test 4: Generic exceptions formatted with format_streaming_error."""
        import skill

        config_content = """
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: test-key
default_model: gpt-4
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config_content)

        events = [
            ("messages-tuple", {"type": "ai", "content": "Partial", "id": "msg-1"}),
        ]
        mock_client = mock_deerflow_client(events=events, error=TimeoutError("Request timed out"))

        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["test prompt"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        # Should show formatted timeout message
        assert "timeout" in captured.err.lower() or "long" in captured.err.lower()

    def test_exit_codes_correct(self, mock_deerflow_client, tmp_path, monkeypatch):
        """Test 5: Exit code is 1 on error, 130 on interrupt."""
        import skill

        config_content = """
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: test-key
default_model: gpt-4
"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(config_content)

        # Test error exit code (1)
        events = []
        mock_client = mock_deerflow_client(events=events, error=ValueError("Test error"))
        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["test prompt"])
        assert exc_info.value.code == 1

        # Test interrupt exit code (130)
        mock_client = mock_deerflow_client(events=events, error=KeyboardInterrupt())
        monkeypatch.setattr(skill, "_get_deerflow_client", lambda: lambda **kwargs: mock_client)

        with pytest.raises(SystemExit) as exc_info:
            skill.main_with_args(["test prompt"])
        assert exc_info.value.code == 130
