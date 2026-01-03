"""Tests for configuration loading and validation."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from gitleague_client.config import ConfigLoader, ClientConfig, ProjectConfig, RepositoryConfig
from gitleague_client.exceptions import ConfigError


class TestRepositoryConfig:
    """Test repository configuration."""

    def test_valid_repo_config(self):
        """Test creating valid repository config."""
        repo = RepositoryConfig(
            path="/home/user/repos/my-repo",
            git_url="https://github.com/user/my-repo.git",
        )

        assert repo.path == "/home/user/repos/my-repo"
        assert repo.git_url == "https://github.com/user/my-repo.git"

    def test_repo_path_expansion(self):
        """Test that paths with ~ are expanded."""
        repo = RepositoryConfig(
            path="~/repos/my-repo",
            git_url="https://github.com/user/my-repo.git",
        )

        assert repo.path.startswith("/")
        assert "~" not in repo.path

    def test_repo_env_var_expansion(self):
        """Test that environment variables are expanded."""
        os.environ["TEST_REPO_PATH"] = "/test/path"

        repo = RepositoryConfig(
            path="$TEST_REPO_PATH/repo",
            git_url="https://github.com/user/repo.git",
        )

        assert repo.path == "/test/path/repo"

    def test_repo_ssh_authentication(self):
        """Test SSH authentication config."""
        repo = RepositoryConfig(
            path="~/repos/repo",
            git_url="git@github.com:user/repo.git",
            ssh_key="~/.ssh/id_ed25519",
        )

        assert repo.ssh_key is not None
        assert "~" not in repo.ssh_key  # Path expanded

    def test_repo_https_with_token(self):
        """Test HTTPS authentication with token."""
        os.environ["GITHUB_TOKEN"] = "ghp_xxxxxxxxxxxx"

        repo = RepositoryConfig(
            path="~/repos/repo",
            git_url="https://github.com/user/repo.git",
            username="myuser",
            password_env="GITHUB_TOKEN",
        )

        assert repo.get_password() == "ghp_xxxxxxxxxxxx"

    def test_repo_password_env_missing(self):
        """Test getting password when env var not set."""
        repo = RepositoryConfig(
            path="~/repos/repo",
            git_url="https://github.com/user/repo.git",
            username="myuser",
            password_env="NONEXISTENT_VAR",
        )

        assert repo.get_password() is None


class TestProjectConfig:
    """Test project configuration."""

    def test_valid_project_config(self):
        """Test creating valid project config."""
        project = ProjectConfig(
            name="My Project",
            project_id="550e8400-e29b-41d4-a716-446655440000",
            repos=[
                RepositoryConfig(
                    path="~/repo1",
                    git_url="https://github.com/org/repo1.git",
                )
            ],
        )

        assert project.name == "My Project"
        assert len(project.repos) == 1


class TestClientConfig:
    """Test client configuration."""

    def test_valid_client_config(self):
        """Test creating valid client config."""
        config = ClientConfig(
            api_url="https://api.example.com",
            api_key="tgl_test_key",
            projects=[
                ProjectConfig(
                    name="Project",
                    project_id="id",
                    repos=[
                        RepositoryConfig(
                            path="~/repo",
                            git_url="https://github.com/org/repo.git",
                        )
                    ],
                )
            ],
        )

        assert config.api_url == "https://api.example.com"
        assert config.api_key == "tgl_test_key"
        assert config.batch_size == 100
        assert config.max_retries == 3

    def test_api_key_from_env(self):
        """Test API key from environment variable."""
        os.environ["GITLEAGUE_API_KEY"] = "tgl_env_key"

        config = ClientConfig(
            api_url="https://api.example.com",
            api_key=None,
            projects=[],
        )

        assert config.api_key == "tgl_env_key"

    def test_api_key_missing(self):
        """Test error when API key not provided."""
        # Remove env var if it exists
        os.environ.pop("GITLEAGUE_API_KEY", None)

        with pytest.raises(ValueError, match="API key"):
            ClientConfig(
                api_url="https://api.example.com",
                api_key=None,
                projects=[],
            )

    def test_batch_size_validation(self):
        """Test batch size validation."""
        with pytest.raises(ValueError, match="batch_size"):
            ClientConfig(
                api_url="https://api.example.com",
                api_key="tgl_key",
                batch_size=1001,
                projects=[],
            )

        with pytest.raises(ValueError, match="batch_size"):
            ClientConfig(
                api_url="https://api.example.com",
                api_key="tgl_key",
                batch_size=0,
                projects=[],
            )

    def test_max_retries_validation(self):
        """Test max_retries validation."""
        with pytest.raises(ValueError, match="max_retries"):
            ClientConfig(
                api_url="https://api.example.com",
                api_key="tgl_key",
                max_retries=-1,
                projects=[],
            )


class TestConfigLoader:
    """Test YAML config loading."""

    def test_load_valid_config(self):
        """Test loading valid YAML config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "api_url": "https://api.example.com",
                "api_key": "tgl_test_key",
                "batch_size": 100,
                "max_retries": 3,
                "projects": [
                    {
                        "name": "Test Project",
                        "project_id": "test-id",
                        "repos": [
                            {
                                "path": "~/test-repo",
                                "git_url": "https://github.com/test/repo.git",
                            }
                        ],
                    }
                ],
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            config = ConfigLoader.load(config_file)

            assert config.api_url == "https://api.example.com"
            assert config.api_key == "tgl_test_key"
            assert len(config.projects) == 1
            assert config.projects[0].name == "Test Project"

        finally:
            Path(config_file).unlink()

    def test_load_missing_file(self):
        """Test loading non-existent file."""
        with pytest.raises(ConfigError, match="not found"):
            ConfigLoader.load("/nonexistent/config.yaml")

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:")
            config_file = f.name

        try:
            with pytest.raises(ConfigError, match="Invalid YAML"):
                ConfigLoader.load(config_file)
        finally:
            Path(config_file).unlink()

    def test_load_empty_file(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_file = f.name

        try:
            with pytest.raises(ConfigError, match="empty"):
                ConfigLoader.load(config_file)
        finally:
            Path(config_file).unlink()

    def test_load_path_expansion(self):
        """Test that ~ is expanded in file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config in temp directory
            config_file = Path(tmpdir) / "test.yaml"
            config_data = {
                "api_url": "https://api.example.com",
                "api_key": "tgl_key",
                "projects": [],
            }
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Load with relative path
            config = ConfigLoader.load(str(config_file))
            assert config.api_url == "https://api.example.com"
