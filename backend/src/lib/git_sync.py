"""Git repository sync utilities for marketplace."""

import os
import shutil
import tempfile
import subprocess
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
import structlog

from models.marketplace import (
    MarketplaceApp, DockerConfig, AppRequirements,
    AppPort, AppVolume, AppEnvVar
)

logger = structlog.get_logger("git_sync")


class GitSync:
    """Handles Git repository synchronization."""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="homelab-marketplace-")
        os.makedirs(self.cache_dir, exist_ok=True)

    def clone_or_pull(self, repo_url: str, branch: str = "main") -> Path:
        """Clone repo or pull if exists. Returns path to repo."""
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
        """Find all app.yaml files in repository."""
        app_files = []

        # Look for apps/ directory first
        apps_dir = repo_path / "apps"
        if apps_dir.exists():
            for app_dir in apps_dir.iterdir():
                if app_dir.is_dir():
                    for yaml_file in ["app.yaml", "app.yml"]:
                        yaml_path = app_dir / yaml_file
                        if yaml_path.exists():
                            app_files.append(yaml_path)
                            break

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
                    env_vars.append(AppEnvVar(name=name, default=default))
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
            author=data.get("author", "Community"),
            license=data.get("license", "MIT"),
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
