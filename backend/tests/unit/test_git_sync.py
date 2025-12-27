import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from lib.git_sync import GitSync


def test_parse_app_yaml():
    yaml_content = """
name: jellyfin
version: 10.8.13
description: Free media system
category: media
tags:
  - streaming
  - movies
docker:
  image: jellyfin/jellyfin:latest
  ports:
    - container: 8096
      host: 8096
"""
    sync = GitSync()
    app = sync.parse_app_yaml(yaml_content, "official")

    assert app.name == "jellyfin"
    assert app.category == "media"
    assert app.docker.image == "jellyfin/jellyfin:latest"
    assert len(app.docker.ports) == 1
    assert app.docker.ports[0].container == 8096
    assert app.docker.ports[0].host == 8096
    assert app.tags == ["streaming", "movies"]


def test_parse_app_yaml_with_volumes():
    yaml_content = """
name: test-app
version: 1.0.0
description: Test app
category: utility
docker:
  image: test:latest
  volumes:
    - host_path: /data
      container_path: /app/data
      readonly: false
"""
    sync = GitSync()
    app = sync.parse_app_yaml(yaml_content, "test-repo")

    assert len(app.docker.volumes) == 1
    assert app.docker.volumes[0].host_path == "/data"
    assert app.docker.volumes[0].container_path == "/app/data"
    assert app.docker.volumes[0].readonly is False


def test_parse_app_yaml_with_string_volumes():
    yaml_content = """
name: test-app
version: 1.0.0
description: Test app
category: utility
docker:
  image: test:latest
  volumes:
    - /data:/app/data
    - /config:/app/config:ro
"""
    sync = GitSync()
    app = sync.parse_app_yaml(yaml_content, "test-repo")

    assert len(app.docker.volumes) == 2
    assert app.docker.volumes[0].host_path == "/data"
    assert app.docker.volumes[0].container_path == "/app/data"
    assert app.docker.volumes[0].readonly is False
    assert app.docker.volumes[1].readonly is True


def test_parse_app_yaml_with_env_vars():
    yaml_content = """
name: test-app
version: 1.0.0
description: Test app
category: utility
docker:
  image: test:latest
  environment:
    - name: DATABASE_URL
      description: Database connection string
      required: true
    - name: API_KEY
      default: secret123
      required: false
"""
    sync = GitSync()
    app = sync.parse_app_yaml(yaml_content, "test-repo")

    assert len(app.docker.environment) == 2
    assert app.docker.environment[0].name == "DATABASE_URL"
    assert app.docker.environment[0].required is True
    assert app.docker.environment[1].name == "API_KEY"
    assert app.docker.environment[1].default == "secret123"


def test_find_app_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create apps directory structure
        apps_dir = repo_path / "apps"
        app1_dir = apps_dir / "app1"
        app1_dir.mkdir(parents=True)
        (app1_dir / "app.yaml").write_text("test")

        app2_dir = apps_dir / "app2"
        app2_dir.mkdir(parents=True)
        (app2_dir / "app.yml").write_text("test")

        # Create root level app.yaml
        (repo_path / "app.yaml").write_text("test")

        sync = GitSync()
        app_files = sync.find_app_files(repo_path)

        # Should find all three files
        assert len(app_files) == 3
        assert any("app1" in str(f) for f in app_files)
        assert any("app2" in str(f) for f in app_files)
        assert any(f == repo_path / "app.yaml" for f in app_files)


def test_load_app_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "app.yaml"
        app_file.write_text("""
name: test-app
version: 1.0.0
description: Test application
category: testing
docker:
  image: test:latest
""")

        sync = GitSync()
        app = sync.load_app_from_file(app_file, "test-repo")

        assert app is not None
        assert app.name == "test-app"
        assert app.version == "1.0.0"
        assert app.repo_id == "test-repo"


def test_load_app_from_file_invalid():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "app.yaml"
        app_file.write_text("invalid: yaml: content:")

        sync = GitSync()
        app = sync.load_app_from_file(app_file, "test-repo")

        # Should return None on error
        assert app is None


@patch('subprocess.run')
def test_clone_or_pull_clone(mock_run):
    # Mock subprocess to create the directory
    def side_effect(*args, **kwargs):
        cmd = args[0]
        if "clone" in cmd:
            # Extract target directory from git clone command
            target_dir = cmd[-1]
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        return MagicMock(returncode=0)

    mock_run.side_effect = side_effect

    with tempfile.TemporaryDirectory() as tmpdir:
        sync = GitSync(cache_dir=tmpdir)
        repo_path = sync.clone_or_pull("https://github.com/test/repo.git", "main")

        assert repo_path.exists()
        # Verify git clone was called
        assert mock_run.call_count == 1
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "clone"


@patch('subprocess.run')
def test_clone_or_pull_pull(mock_run):
    mock_run.return_value = MagicMock(returncode=0)

    with tempfile.TemporaryDirectory() as tmpdir:
        sync = GitSync(cache_dir=tmpdir)

        # Create existing repo directory
        repo_dir = Path(tmpdir) / "repo"
        repo_dir.mkdir()

        repo_path = sync.clone_or_pull("https://github.com/test/repo.git", "main")

        # Verify git fetch and reset were called
        assert mock_run.call_count == 2
        fetch_call = mock_run.call_args_list[0][0][0]
        assert "fetch" in fetch_call


@patch('subprocess.run')
def test_clone_or_pull_error(mock_run):
    # Simulate git error
    mock_run.side_effect = Exception("Git command failed")
    mock_run.return_value = MagicMock(returncode=1, stderr=b"error message")

    with tempfile.TemporaryDirectory() as tmpdir:
        sync = GitSync(cache_dir=tmpdir)

        with pytest.raises(Exception):
            sync.clone_or_pull("https://github.com/test/repo.git", "main")


def test_cleanup():
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = GitSync(cache_dir=tmpdir)

        # Create some test files
        test_file = Path(sync.cache_dir) / "test.txt"
        test_file.write_text("test")

        assert test_file.exists()

        # Cleanup should remove the cache directory
        sync.cleanup()

        assert not Path(sync.cache_dir).exists()
