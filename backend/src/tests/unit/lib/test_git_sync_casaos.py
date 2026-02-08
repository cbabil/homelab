"""
Unit tests for lib/git_sync.py - CasaOS functionality

Tests CasaOS App Store integration and docker-compose parsing.
"""

from unittest.mock import patch

from lib.git_sync import GitSync


class TestFindCasaosAppFiles:
    """Tests for find_casaos_app_files method."""

    def test_find_casaos_apps(self, tmp_path):
        """find_casaos_app_files should find docker-compose.yml files."""
        apps_dir = tmp_path / "Apps" / "Jellyfin"
        apps_dir.mkdir(parents=True)
        (apps_dir / "docker-compose.yml").touch()

        sync = GitSync()
        files = sync.find_casaos_app_files(tmp_path)

        assert len(files) == 1
        assert files[0].name == "docker-compose.yml"

    def test_find_casaos_multiple_apps(self, tmp_path):
        """find_casaos_app_files should find multiple apps."""
        for app_name in ["Jellyfin", "Plex", "Emby"]:
            app_dir = tmp_path / "Apps" / app_name
            app_dir.mkdir(parents=True)
            (app_dir / "docker-compose.yml").touch()

        sync = GitSync()
        files = sync.find_casaos_app_files(tmp_path)
        assert len(files) == 3

    def test_find_casaos_no_apps_dir(self, tmp_path):
        """find_casaos_app_files should handle missing Apps directory."""
        sync = GitSync()
        files = sync.find_casaos_app_files(tmp_path)
        assert files == []


class TestParseCasaosDockerCompose:
    """Tests for parse_casaos_docker_compose method."""

    def test_parse_basic_casaos_app(self):
        """parse_casaos_docker_compose should parse basic CasaOS app."""
        content = """
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    ports:
      - "8096:8096"
x-casaos:
  title:
    en_US: Jellyfin
  description:
    en_US: Free media system
  category: Media
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "casaos-store", "Jellyfin")

        assert app is not None
        assert app.name == "Jellyfin"
        assert app.docker.image == "jellyfin/jellyfin:latest"
        assert app.category == "Media"

    def test_parse_casaos_with_main_service(self):
        """parse_casaos_docker_compose should use main service from x-casaos."""
        content = """
services:
  app:
    image: app:latest
  db:
    image: postgres:latest
x-casaos:
  main: app
  title:
    en_US: My App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "MyApp")

        assert app.docker.image == "app:latest"

    def test_parse_casaos_with_dict_ports(self):
        """parse_casaos_docker_compose should parse dict port format."""
        content = """
services:
  app:
    image: app:latest
    ports:
      - target: 8080
        published: 8080
        protocol: tcp
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert len(app.docker.ports) == 1
        assert app.docker.ports[0].container == 8080
        assert app.docker.ports[0].host == 8080

    def test_parse_casaos_with_dict_volumes(self):
        """parse_casaos_docker_compose should parse dict volume format."""
        content = """
services:
  app:
    image: app:latest
    volumes:
      - source: /data
        target: /app/data
        read_only: true
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert len(app.docker.volumes) == 1
        assert app.docker.volumes[0].host_path == "/data"
        assert app.docker.volumes[0].readonly is True

    def test_parse_casaos_with_string_volumes(self):
        """parse_casaos_docker_compose should parse string volume format."""
        content = """
services:
  app:
    image: app:latest
    volumes:
      - /host:/container
      - /config:/app/config:ro
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert len(app.docker.volumes) == 2
        assert app.docker.volumes[1].readonly is True

    def test_parse_casaos_with_dict_environment(self):
        """parse_casaos_docker_compose should parse dict environment."""
        content = """
