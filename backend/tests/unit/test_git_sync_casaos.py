"""
Unit tests for lib/git_sync.py - CasaOS App Store support.

Tests for CasaOS docker-compose.yml parsing and app loading.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from lib.git_sync import GitSync


class TestCasaOsAppStore:
    """Tests for CasaOS App Store support."""

    def test_find_casaos_app_files(self):
        """Should find docker-compose.yml files in Apps directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Create Apps directory structure
            apps_dir = repo_path / "Apps"
            app1_dir = apps_dir / "Jellyfin"
            app1_dir.mkdir(parents=True)
            (app1_dir / "docker-compose.yml").write_text("test")

            app2_dir = apps_dir / "Nextcloud"
            app2_dir.mkdir(parents=True)
            (app2_dir / "docker-compose.yml").write_text("test")

            sync = GitSync()
            app_files = sync.find_casaos_app_files(repo_path)

            assert len(app_files) == 2
            assert any("Jellyfin" in str(f) for f in app_files)
            assert any("Nextcloud" in str(f) for f in app_files)

    def test_find_casaos_app_files_no_apps_dir(self):
        """Should return empty list when no Apps directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = GitSync()
            app_files = sync.find_casaos_app_files(Path(tmpdir))

            assert len(app_files) == 0

    def test_parse_casaos_docker_compose_basic(self):
        """Should parse basic CasaOS docker-compose.yml."""
        compose_content = """
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    ports:
      - "8096:8096"
    volumes:
      - /data/jellyfin:/config
    environment:
      PUID: "1000"
      PGID: "1000"
x-casaos:
  title:
    en_US: Jellyfin
  description:
    en_US: Free media system
  category: Media
  author: Jellyfin Project
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Jellyfin")

        assert app is not None
        assert app.name == "Jellyfin"
        assert app.docker.image == "jellyfin/jellyfin:latest"
        assert app.category == "Media"
        assert len(app.docker.ports) == 1
        assert app.docker.ports[0].host == 8096
        assert app.docker.ports[0].container == 8096
        assert len(app.docker.volumes) == 1
        assert app.docker.volumes[0].host_path == "/data/jellyfin"

    def test_parse_casaos_docker_compose_no_data(self):
        """Should return None for empty/invalid YAML."""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose("", "casaos", "Invalid")

        assert app is None

    def test_parse_casaos_docker_compose_no_services(self):
        """Should return None when no services defined."""
        compose_content = """
x-casaos:
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is None

    def test_parse_casaos_docker_compose_no_image(self):
        """Should return None when main service has no image."""
        compose_content = """
services:
  app:
    ports:
      - "8080:8080"
x-casaos:
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is None

    def test_parse_casaos_docker_compose_dict_env(self):
        """Should parse dict-style environment variables."""
        compose_content = """
services:
  app:
    image: test:latest
    environment:
      VAR1: value1
      VAR2: value2
x-casaos:
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is not None
        assert len(app.docker.environment) == 2

    def test_parse_casaos_docker_compose_list_env(self):
        """Should parse list-style environment variables."""
        compose_content = """
services:
  app:
    image: test:latest
    environment:
      - VAR1=value1
      - VAR2=value2
