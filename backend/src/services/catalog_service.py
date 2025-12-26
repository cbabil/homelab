"""
App Catalog Service

Loads and manages application definitions from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
import structlog
from models.app_catalog import AppDefinition, AppCategory, AppPort, AppVolume, AppEnvVar

logger = structlog.get_logger("catalog_service")


class CatalogService:
    """Service for loading and querying app catalog."""

    def __init__(self, catalog_dirs: List[str] = None):
        """Initialize catalog service."""
        self.catalog_dirs = catalog_dirs or []
        self.apps: Dict[str, AppDefinition] = {}
        logger.info("Catalog service initialized", dirs=self.catalog_dirs)

    def _parse_app_file(self, file_path: Path) -> Optional[AppDefinition]:
        """Parse a YAML app definition file."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            # Parse ports
            ports = []
            for p in data.get('ports', []):
                ports.append(AppPort(
                    container=p.get('container'),
                    host=p.get('host'),
                    protocol=p.get('protocol', 'tcp')
                ))

            # Parse volumes
            volumes = []
            for v in data.get('volumes', []):
                if isinstance(v, str):
                    # Format: host:container or host:container:ro
                    parts = v.split(':')
                    volumes.append(AppVolume(
                        host_path=parts[0],
                        container_path=parts[1],
                        readonly=len(parts) > 2 and parts[2] == 'ro'
                    ))
                else:
                    volumes.append(AppVolume(
                        host_path=v.get('host_path'),
                        container_path=v.get('container_path'),
                        readonly=v.get('readonly', False)
                    ))

            # Parse env vars
            env_vars = []
            for e in data.get('env', data.get('env_vars', [])):
                if isinstance(e, str):
                    # Format: NAME=value or NAME
                    if '=' in e:
                        name, default = e.split('=', 1)
                        env_vars.append(AppEnvVar(name=name, default=default))
                    else:
                        env_vars.append(AppEnvVar(name=e, required=True))
                else:
                    env_vars.append(AppEnvVar(
                        name=e.get('name'),
                        description=e.get('description'),
                        required=e.get('required', False),
                        default=e.get('default')
                    ))

            return AppDefinition(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                category=AppCategory(data.get('category', 'utility')),
                image=data['image'],
                ports=ports,
                volumes=volumes,
                env_vars=env_vars,
                restart_policy=data.get('restart_policy', 'unless-stopped'),
                network_mode=data.get('network_mode'),
                privileged=data.get('privileged', False),
                capabilities=data.get('capabilities', [])
            )

        except Exception as e:
            logger.error("Failed to parse app file", file=str(file_path), error=str(e))
            return None

    def load_catalog(self) -> None:
        """Load all app definitions from catalog directories."""
        self.apps = {}

        for dir_path in self.catalog_dirs:
            catalog_dir = Path(dir_path)
            if not catalog_dir.exists():
                logger.warning("Catalog directory not found", path=dir_path)
                continue

            for yaml_file in catalog_dir.glob("*.yaml"):
                app = self._parse_app_file(yaml_file)
                if app:
                    self.apps[app.id] = app
                    logger.debug("Loaded app", app_id=app.id)

            for yml_file in catalog_dir.glob("*.yml"):
                app = self._parse_app_file(yml_file)
                if app:
                    self.apps[app.id] = app
                    logger.debug("Loaded app", app_id=app.id)

        logger.info("Catalog loaded", app_count=len(self.apps))

    def get_app(self, app_id: str) -> Optional[AppDefinition]:
        """Get app definition by ID."""
        return self.apps.get(app_id)

    def list_apps(self, category: str = None) -> List[AppDefinition]:
        """List all apps, optionally filtered by category."""
        apps = list(self.apps.values())

        if category:
            apps = [a for a in apps if a.category.value == category]

        return sorted(apps, key=lambda a: a.name)

    def reload_catalog(self) -> None:
        """Reload catalog from disk."""
        self.load_catalog()
