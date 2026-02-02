"""Git repository sync utilities for marketplace."""

import os
import re
import shutil
import tempfile
import subprocess
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Any

import yaml
import structlog

from models.marketplace import (
    MarketplaceApp, DockerConfig, AppRequirements,
    AppPort, AppVolume, AppEnvVar
)

logger = structlog.get_logger("git_sync")

# Valid git URL patterns (HTTPS and SSH)
VALID_GIT_URL_PATTERN = re.compile(
    r'^https?://[\w\-\.]+(/[\w\-\.]+)+(/[\w\-\.]+)*(\.git)?$|'  # HTTPS URLs
    r'^git@[\w\-\.]+:[\w\-\.]+(/[\w\-\.]+)*(\.git)?$'  # SSH URLs
)

# Valid branch name pattern (alphanumeric, hyphens, underscores, slashes, dots)
VALID_BRANCH_PATTERN = re.compile(r'^[\w\-\./]+$')


def validate_git_url(url: str) -> None:
    """Validate git repository URL format."""
    if not url or not VALID_GIT_URL_PATTERN.match(url):
        raise ValueError(f"Invalid git repository URL: {url}")


def validate_branch_name(branch: str) -> None:
    """Validate git branch name format."""
    if not branch or not VALID_BRANCH_PATTERN.match(branch):
        raise ValueError(f"Invalid branch name: {branch}")
    # Prevent path traversal
    if '..' in branch:
        raise ValueError(f"Invalid branch name (path traversal): {branch}")


# CasaOS App Store configuration
CASAOS_APPSTORE_URL = "https://github.com/IceWhaleTech/CasaOS-AppStore"
CASAOS_APPSTORE_BRANCH = "main"


