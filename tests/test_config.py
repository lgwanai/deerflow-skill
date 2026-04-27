"""Tests for configuration resolution and validation.

Tests the behavior specified in the plan:
- Test 1: When DEER_FLOW_CONFIG_PATH is set and file exists, returns that path
- Test 2: When DEER_FLOW_CONFIG_PATH is not set, checks ./config.yaml first
- Test 3: When ./config.yaml missing, checks ../config.yaml
- Test 4: When all paths fail, raises FileNotFoundError with clear message
- Test 5: Calls create_example_config() when config missing
"""
import os
from pathlib import Path
from unittest import mock

import pytest


class TestResolveConfigPath:
    """Tests for resolve_config_path function."""

    def test_returns_env_path_when_set_and_exists(self, tmp_path: Path, monkeypatch):
        """Test 1: When DEER_FLOW_CONFIG_PATH is set and file exists, returns that path."""
        # Create a config file at a specific location
        config_file = tmp_path / "custom-config.yaml"
        config_file.write_text("models: []")

        # Set the environment variable
        monkeypatch.setenv("DEER_FLOW_CONFIG_PATH", str(config_file))

        # Import after setting env var
        from lib.config import resolve_config_path

        result = resolve_config_path()

        assert result == config_file

    def test_returns_cwd_config_when_env_not_set(self, tmp_path: Path, monkeypatch):
        """Test 2: When DEER_FLOW_CONFIG_PATH is not set, checks ./config.yaml first."""
        # Clear the environment variable
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Create config in current directory
        config_file = tmp_path / "config.yaml"
        config_file.write_text("models: []")

        # Change to tmp_path directory
        with mock.patch.object(Path, "cwd", return_value=tmp_path):
            from lib.config import resolve_config_path

            result = resolve_config_path()

            assert result == config_file

    def test_returns_parent_config_when_cwd_missing(self, tmp_path: Path, monkeypatch):
        """Test 3: When ./config.yaml missing, checks ../config.yaml."""
        # Clear the environment variable
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Create a subdirectory and parent config
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        parent_config = tmp_path / "config.yaml"
        parent_config.write_text("models: []")

        # Mock cwd to be the subdirectory (so parent has config)
        with mock.patch.object(Path, "cwd", return_value=subdir):
            from lib.config import resolve_config_path

            result = resolve_config_path()

            assert result == parent_config

    def test_raises_file_not_found_when_all_paths_fail(self, tmp_path: Path, monkeypatch):
        """Test 4: When all paths fail, raises FileNotFoundError with clear message."""
        # Clear the environment variable
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Create isolated directory with no config
        isolated_dir = tmp_path / "isolated"
        isolated_dir.mkdir()

        # Create a fake parent that also has no config
        fake_parent = tmp_path / "fake_parent"
        fake_parent.mkdir()

        with mock.patch.object(Path, "cwd", return_value=isolated_dir):
            # Mock parent() to return a directory without config
            with mock.patch.object(Path, "parent", new_callable=lambda: mock.PropertyMock(return_value=fake_parent)):
                from lib.config import resolve_config_path

                with pytest.raises(FileNotFoundError) as exc_info:
                    resolve_config_path()

                assert "config.yaml not found" in str(exc_info.value).lower()

    def test_creates_example_config_when_missing(self, tmp_path: Path, monkeypatch):
        """Test 5: Creates config.example.yaml when config is missing."""
        # Clear the environment variable
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        # Create isolated directory with no config
        isolated_dir = tmp_path / "isolated"
        isolated_dir.mkdir()
        fake_parent = tmp_path / "fake_parent"
        fake_parent.mkdir()

        with mock.patch.object(Path, "cwd", return_value=isolated_dir):
            with mock.patch.object(Path, "parent", new_callable=lambda: mock.PropertyMock(return_value=fake_parent)):
                from lib.config import resolve_config_path

                # Should raise FileNotFoundError but also create example config
                with pytest.raises(FileNotFoundError):
                    resolve_config_path()

        # Verify example config was created in cwd
        example_path = isolated_dir / "config.example.yaml"
        assert example_path.exists(), "config.example.yaml should be created when config is missing"


class TestCreateExampleConfig:
    """Tests for create_example_config function."""

    def test_creates_example_config_in_cwd(self, tmp_path: Path):
        """Test that create_example_config creates config.example.yaml in current directory."""
        from lib.config import create_example_config

        with mock.patch.object(Path, "cwd", return_value=tmp_path):
            create_example_config()

        example_path = tmp_path / "config.example.yaml"
        assert example_path.exists()

    def test_example_config_has_required_sections(self, tmp_path: Path):
        """Test that example config contains models section with OpenAI and Anthropic."""
        from lib.config import create_example_config

        with mock.patch.object(Path, "cwd", return_value=tmp_path):
            create_example_config()

        example_path = tmp_path / "config.example.yaml"
        content = example_path.read_text()

        assert "models:" in content
        assert "langchain_openai:ChatOpenAI" in content
        assert "langchain_anthropic:ChatAnthropic" in content
        assert "api_key:" in content


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validates_parseable_yaml(self, tmp_path: Path):
        """Test that validate_config accepts valid YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: "sk-test-key"
""")

        from lib.config import validate_config

        # Should not raise
        validate_config(config_file)

    def test_raises_on_invalid_yaml(self, tmp_path: Path):
        """Test that validate_config raises on invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: : :")

        from lib.config import validate_config

        with pytest.raises(ValueError) as exc_info:
            validate_config(config_file)

        assert "parse" in str(exc_info.value).lower()

    def test_raises_on_missing_credentials(self, tmp_path: Path):
        """Test that validate_config raises when credentials are missing."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: ""
  - name: claude
    use: langchain_anthropic:ChatAnthropic
    api_key: "$MISSING_VAR"
""")

        from lib.config import validate_config

        with pytest.raises(ValueError) as exc_info:
            validate_config(config_file)

        error_msg = str(exc_info.value).lower()
        assert "credential" in error_msg or "api_key" in error_msg


class TestResolveAndValidateConfig:
    """Tests for resolve_and_validate_config convenience function."""

    def test_returns_valid_config_path(self, tmp_path: Path, monkeypatch):
        """Test that resolve_and_validate_config returns path for valid config."""
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: "sk-test-key"
""")

        with mock.patch.object(Path, "cwd", return_value=tmp_path):
            from lib.config import resolve_and_validate_config

            result = resolve_and_validate_config()

            assert result == config_file

    def test_raises_on_missing_config(self, tmp_path: Path, monkeypatch):
        """Test that resolve_and_validate_config raises when config is missing."""
        monkeypatch.delenv("DEER_FLOW_CONFIG_PATH", raising=False)

        isolated_dir = tmp_path / "isolated"
        isolated_dir.mkdir()
        fake_parent = tmp_path / "fake_parent"
        fake_parent.mkdir()

        with mock.patch.object(Path, "cwd", return_value=isolated_dir):
            with mock.patch.object(Path, "parent", new_callable=lambda: mock.PropertyMock(return_value=fake_parent)):
                from lib.config import resolve_and_validate_config

                with pytest.raises(FileNotFoundError):
                    resolve_and_validate_config()