x-casaos:
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is not None
        assert len(app.docker.environment) == 2
        assert app.docker.environment[0].name == "VAR1"
        assert app.docker.environment[0].default == "value1"

    def test_parse_casaos_docker_compose_with_main_service(self):
        """Should use specified main service."""
        compose_content = """
services:
  db:
    image: postgres:latest
  web:
    image: nginx:latest
x-casaos:
  main: web
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is not None
        assert app.docker.image == "nginx:latest"

    def test_parse_casaos_docker_compose_nonexistent_main(self):
        """Should return None when main service doesn't exist."""
        compose_content = """
services:
  app:
    image: test:latest
x-casaos:
  main: nonexistent
  title:
    en_US: Test
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(compose_content, "casaos", "Test")

        assert app is None


class TestParseCasaosPort:
    """Tests for CasaOS port parsing."""

    def test_parse_casaos_port_dict_format(self):
        """Should parse dict port specification."""
        sync = GitSync()
        port = sync._parse_casaos_port({"target": 80, "published": 8080})

        assert port is not None
        assert port.container == 80
        assert port.host == 8080

    def test_parse_casaos_port_string_format(self):
        """Should parse string port specification."""
        sync = GitSync()
        port = sync._parse_casaos_port("8080:80")

        assert port is not None
        assert port.container == 80
        assert port.host == 8080

    def test_parse_casaos_port_with_protocol(self):
        """Should parse port with protocol."""
        sync = GitSync()
        port = sync._parse_casaos_port("8080:80/tcp")

        assert port is not None
        assert port.protocol == "tcp"

    def test_parse_casaos_port_invalid(self):
        """Should return None for invalid port."""
        sync = GitSync()
        port = sync._parse_casaos_port("invalid")

        assert port is None

    def test_parse_casaos_port_dict_missing_values(self):
        """Should return None for incomplete dict."""
        sync = GitSync()
        port = sync._parse_casaos_port({"target": 80})

        assert port is None

    def test_parse_casaos_port_value_error(self):
        """Should handle ValueError when parsing non-numeric port."""
        sync = GitSync()
        # This should trigger the ValueError handler (int() on "abc" fails)
        port = sync._parse_casaos_port("abc:def")

        assert port is None

    def test_parse_casaos_port_type_error(self):
        """Should handle TypeError when parsing malformed port spec."""
        sync = GitSync()
        # Dict with non-string/int values that cause TypeError
        port = sync._parse_casaos_port({"target": None, "published": None})

        assert port is None


class TestParseCasaosVolume:
    """Tests for CasaOS volume parsing."""

    def test_parse_casaos_volume_dict_format(self):
        """Should parse dict volume specification."""
        sync = GitSync()
        vol = sync._parse_casaos_volume(
            {"source": "/host/path", "target": "/container/path", "read_only": True}
        )

        assert vol is not None
        assert vol.host_path == "/host/path"
        assert vol.container_path == "/container/path"
        assert vol.readonly is True

    def test_parse_casaos_volume_string_format(self):
        """Should parse string volume specification."""
        sync = GitSync()
        vol = sync._parse_casaos_volume("/host/path:/container/path")

        assert vol is not None
        assert vol.host_path == "/host/path"
        assert vol.container_path == "/container/path"
        assert vol.readonly is False

    def test_parse_casaos_volume_string_readonly(self):
        """Should parse readonly volume."""
        sync = GitSync()
        vol = sync._parse_casaos_volume("/host/path:/container/path:ro")

        assert vol is not None
        assert vol.readonly is True

    def test_parse_casaos_volume_invalid(self):
        """Should return None for invalid volume."""
        sync = GitSync()
        vol = sync._parse_casaos_volume("single-path-no-colon")

        assert vol is None

    def test_parse_casaos_volume_dict_missing_values(self):
        """Should return None for incomplete dict."""
        sync = GitSync()
        vol = sync._parse_casaos_volume({"source": "/path"})

        assert vol is None

    def test_parse_casaos_volume_exception_handling(self):
        """Should handle exceptions during volume parsing."""
        sync = GitSync()
        # Use a mock object that raises exception when accessed
        bad_spec = MagicMock()
        bad_spec.__class__ = dict  # Make isinstance(bad_spec, dict) return True
        bad_spec.get.side_effect = RuntimeError("Unexpected error")

        vol = sync._parse_casaos_volume(bad_spec)

        assert vol is None


class TestLoadCasaosApp:
    """Tests for loading CasaOS apps from file."""

    def test_load_casaos_app_success(self):
        """Should load app from docker-compose.yml file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app_dir = Path(tmpdir) / "Jellyfin"
            app_dir.mkdir()
            compose_file = app_dir / "docker-compose.yml"
            compose_file.write_text("""
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
x-casaos:
  title:
    en_US: Jellyfin
""")
            sync = GitSync()
            app = sync.load_casaos_app(compose_file, "casaos")

            assert app is not None
            assert "jellyfin" in app.name.lower()

    def test_load_casaos_app_invalid_file(self):
        """Should return None for invalid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app_dir = Path(tmpdir) / "Invalid"
            app_dir.mkdir()
            compose_file = app_dir / "docker-compose.yml"
            compose_file.write_text("invalid: yaml: content:")

            sync = GitSync()
            app = sync.load_casaos_app(compose_file, "casaos")

            assert app is None

    def test_load_casaos_app_missing_file(self):
        """Should return None for missing file."""
        sync = GitSync()
        app = sync.load_casaos_app(Path("/nonexistent/file.yml"), "casaos")

        assert app is None