services:
  app:
    image: app:latest
    environment:
      DATABASE_URL: postgres://localhost/db
      DEBUG: "true"
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert len(app.docker.environment) == 2

    def test_parse_casaos_with_list_environment(self):
        """parse_casaos_docker_compose should parse list environment."""
        content = """
services:
  app:
    image: app:latest
    environment:
      - DATABASE_URL=postgres://localhost/db
      - DEBUG=true
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert len(app.docker.environment) == 2
        assert app.docker.environment[0].name == "DATABASE_URL"

    def test_parse_casaos_no_services(self):
        """parse_casaos_docker_compose should return None if no services."""
        content = """
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")
        assert app is None

    def test_parse_casaos_no_image(self):
        """parse_casaos_docker_compose should return None if no image."""
        content = """
services:
  app:
    ports:
      - "8080:8080"
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")
        assert app is None

    def test_parse_casaos_empty_content(self):
        """parse_casaos_docker_compose should return None for empty content."""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose("", "store", "App")
        assert app is None

    def test_parse_casaos_invalid_yaml(self):
        """parse_casaos_docker_compose should return None for invalid YAML."""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose("invalid: yaml: :", "store", "App")
        assert app is None

    def test_parse_casaos_version_from_image_tag(self):
        """parse_casaos_docker_compose should extract version from image tag."""
        content = """
services:
  app:
    image: myapp:v1.2.3
x-casaos:
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert app.version == "v1.2.3"

    def test_parse_casaos_tagline_as_description(self):
        """parse_casaos_docker_compose should use tagline as short description."""
        content = """
services:
  app:
    image: app:latest
x-casaos:
  title:
    en_US: My App
  tagline:
    en_US: A short tagline
  description:
    en_US: A much longer description that goes into detail
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert app.description == "A short tagline"

    def test_parse_casaos_author_fallback(self):
        """parse_casaos_docker_compose should fallback to developer."""
        content = """
services:
  app:
    image: app:latest
x-casaos:
  title:
    en_US: App
  developer: Original Developer
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert app.author == "Original Developer"

    def test_parse_casaos_with_architectures(self):
        """parse_casaos_docker_compose should parse architectures."""
        content = """
services:
  app:
    image: app:latest
x-casaos:
  title:
    en_US: App
  architectures:
    - amd64
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")

        assert app.requirements.architectures == ["amd64"]

    def test_parse_casaos_main_service_not_found(self):
        """parse_casaos_docker_compose should handle missing main service."""
        content = """
services:
  app:
    image: app:latest
x-casaos:
  main: nonexistent
  title:
    en_US: App
