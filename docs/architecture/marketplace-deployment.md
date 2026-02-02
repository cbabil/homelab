# Marketplace & Deployment Architecture

## Overview

The tomo application uses a unified marketplace-based architecture for app discovery and deployment. Apps are sourced exclusively from marketplace repositories, eliminating duplicate definitions.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MARKETPLACE LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Git Repositories              MarketplaceService                   │
│   ┌──────────────┐             ┌─────────────────┐                  │
│   │ Official     │──── sync ──▶│ sync_repo()     │                  │
│   │ Community    │             │ search_apps()   │                  │
│   │ Personal     │             │ get_app()       │                  │
│   └──────────────┘             └────────┬────────┘                  │
│                                         │                            │
│                                         ▼                            │
│                              ┌─────────────────┐                     │
│                              │ MarketplaceApp  │                     │
│                              │ - id, name      │                     │
│                              │ - docker config │                     │
│                              │ - requirements  │                     │
│                              └────────┬────────┘                     │
│                                       │                              │
└───────────────────────────────────────┼──────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   DeploymentService                                                  │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │ 1. Get app from MarketplaceService                      │       │
│   │ 2. Extract DockerConfig (image, ports, volumes, env)    │       │
│   │ 3. Build docker run command                             │       │
│   │ 4. Execute on target server via SSH                     │       │
│   └─────────────────────────────────────────────────────────┘       │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────┐    ┌─────────────┐    ┌──────────────┐          │
│   │ SSHService   │───▶│ Docker Host │───▶│ Container    │          │
│   └──────────────┘    └─────────────┘    └──────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### MarketplaceService

Manages marketplace repositories and app discovery.

**Location:** `backend/src/services/marketplace_service.py`

**Responsibilities:**
- Add/remove/sync git repositories
- Search and filter apps
- Provide app metadata and Docker configuration
- Manage app ratings

**Key Methods:**
```python
async def sync_repo(repo_id: str) -> List[MarketplaceApp]
async def search_apps(search, category, tags, ...) -> List[MarketplaceApp]
async def get_app(app_id: str) -> Optional[MarketplaceApp]
async def get_categories() -> List[dict]
```

### MarketplaceApp Model

Contains all app metadata including Docker deployment configuration.

**Location:** `backend/src/models/marketplace.py`

**Structure:**
```python
class MarketplaceApp:
    id: str                    # Unique identifier
    name: str                  # Display name
    description: str           # Short description
    version: str               # App version
    category: str              # Category (media, storage, etc.)
    tags: List[str]            # Search tags
    docker: DockerConfig       # Docker deployment config
    requirements: AppRequirements
    repo_id: str               # Source repository
    ...
```

### DockerConfig Model

Docker container configuration embedded in each MarketplaceApp.

```python
class DockerConfig:
    image: str                 # Docker image (e.g., "nginx:latest")
    ports: List[AppPort]       # Port mappings
    volumes: List[AppVolume]   # Volume mappings
    environment: List[AppEnvVar]  # Environment variables
    restart_policy: str        # Restart policy
    network_mode: Optional[str]
    privileged: bool
    capabilities: List[str]
```

### DeploymentService

Handles actual container deployment on remote servers.

**Location:** `backend/src/services/deployment_service.py`

**Responsibilities:**
- Get Docker config from MarketplaceService
- Build docker run commands
- Execute commands via SSH
- Track installation status

**Key Methods:**
```python
async def install_app(server_id, app_id, config) -> InstalledApp
async def uninstall_app(server_id, app_id, remove_data) -> bool
async def start_app(server_id, app_id) -> bool
async def stop_app(server_id, app_id) -> bool
```

## Repository Structure

Marketplace repositories contain YAML app definitions:

```
tomo-marketplace/
├── apps/
│   ├── media/
│   │   ├── jellyfin.yaml
│   │   └── plex.yaml
│   ├── storage/
│   │   └── nextcloud.yaml
│   └── networking/
│       └── nginx-proxy-manager.yaml
└── README.md
```

### App Definition Format

```yaml
id: jellyfin
name: Jellyfin
description: Free media server
version: "10.9.11"
category: media
tags:
  - media
  - streaming

author: Jellyfin Contributors
license: GPL-2.0
repository: https://github.com/jellyfin/jellyfin
icon: https://jellyfin.org/images/logo.svg

docker:
  image: jellyfin/jellyfin:latest
  ports:
    - container: 8096
      host: 8096
  volumes:
    - host_path: /var/jellyfin/config
      container_path: /config
    - host_path: /media
      container_path: /media
      readonly: true
  environment:
    - name: TZ
      description: Timezone
      required: false
      default: UTC
  restart_policy: unless-stopped
  privileged: false
  capabilities: []

requirements:
  min_ram: 2048
  min_storage: 1024
  architectures:
    - amd64
    - arm64
```

## Database Tables

### marketplace_repos
Stores configured marketplace repositories.

| Column | Type | Description |
|--------|------|-------------|
| id | string | Repository ID |
| name | string | Display name |
| url | string | Git URL |
| branch | string | Git branch |
| repo_type | enum | official/community/personal |
| enabled | bool | Active for syncing |
| status | enum | active/syncing/error |
| last_synced | datetime | Last sync time |
| app_count | int | Number of apps |

### marketplace_apps
Stores synced app definitions with Docker configs.

| Column | Type | Description |
|--------|------|-------------|
| id | string | App ID |
| name | string | Display name |
| description | text | Short description |
| version | string | App version |
| category | string | Category |
| tags | json | Search tags |
| repo_id | fk | Source repository |
| docker_config | json | Docker configuration |
| requirements | json | System requirements |
| avg_rating | float | Average user rating |
| install_count | int | Installation count |

## Sync Process

1. **Trigger sync** - Manual or scheduled
2. **Clone/pull repo** - GitSync fetches latest
3. **Parse YAML files** - Find all `*.yaml` in apps/
4. **Validate & upsert** - Update marketplace_apps table
5. **Update counts** - Refresh repo app_count

```python
# Example sync flow
repo = await marketplace_service.get_repo("official")
apps = await marketplace_service.sync_repo(repo.id)
# apps now in database, ready for deployment
```

## Deployment Process

1. **User requests install** - app_id + server_id + config
2. **Fetch app** - `marketplace_service.get_app(app_id)`
3. **Extract DockerConfig** - `app.docker`
4. **Build command** - `_build_docker_run_command()`
5. **SSH execute** - Pull image, run container
6. **Track status** - Store in installations table

```python
# Example deployment
installation = await deployment_service.install_app(
    server_id="server-123",
    app_id="jellyfin",
    config={"env": {"TZ": "America/New_York"}}
)
```

## Benefits of This Architecture

1. **Single source of truth** - Apps defined once in marketplace repos
2. **Version controlled** - App definitions tracked in git
3. **Community contributions** - Easy to add/update apps
4. **No local duplication** - Removed legacy YAML catalog
5. **Consistent format** - All apps follow same structure
6. **Ratings & popularity** - Track user preferences locally
