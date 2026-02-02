# Applications & Deployment

## Entity Relationship Diagram

```mermaid
erDiagram
    app_categories {
        TEXT id PK "Category identifier"
        TEXT name "Category display name"
        TEXT description "Category description"
        TEXT icon "Lucide icon name"
        TEXT color "Color theme classes"
    }

    applications {
        TEXT id PK "Unique app identifier"
        TEXT name "Application name"
        TEXT description "Short description"
        TEXT long_description "Detailed description"
        TEXT version "Current version"
        TEXT category_id FK "References app_categories.id"
        TEXT tags "JSON array of tags"
        TEXT icon "Icon URL"
        TEXT screenshots "JSON array of URLs"
        TEXT author "Application author"
        TEXT repository "Source repo URL"
        TEXT documentation "Docs URL"
        TEXT license "Software license"
        TEXT requirements "JSON: RAM, storage, ports"
        TEXT status "available | installed | installing | error"
        INTEGER install_count "Number of installs"
        REAL rating "User rating 0-5"
        INTEGER featured "Featured flag 0 or 1"
        DATETIME created_at "Creation timestamp"
        DATETIME updated_at "Last update timestamp"
        TEXT connected_server_id FK "Server where installed"
    }

    installed_apps {
        TEXT id PK "Unique installation identifier"
        TEXT server_id FK "References servers.id"
        TEXT app_id FK "References applications.id"
        TEXT container_id "Docker container ID"
        TEXT container_name "Container name"
        TEXT status "pending | pulling | creating | starting | running | stopped | error"
        TEXT config "JSON: ports, volumes, env vars"
        TEXT installed_at "Installation timestamp"
        TEXT started_at "Container start timestamp"
        TEXT error_message "Error details if any"
        TEXT step_durations "JSON: timing for each step"
        TEXT step_started_at "Current step start time"
        TEXT networks "JSON: network configurations"
        TEXT named_volumes "JSON: volume names"
        TEXT bind_mounts "JSON: bind mount paths"
    }

    servers {
        TEXT id PK "Server reference"
    }

    app_categories ||--o{ applications : "contains"
    applications ||--o{ installed_apps : "deployed as"
    servers ||--o{ installed_apps : "runs"
    servers ||--o{ applications : "hosts"
```

## Tables

### `app_categories`
Application category definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Category identifier |
| `name` | TEXT | NOT NULL | Display name |
| `description` | TEXT | NOT NULL | Description |
| `icon` | TEXT | NOT NULL | Lucide icon name |
| `color` | TEXT | NOT NULL | Theme color classes |

---

### `applications`
Local application catalog entries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Application identifier |
| `name` | TEXT | NOT NULL | Application name |
| `description` | TEXT | NOT NULL | Short description |
| `long_description` | TEXT | | Detailed description |
| `version` | TEXT | NOT NULL | Version string |
| `category_id` | TEXT | NOT NULL, FK | Category reference |
| `tags` | TEXT | | JSON array of tags |
| `icon` | TEXT | | Icon URL |
| `screenshots` | TEXT | | JSON array of URLs |
| `author` | TEXT | NOT NULL | Author name |
| `repository` | TEXT | | Source repo URL |
| `documentation` | TEXT | | Docs URL |
| `license` | TEXT | NOT NULL | License type |
| `requirements` | TEXT | | JSON requirements |
| `status` | TEXT | NOT NULL | Installation status |
| `install_count` | INTEGER | | Install count |
| `rating` | REAL | | User rating (0-5) |
| `featured` | INTEGER | DEFAULT 0 | Featured flag |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last update |
| `connected_server_id` | TEXT | | Server where installed |

**Indexes:** `category_id`, `status`, `connected_server_id`
**Foreign Keys:** `category_id` → `app_categories(id)`

---

### `installed_apps`
Tracks deployed application instances on servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Installation identifier |
| `server_id` | TEXT | NOT NULL, FK | Server reference |
| `app_id` | TEXT | NOT NULL | Application reference |
| `container_id` | TEXT | | Docker container ID |
| `container_name` | TEXT | | Container name |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | Deployment status |
| `config` | TEXT | | JSON config (ports, volumes, env) |
| `installed_at` | TEXT | | Installation timestamp |
| `started_at` | TEXT | | Container start time |
| `error_message` | TEXT | | Error details |
| `step_durations` | TEXT | | JSON step timing |
| `step_started_at` | TEXT | | Current step start |
| `networks` | TEXT | | JSON network config |
| `named_volumes` | TEXT | | JSON volume names |
| `bind_mounts` | TEXT | | JSON bind mounts |

**Indexes:** `idx_installed_apps_server`, `idx_installed_apps_status`
**Foreign Keys:** `server_id` → `servers(id)` ON DELETE CASCADE
**Constraints:** UNIQUE(server_id, app_id)
