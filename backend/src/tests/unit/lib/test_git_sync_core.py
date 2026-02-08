"""
Unit tests for lib/git_sync.py - Core functionality

Tests Git repository sync utilities for marketplace (validation, clone/pull, app parsing).
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.git_sync import (
    CASAOS_APPSTORE_BRANCH,
    CASAOS_APPSTORE_URL,
    VALID_BRANCH_PATTERN,
    VALID_GIT_URL_PATTERN,
    GitSync,
    validate_branch_name,
    validate_git_url,
)


class TestConstants:
    """Tests for module constants."""

    def test_casaos_appstore_url(self):
        """CASAOS_APPSTORE_URL should be a GitHub URL."""
        assert "github.com" in CASAOS_APPSTORE_URL
        assert "CasaOS" in CASAOS_APPSTORE_URL

    def test_casaos_appstore_branch(self):
        """CASAOS_APPSTORE_BRANCH should be 'main'."""
        assert CASAOS_APPSTORE_BRANCH == "main"

    def test_valid_git_url_pattern_type(self):
        """VALID_GIT_URL_PATTERN should be a compiled regex."""
        import re

        assert isinstance(VALID_GIT_URL_PATTERN, re.Pattern)

    def test_valid_branch_pattern_type(self):
        """VALID_BRANCH_PATTERN should be a compiled regex."""
        import re

        assert isinstance(VALID_BRANCH_PATTERN, re.Pattern)


class TestValidateGitUrl:
    """Tests for validate_git_url function."""

    def test_valid_https_url(self):
        """validate_git_url should accept valid HTTPS URLs."""
        validate_git_url("https://github.com/user/repo")
        validate_git_url("https://github.com/user/repo.git")
        validate_git_url("https://gitlab.com/user/repo")

    def test_valid_https_url_with_subgroups(self):
        """validate_git_url should accept HTTPS URLs with subgroups."""
        validate_git_url("https://github.com/org/subgroup/repo")
        validate_git_url("https://gitlab.com/a/b/c/repo.git")

    def test_valid_ssh_url(self):
        """validate_git_url should accept valid SSH URLs."""
        validate_git_url("git@github.com:user/repo")
        validate_git_url("git@github.com:user/repo.git")
        validate_git_url("git@gitlab.com:org/repo")

    def test_invalid_url_empty(self):
        """validate_git_url should reject empty URL."""
        with pytest.raises(ValueError) as exc_info:
            validate_git_url("")
        assert "Invalid git repository URL" in str(exc_info.value)

    def test_invalid_url_none(self):
        """validate_git_url should reject None."""
        with pytest.raises(ValueError) as exc_info:
            validate_git_url(None)
        assert "Invalid git repository URL" in str(exc_info.value)

    def test_invalid_url_malformed(self):
        """validate_git_url should reject malformed URLs."""
        with pytest.raises(ValueError) as exc_info:
            validate_git_url("not-a-url")
        assert "Invalid git repository URL" in str(exc_info.value)

    def test_invalid_url_javascript(self):
        """validate_git_url should reject javascript: URLs."""
        with pytest.raises(ValueError) as exc_info:
            validate_git_url("javascript:alert(1)")
        assert "Invalid git repository URL" in str(exc_info.value)


class TestValidateBranchName:
    """Tests for validate_branch_name function."""

    def test_valid_branch_simple(self):
        """validate_branch_name should accept simple branch names."""
        validate_branch_name("main")
        validate_branch_name("master")
        validate_branch_name("develop")

    def test_valid_branch_with_slashes(self):
        """validate_branch_name should accept branches with slashes."""
        validate_branch_name("feature/new-feature")
        validate_branch_name("release/v1.0.0")
        validate_branch_name("hotfix/bug-fix")

    def test_valid_branch_with_hyphens_underscores(self):
        """validate_branch_name should accept hyphens and underscores."""
        validate_branch_name("my-branch")
        validate_branch_name("my_branch")
        validate_branch_name("my-branch_name")

    def test_valid_branch_with_dots(self):
        """validate_branch_name should accept dots."""
        validate_branch_name("v1.0.0")
        validate_branch_name("release.candidate")

    def test_invalid_branch_empty(self):
        """validate_branch_name should reject empty branch."""
        with pytest.raises(ValueError) as exc_info:
            validate_branch_name("")
        assert "Invalid branch name" in str(exc_info.value)

    def test_invalid_branch_none(self):
        """validate_branch_name should reject None."""
        with pytest.raises(ValueError) as exc_info:
            validate_branch_name(None)
        assert "Invalid branch name" in str(exc_info.value)

    def test_invalid_branch_path_traversal(self):
        """validate_branch_name should reject path traversal."""
        with pytest.raises(ValueError) as exc_info:
            validate_branch_name("../etc/passwd")
        assert "path traversal" in str(exc_info.value).lower()

    def test_invalid_branch_special_chars(self):
        """validate_branch_name should reject special characters."""
        with pytest.raises(ValueError) as exc_info:
            validate_branch_name("branch;rm -rf /")
        assert "Invalid branch name" in str(exc_info.value)


class TestGitSyncInit:
    """Tests for GitSync initialization."""

    def test_init_default_cache_dir(self):
        """GitSync should create temp cache dir by default."""
        sync = GitSync()
        assert sync.cache_dir is not None
        assert "tomo-marketplace-" in sync.cache_dir
        sync.cleanup()

    def test_init_custom_cache_dir(self, tmp_path):
        """GitSync should use provided cache dir."""
        cache_dir = str(tmp_path / "custom-cache")
        sync = GitSync(cache_dir=cache_dir)
        assert sync.cache_dir == cache_dir
        assert Path(cache_dir).exists()


class TestCloneOrPull:
    """Tests for clone_or_pull method."""

    @patch("subprocess.run")
    def test_clone_new_repo(self, mock_run, tmp_path):
        """clone_or_pull should clone new repositories."""

        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "clone" in cmd:
                Path(cmd[-1]).mkdir(parents=True, exist_ok=True)
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect
        sync = GitSync(cache_dir=str(tmp_path))
        repo_path = sync.clone_or_pull("https://github.com/test/repo.git", "main")

        assert repo_path.exists()
        assert mock_run.call_count == 1
        call_args = mock_run.call_args[0][0]
        assert "clone" in call_args

    @patch("subprocess.run")
    def test_pull_existing_repo(self, mock_run, tmp_path):
        """clone_or_pull should pull existing repositories."""
        mock_run.return_value = MagicMock(returncode=0)

        # Create existing repo
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        sync = GitSync(cache_dir=str(tmp_path))
        sync.clone_or_pull("https://github.com/test/repo.git", "main")

        assert mock_run.call_count == 2  # fetch + reset

    @patch("subprocess.run")
    def test_clone_or_pull_git_error(self, mock_run, tmp_path):
        """clone_or_pull should raise on git errors."""
        mock_error = subprocess.CalledProcessError(1, ["git", "clone"])
        mock_error.stderr = b"fatal: repository not found"
        mock_run.side_effect = mock_error

        sync = GitSync(cache_dir=str(tmp_path))
        with pytest.raises(RuntimeError) as exc_info:
            sync.clone_or_pull("https://github.com/test/repo.git", "main")
        assert "repository not found" in str(exc_info.value)

    @patch("subprocess.run")
    def test_clone_or_pull_no_stderr(self, mock_run, tmp_path):
        """clone_or_pull should handle missing stderr."""
        mock_error = subprocess.CalledProcessError(1, ["git", "clone"])
        mock_error.stderr = None
        mock_run.side_effect = mock_error

        sync = GitSync(cache_dir=str(tmp_path))
        with pytest.raises(RuntimeError) as exc_info:
            sync.clone_or_pull("https://github.com/test/repo.git", "main")
        assert "No error message" in str(exc_info.value)

    def test_clone_or_pull_invalid_url(self, tmp_path):
        """clone_or_pull should validate URL before cloning."""
        sync = GitSync(cache_dir=str(tmp_path))
        with pytest.raises(ValueError) as exc_info:
            sync.clone_or_pull("not-a-valid-url", "main")
        assert "Invalid git repository URL" in str(exc_info.value)

    def test_clone_or_pull_invalid_branch(self, tmp_path):
        """clone_or_pull should validate branch name."""
        sync = GitSync(cache_dir=str(tmp_path))
        with pytest.raises(ValueError) as exc_info:
            sync.clone_or_pull("https://github.com/test/repo.git", "../etc")
        assert "path traversal" in str(exc_info.value).lower()


class TestFindAppFiles:
    """Tests for find_app_files method."""

    def test_find_in_apps_directory(self, tmp_path):
        """find_app_files should find files in apps/ directory."""
        apps_dir = tmp_path / "apps" / "myapp"
        apps_dir.mkdir(parents=True)
        (apps_dir / "app.yaml").touch()

        sync = GitSync()
        files = sync.find_app_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "app.yaml"

    def test_find_yml_extension(self, tmp_path):
        """find_app_files should find .yml files."""
        apps_dir = tmp_path / "apps" / "myapp"
        apps_dir.mkdir(parents=True)
        (apps_dir / "app.yml").touch()

        sync = GitSync()
        files = sync.find_app_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "app.yml"

    def test_find_in_root_directory(self, tmp_path):
        """find_app_files should find app.yaml in root."""
        (tmp_path / "app.yaml").touch()

        sync = GitSync()
        files = sync.find_app_files(tmp_path)
        assert len(files) == 1

    def test_find_in_nested_categories(self, tmp_path):
        """find_app_files should find files in category subdirectories."""
        cat_dir = tmp_path / "apps" / "media" / "jellyfin"
        cat_dir.mkdir(parents=True)
        (cat_dir / "app.yaml").touch()

        sync = GitSync()
        files = sync.find_app_files(tmp_path)
        assert len(files) == 1

    def test_find_empty_directory(self, tmp_path):
        """find_app_files should handle empty directories."""
        sync = GitSync()
        files = sync.find_app_files(tmp_path)
        assert files == []


class TestParseAppYaml:
    """Tests for parse_app_yaml method."""

    def test_parse_basic_app(self):
        """parse_app_yaml should parse basic app definition."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test application