class GitSync:
    """Handles Git repository synchronization."""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="tomo-marketplace-")
        os.makedirs(self.cache_dir, exist_ok=True)

    def clone_or_pull(self, repo_url: str, branch: str = "main") -> Path:
        """Clone repo or pull if exists. Returns path to repo."""
        # Validate inputs before executing git commands
        validate_git_url(repo_url)
        validate_branch_name(branch)

        # Create safe directory name from URL
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_path = Path(self.cache_dir) / repo_name

        try:
            if repo_path.exists():
                # Pull latest
                subprocess.run(
                    ["git", "-C", str(repo_path), "fetch", "origin", branch],
                    check=True, capture_output=True
                )
                subprocess.run(
                    ["git", "-C", str(repo_path), "reset", "--hard", f"origin/{branch}"],
                    check=True, capture_output=True
                )
                logger.debug("Pulled latest", repo=repo_name, branch=branch)
            else:
                # Clone
                subprocess.run(
                    ["git", "clone", "--branch", branch, "--depth", "1", repo_url, str(repo_path)],
                    check=True, capture_output=True
                )
                logger.debug("Cloned repo", repo=repo_name, branch=branch)

            return repo_path

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else "No error message"
            logger.error("Git operation failed", repo=repo_url, error=stderr)
            raise RuntimeError(f"Git operation failed: {stderr}")

    def find_app_files(self, repo_path: Path) -> List[Path]:
        """Find all app.yaml files in repository.

        Supports multiple directory structures:
        - apps/<app>/app.yaml (flat structure)
        - apps/<category>/<app>/app.yaml (category structure)
        - app.yaml (single-app repo root)
        """
        app_files = []

        # Look for apps/ directory first
        apps_dir = repo_path / "apps"
        if apps_dir.exists():
            # Use glob to find all app.yaml/app.yml files recursively
            for yaml_file in ["app.yaml", "app.yml"]:
                app_files.extend(apps_dir.glob(f"**/{yaml_file}"))

        # Also check root for single-app repos
        for yaml_file in ["app.yaml", "app.yml"]:
            yaml_path = repo_path / yaml_file
            if yaml_path.exists():
                app_files.append(yaml_path)

        return app_files

    def parse_app_yaml(self, content: str, repo_id: str) -> MarketplaceApp:
        """Parse YAML content into MarketplaceApp."""
        data = yaml.safe_load(content)

        # Parse docker config
        docker_data = data.get("docker", {})
        ports = [
            AppPort(
                container=p.get("container", p) if isinstance(p, dict) else p,
                host=p.get("host", p) if isinstance(p, dict) else p,
                protocol=p.get("protocol", "tcp") if isinstance(p, dict) else "tcp"
            )
            for p in docker_data.get("ports", [])
        ]

        volumes = []
        for v in docker_data.get("volumes", []):
            if isinstance(v, str):
                parts = v.split(":")
                volumes.append(AppVolume(
                    host_path=parts[0],
                    container_path=parts[1] if len(parts) > 1 else parts[0],
                    readonly=len(parts) > 2 and parts[2] == "ro"
                ))
            else:
                volumes.append(AppVolume(
                    host_path=v.get("host_path", v.get("host", "")),
                    container_path=v.get("container_path", v.get("container", "")),
                    readonly=v.get("readonly", False)
                ))

        env_vars = []
        for e in docker_data.get("environment", docker_data.get("env", [])):
            if isinstance(e, str):
                if "=" in e:
                    name, default = e.split("=", 1)
                    env_vars.append(AppEnvVar(name=name, default=default, required=False))
                else:
                    env_vars.append(AppEnvVar(name=e, required=True))
            else:
                env_vars.append(AppEnvVar(
                    name=e.get("name"),
                    description=e.get("description"),
                    required=e.get("required", False),
                    default=e.get("default")
                ))

        # Validate docker image is non-empty
        docker_image = docker_data.get("image", "")
        if not docker_image:
            raise ValueError("docker.image is required and cannot be empty")

        docker_config = DockerConfig(
            image=docker_image,
            ports=ports,
            volumes=volumes,
            environment=env_vars,
            restart_policy=docker_data.get("restart_policy", "unless-stopped"),
            network_mode=docker_data.get("network_mode"),
            privileged=docker_data.get("privileged", False),
            capabilities=docker_data.get("capabilities", [])
        )

        # Parse requirements
        req_data = data.get("requirements", {})
        requirements = AppRequirements(
            min_ram=req_data.get("min_ram"),
            min_storage=req_data.get("min_storage"),
            architectures=req_data.get("architectures", ["amd64", "arm64"])
        )

        now = datetime.now(UTC)

        return MarketplaceApp(
            id=data.get("id", data.get("name", "").lower().replace(" ", "-")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            long_description=data.get("long_description"),
            version=data.get("version", "1.0.0"),
            category=data.get("category", "utility"),
            tags=data.get("tags", []),
            icon=data.get("icon"),
            author=data.get("author", ""),
            license=data.get("license", ""),
            maintainers=data.get("maintainers", []),
            repository=data.get("repository"),
            documentation=data.get("documentation"),
            repo_id=repo_id,
            docker=docker_config,
            requirements=requirements,
            install_count=0,
            avg_rating=0.0,
            rating_count=0,
            featured=False,
            created_at=now,
            updated_at=now
        )

    def load_app_from_file(self, file_path: Path, repo_id: str) -> Optional[MarketplaceApp]:
        """Load and parse an app.yaml file."""
        try:
            content = file_path.read_text()
            return self.parse_app_yaml(content, repo_id)
        except Exception as e:
            logger.error("Failed to parse app file", path=str(file_path), error=str(e))
            return None

    def cleanup(self):
        """Remove cached repositories."""
        if self.cache_dir and Path(self.cache_dir).exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)

    # ─────────────────────────────────────────────────────────────
    # CasaOS App Store Support
    # ─────────────────────────────────────────────────────────────

    def find_casaos_app_files(self, repo_path: Path) -> List[Path]:
        """Find all docker-compose.yml files in CasaOS Apps directory."""
        app_files = []
        apps_dir = repo_path / "Apps"

        if apps_dir.exists():
            for docker_file in apps_dir.glob("*/docker-compose.yml"):
                app_files.append(docker_file)

        logger.debug("Found CasaOS app files", count=len(app_files))
        return app_files

    def parse_casaos_docker_compose(self, content: str, repo_id: str, app_dir_name: str) -> Optional[MarketplaceApp]:
        """Parse CasaOS docker-compose.yml into MarketplaceApp.

        CasaOS uses standard docker-compose format with x-casaos extension.
        """
        try:
            data = yaml.safe_load(content)
            if not data:
                return None

            # Get x-casaos metadata
            casaos_meta = data.get("x-casaos", {})
            services = data.get("services", {})

            if not services:
                logger.warning("No services found in docker-compose", app=app_dir_name)
                return None

            # Get main service (CasaOS specifies this in x-casaos.main)
            main_service_name = casaos_meta.get("main", list(services.keys())[0])
            main_service = services.get(main_service_name, {})

            if not main_service:
                logger.warning("Main service not found", app=app_dir_name, main=main_service_name)
                return None

            # Extract image
            docker_image = main_service.get("image", "")
            if not docker_image:
                logger.warning("No image specified", app=app_dir_name)
                return None

            # Parse ports
            ports = []
            for port_spec in main_service.get("ports", []):
                port_info = self._parse_casaos_port(port_spec)
                if port_info:
                    ports.append(port_info)

            # Parse volumes
            volumes = []
            for vol_spec in main_service.get("volumes", []):
                vol_info = self._parse_casaos_volume(vol_spec)
                if vol_info:
                    volumes.append(vol_info)

            # Parse environment variables
            env_vars = []
            env_data = main_service.get("environment", {})
            if isinstance(env_data, dict):
                for name, value in env_data.items():
                    env_vars.append(AppEnvVar(
                        name=name,
                        default=str(value) if value else None,
                        required=False
                    ))
            elif isinstance(env_data, list):
                for env_item in env_data:
                    if isinstance(env_item, str) and "=" in env_item:
                        name, value = env_item.split("=", 1)
                        env_vars.append(AppEnvVar(name=name, default=value, required=False))

            # Build DockerConfig
            docker_config = DockerConfig(
                image=docker_image,
                ports=ports,
                volumes=volumes,
                environment=env_vars,
                restart_policy=main_service.get("restart", "unless-stopped"),
                network_mode=main_service.get("network_mode"),
                privileged=main_service.get("privileged", False),
                capabilities=main_service.get("cap_add", [])
            )

            # Extract metadata from x-casaos
            title = casaos_meta.get("title", {})
            description = casaos_meta.get("description", {})
            tagline = casaos_meta.get("tagline", {})

            # Get English versions (fallback to first available)
            app_name = title.get("en_US", title.get("en_GB", app_dir_name)) if isinstance(title, dict) else app_dir_name
            app_description = ""
            if isinstance(description, dict):
                app_description = description.get("en_US", description.get("en_GB", ""))
            app_tagline = ""
            if isinstance(tagline, dict):
                app_tagline = tagline.get("en_US", tagline.get("en_GB", ""))

            # Use tagline as short description if available
            short_desc = app_tagline if app_tagline else (app_description[:200] if app_description else "")

            # Parse requirements
            architectures = casaos_meta.get("architectures", ["amd64", "arm64"])
            requirements = AppRequirements(
                min_ram=None,
                min_storage=None,
                architectures=architectures
            )

            # Extract version from image tag
            version = "latest"
            if ":" in docker_image:
                version = docker_image.split(":")[-1]

            now = datetime.now(UTC)
            app_id = app_dir_name.lower().replace(" ", "-")

            return MarketplaceApp(
                id=f"casaos-{app_id}",
                name=app_name,
                description=short_desc,
                long_description=app_description if len(app_description) > 200 else None,
                version=version,
                category=casaos_meta.get("category", "Utilities"),
                tags=[],
                icon=casaos_meta.get("icon"),
                author=casaos_meta.get("author", casaos_meta.get("developer", "CasaOS Community")),
                license="Open Source",
                maintainers=[],
                repository=None,
                documentation=None,
                repo_id=repo_id,
                docker=docker_config,
                requirements=requirements,
                install_count=0,
                avg_rating=0.0,
                rating_count=0,
                featured=False,
                created_at=now,
                updated_at=now
            )

        except Exception as e:
            logger.error("Failed to parse CasaOS docker-compose", app=app_dir_name, error=str(e))
            return None

    def _parse_casaos_port(self, port_spec: Any) -> Optional[AppPort]:
        """Parse CasaOS port specification."""
        try:
            if isinstance(port_spec, dict):
                target = port_spec.get("target", port_spec.get("container_port"))
                published = port_spec.get("published", port_spec.get("host_port"))
                protocol = port_spec.get("protocol", "tcp")
                if target and published:
                    return AppPort(
                        container=int(target),
                        host=int(str(published).strip('"')),
                        protocol=protocol
                    )
            elif isinstance(port_spec, str):
                # Handle "8080:80" or "8080:80/tcp" format
                port_str = port_spec.split("/")[0]
                protocol = port_spec.split("/")[1] if "/" in port_spec else "tcp"
                if ":" in port_str:
                    parts = port_str.split(":")
                    host_port = parts[0]
                    container_port = parts[1] if len(parts) > 1 else parts[0]
                    return AppPort(
                        container=int(container_port),
                        host=int(host_port),
                        protocol=protocol
                    )
        except (ValueError, TypeError) as e:
            logger.debug("Failed to parse port", spec=port_spec, error=str(e))
        return None

    def _parse_casaos_volume(self, vol_spec: Any) -> Optional[AppVolume]:
        """Parse CasaOS volume specification."""
        try:
            if isinstance(vol_spec, dict):
                source = vol_spec.get("source", vol_spec.get("host_path", ""))
                target = vol_spec.get("target", vol_spec.get("container_path", ""))
                readonly = vol_spec.get("read_only", False)
                if source and target:
                    return AppVolume(
                        host_path=source,
                        container_path=target,
                        readonly=readonly
                    )
            elif isinstance(vol_spec, str):
                # Handle "/host/path:/container/path" or "/host/path:/container/path:ro"
                parts = vol_spec.split(":")
                if len(parts) >= 2:
                    return AppVolume(
                        host_path=parts[0],
                        container_path=parts[1],
                        readonly=len(parts) > 2 and parts[2] == "ro"
                    )
        except Exception as e:
            logger.debug("Failed to parse volume", spec=vol_spec, error=str(e))
        return None

    def load_casaos_app(self, file_path: Path, repo_id: str) -> Optional[MarketplaceApp]:
        """Load and parse a CasaOS docker-compose.yml file."""
        try:
            content = file_path.read_text()
            app_dir_name = file_path.parent.name
            return self.parse_casaos_docker_compose(content, repo_id, app_dir_name)
        except Exception as e:
            logger.error("Failed to load CasaOS app", path=str(file_path), error=str(e))
            return None