"""
        sync = GitSync()
        app = sync.parse_casaos_docker_compose(content, "store", "App")
        assert app is None


class TestParseCasaosPort:
    """Tests for _parse_casaos_port method."""

    def test_parse_dict_port_with_target_published(self):
        """_parse_casaos_port should parse dict with target/published."""
        sync = GitSync()
        port = sync._parse_casaos_port(
            {"target": 8080, "published": 9090, "protocol": "udp"}
        )

        assert port is not None
        assert port.container == 8080
        assert port.host == 9090
        assert port.protocol == "udp"

    def test_parse_dict_port_with_container_host(self):
        """_parse_casaos_port should parse dict with container_port/host_port."""
        sync = GitSync()
        port = sync._parse_casaos_port({"container_port": 8080, "host_port": 9090})

        assert port is not None
        assert port.container == 8080
        assert port.host == 9090

    def test_parse_string_port(self):
        """_parse_casaos_port should parse string port."""
        sync = GitSync()
        port = sync._parse_casaos_port("8080:80")

        assert port is not None
        assert port.container == 80
        assert port.host == 8080

    def test_parse_string_port_with_protocol(self):
        """_parse_casaos_port should parse string port with protocol."""
        sync = GitSync()
        port = sync._parse_casaos_port("8080:80/udp")

        assert port is not None
        assert port.container == 80
        assert port.host == 8080
        assert port.protocol == "udp"

    def test_parse_invalid_port(self):
        """_parse_casaos_port should return None for invalid port."""
        sync = GitSync()
        assert sync._parse_casaos_port("invalid") is None
        assert sync._parse_casaos_port({}) is None
        assert sync._parse_casaos_port(None) is None

    def test_parse_port_value_error(self):
        """_parse_casaos_port should handle ValueError from int conversion."""
        sync = GitSync()
        # Dict with non-integer values triggers ValueError
        port = sync._parse_casaos_port({"target": "not_a_number", "published": 8080})
        assert port is None

    def test_parse_port_string_value_error(self):
        """_parse_casaos_port should handle ValueError from string port."""
        sync = GitSync()
        port = sync._parse_casaos_port("abc:def")
        assert port is None

    def test_parse_port_with_quoted_published(self):
        """_parse_casaos_port should handle quoted published port."""
        sync = GitSync()
        port = sync._parse_casaos_port({"target": 8080, "published": '"9090"'})

        assert port is not None
        assert port.host == 9090


class TestParseCasaosVolume:
    """Tests for _parse_casaos_volume method."""

    def test_parse_dict_volume_source_target(self):
        """_parse_casaos_volume should parse dict with source/target."""
        sync = GitSync()
        vol = sync._parse_casaos_volume(
            {"source": "/host/data", "target": "/container/data", "read_only": True}
        )

        assert vol is not None
        assert vol.host_path == "/host/data"
        assert vol.container_path == "/container/data"
        assert vol.readonly is True

    def test_parse_dict_volume_host_container_path(self):
        """_parse_casaos_volume should parse dict with host_path/container_path."""
        sync = GitSync()
        vol = sync._parse_casaos_volume(
            {"host_path": "/host/data", "container_path": "/container/data"}
        )

        assert vol is not None
        assert vol.host_path == "/host/data"

    def test_parse_string_volume(self):
        """_parse_casaos_volume should parse string volume."""
        sync = GitSync()
        vol = sync._parse_casaos_volume("/host:/container")

        assert vol is not None
        assert vol.host_path == "/host"
        assert vol.container_path == "/container"

    def test_parse_string_volume_readonly(self):
        """_parse_casaos_volume should parse string volume with ro flag."""
        sync = GitSync()
        vol = sync._parse_casaos_volume("/host:/container:ro")

        assert vol is not None
        assert vol.readonly is True

    def test_parse_invalid_volume(self):
        """_parse_casaos_volume should return None for invalid volume."""
        sync = GitSync()
        assert sync._parse_casaos_volume("invalid") is None
        assert sync._parse_casaos_volume({}) is None
        assert sync._parse_casaos_volume(None) is None

    @patch("lib.git_sync.AppVolume")
    def test_parse_volume_exception(self, mock_app_volume):
        """_parse_casaos_volume should handle exceptions from AppVolume."""
        mock_app_volume.side_effect = Exception("Validation error")
        sync = GitSync()
        vol = sync._parse_casaos_volume("/host:/container")
        assert vol is None


class TestLoadCasaosApp:
    """Tests for load_casaos_app method."""

    def test_load_valid_casaos_app(self, tmp_path):
        """load_casaos_app should load valid docker-compose.yml."""
        app_dir = tmp_path / "Jellyfin"
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
        assert app.name == "Jellyfin"

    def test_load_invalid_casaos_app(self, tmp_path):
        """load_casaos_app should return None for invalid file."""
        app_dir = tmp_path / "BadApp"
        app_dir.mkdir()
        compose_file = app_dir / "docker-compose.yml"
        compose_file.write_text("invalid: yaml: :")

        sync = GitSync()
        app = sync.load_casaos_app(compose_file, "casaos")
        assert app is None

    def test_load_missing_casaos_app(self, tmp_path):
        """load_casaos_app should return None for missing file."""
        sync = GitSync()
        app = sync.load_casaos_app(tmp_path / "missing.yml", "casaos")
        assert app is None