category: utility
docker:
  image: test:latest
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "test-repo")

        assert app.name == "test-app"
        assert app.version == "1.0.0"
        assert app.docker.image == "test:latest"
        assert app.repo_id == "test-repo"

    def test_parse_app_with_ports(self):
        """parse_app_yaml should parse port configurations."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  ports:
    - container: 8080
      host: 8080
    - container: 443
      host: 443
      protocol: udp
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.ports) == 2
        assert app.docker.ports[0].container == 8080
        assert app.docker.ports[1].protocol == "udp"

    def test_parse_app_with_simple_port(self):
        """parse_app_yaml should handle integer ports."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  ports:
    - 8080
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.ports) == 1
        assert app.docker.ports[0].container == 8080

    def test_parse_app_with_volumes_dict(self):
        """parse_app_yaml should parse dict volumes."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  volumes:
    - host_path: /data
      container_path: /app/data
      readonly: true
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.volumes) == 1
        assert app.docker.volumes[0].host_path == "/data"
        assert app.docker.volumes[0].readonly is True

    def test_parse_app_with_volumes_string(self):
        """parse_app_yaml should parse string volumes."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  volumes:
    - /host:/container
    - /config:/app/config:ro
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.volumes) == 2
        assert app.docker.volumes[0].host_path == "/host"
        assert app.docker.volumes[0].container_path == "/container"
        assert app.docker.volumes[1].readonly is True

    def test_parse_app_with_env_vars_dict(self):
        """parse_app_yaml should parse dict environment variables."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  environment:
    - name: DATABASE_URL
      description: Database connection
      required: true
    - name: API_KEY
      default: secret
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.environment) == 2
        assert app.docker.environment[0].name == "DATABASE_URL"
        assert app.docker.environment[0].required is True
        assert app.docker.environment[1].default == "secret"

    def test_parse_app_with_env_vars_string_equals(self):
        """parse_app_yaml should parse string env vars with equals sign."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  environment:
    - DATABASE_URL=postgres://localhost/db
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.environment) == 1
        assert app.docker.environment[0].name == "DATABASE_URL"
        assert app.docker.environment[0].default == "postgres://localhost/db"
        assert app.docker.environment[0].required is False

    def test_parse_app_with_env_vars_string_no_equals(self):
        """parse_app_yaml should parse string env vars without equals sign."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
  environment:
    - REQUIRED_VAR
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert len(app.docker.environment) == 1
        assert app.docker.environment[0].name == "REQUIRED_VAR"
        assert app.docker.environment[0].required is True

    def test_parse_app_missing_image(self):
        """parse_app_yaml should raise when docker.image is missing."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  ports:
    - 8080
"""
        sync = GitSync()
        with pytest.raises(ValueError) as exc_info:
            sync.parse_app_yaml(yaml_content, "repo")
        assert "docker.image is required" in str(exc_info.value)

    def test_parse_app_with_requirements(self):
        """parse_app_yaml should parse requirements."""
        yaml_content = """
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
requirements:
  min_ram: 512
  min_storage: 1024
  architectures:
    - amd64
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")

        assert app.requirements.min_ram == 512
        assert app.requirements.min_storage == 1024
        assert app.requirements.architectures == ["amd64"]

    def test_parse_app_id_from_name(self):
        """parse_app_yaml should generate id from name."""
        yaml_content = """
name: My App Name
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
"""
        sync = GitSync()
        app = sync.parse_app_yaml(yaml_content, "repo")
        assert app.id == "my-app-name"


class TestLoadAppFromFile:
    """Tests for load_app_from_file method."""

    def test_load_valid_file(self, tmp_path):
        """load_app_from_file should load valid YAML file."""
        app_file = tmp_path / "app.yaml"
        app_file.write_text("""
name: test-app
version: 1.0.0
description: Test
category: utility
docker:
  image: test:latest
""")
        sync = GitSync()
        app = sync.load_app_from_file(app_file, "repo")

        assert app is not None
        assert app.name == "test-app"

    def test_load_invalid_yaml(self, tmp_path):
        """load_app_from_file should return None for invalid YAML."""
        app_file = tmp_path / "app.yaml"
        app_file.write_text("invalid: yaml: content: :")

        sync = GitSync()
        app = sync.load_app_from_file(app_file, "repo")
        assert app is None

    def test_load_missing_file(self, tmp_path):
        """load_app_from_file should return None for missing file."""
        sync = GitSync()
        app = sync.load_app_from_file(tmp_path / "missing.yaml", "repo")
        assert app is None


class TestCleanup:
    """Tests for cleanup method."""

    def test_cleanup_removes_cache(self, tmp_path):
        """cleanup should remove cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "test.txt").touch()

        sync = GitSync(cache_dir=str(cache_dir))
        sync.cleanup()

        assert not cache_dir.exists()

    def test_cleanup_nonexistent_dir(self, tmp_path):
        """cleanup should handle nonexistent directory."""
        sync = GitSync(cache_dir=str(tmp_path / "nonexistent"))
        sync.cleanup()  # Should not raise
