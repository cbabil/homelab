# Tomo v1.0 - Production Roadmap

## Product Overview

A self-hosted web application for managing tomo infrastructure. Users install via RPM package, connect to remote servers via SSH, and deploy Docker applications through a curated + extensible catalog.

**Target Users:** Tomo enthusiasts, sysadmins managing multiple servers

**Deployment Model:**
- Packaged as `.rpm` (RHEL/Fedora/Rocky)
- Runs as systemd service
- HTTP on localhost (user adds reverse proxy for HTTPS)
- SQLite database for persistence

## Technical Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastMCP, SQLite, Paramiko |
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Packaging | RPM (systemd service) |
| Target OS | RHEL/Rocky/Fedora |

## Key Design Decisions

- **Extensible app catalog:** YAML definitions, users can add custom apps
- **Multi-user with roles:** Admin creates users, role-based access
- **Built-in metrics:** Dashboard in UI + JSON API for integrations
- **Manual backup:** Export/import encrypted archive
- **HTTP only:** User provides reverse proxy for HTTPS

## Out of Scope for v1.0

- Self-registration (admin creates users)
- Scheduled backups (manual export only)
- Built-in HTTPS / Let's Encrypt
- Kubernetes support
- SaaS / multi-tenant features

---

## Phase 1: Foundation & Auth

**Goal:** A working application shell with secure authentication, ready to build features on.

### Backend Deliverables
- FastMCP server with health endpoints (`/health`, `/api/status`)
- SQLite database with migrations system
- User model with roles (admin, user)
- Auth service: JWT tokens, bcrypt password hashing, session management
- First-run setup: create initial admin account
- Structured logging to file (JSON format)
- Configuration via environment variables or config file

### Frontend Deliverables
- React + TypeScript + Vite setup
- Login page with form validation
- Protected route wrapper (redirect if not authenticated)
- App shell layout (sidebar nav, header with user menu)
- Auth context/provider for global auth state
- Logout functionality
- Basic error handling (toast notifications)

### MCP Tools
- `login(username, password)` → JWT token
- `logout()` → invalidate session
- `get_current_user()` → user profile
- `create_user(username, email, password, role)` → admin only
- `list_users()` → admin only

### Quality Gates
- [ ] Backend unit tests (90% coverage)
- [ ] Frontend component tests
- [ ] E2E test: login flow
- [ ] Security: no plaintext passwords, JWT expiry works
- [ ] Linting/type-check passes

### Definition of Done
Admin can install the app, create first account via CLI, log in via browser, and see an empty dashboard.

---

## Phase 2: Server Management

**Goal:** Users can add, test, and manage SSH connections to their tomo servers.

### Backend Deliverables
- Server model (id, name, host, port, username, auth_type, status)
- Encrypted credential storage (AES-256 for passwords/SSH keys)
- SSH service using Paramiko:
  - Connection testing with timeout
  - Host key verification (warn on first connect, reject on mismatch)
  - Support for password and key-based auth
- Server CRUD operations with validation

### Frontend Deliverables
- Servers list page (table with status indicators)
- Add server modal/form:
  - Host, port, username fields
  - Auth type toggle (password vs SSH key)
  - SSH key paste/upload
- Test connection button with real-time feedback
- Edit/delete server actions
- Connection status badges (online, offline, error)

### MCP Tools
- `add_server(name, host, port, username, auth_type, credentials)` → server_id
- `test_connection(server_id)` → success + latency + system info
- `list_servers()` → all servers with status
- `get_server(server_id)` → server details
- `update_server(server_id, ...)` → update config
- `delete_server(server_id)` → remove server + credentials

### Quality Gates
- [ ] Credentials never logged or exposed in responses
- [ ] SSH connection tests work with real servers
- [ ] E2E test: add server, test connection, delete server
- [ ] Input validation (hostname format, port range)

### Definition of Done
User can add a remote server, test SSH connectivity, see it in the list, and remove it.

---

## Phase 3: Server Preparation

**Goal:** Automatically prepare target servers with Docker and prerequisites, ready to run containerized apps.

### Backend Deliverables
- Preparation service with step-by-step execution:
  1. Detect OS (Ubuntu, Debian, RHEL, Rocky, Fedora)
  2. Update package manager
  3. Install dependencies (curl, ca-certificates)
  4. Install Docker (official repo method)
  5. Start and enable Docker service
  6. Add user to docker group
  7. Verify Docker installation
- Preparation status tracking (pending, in_progress, completed, failed)
- Rollback capability on failure
- Preparation log storage per server

### Frontend Deliverables
- Server detail page with preparation status
- "Prepare Server" button (disabled if already prepared)
- Progress stepper showing current step
- Real-time log output during preparation
- Success/failure feedback with actionable errors
- "Retry" option on failure

### MCP Tools
- `prepare_server(server_id)` → preparation_id
- `get_preparation_status(server_id)` → status + current step + logs
- `get_preparation_log(server_id)` → full log history
- `retry_preparation(server_id)` → restart from failed step

### Quality Gates
- [ ] Works on Ubuntu 22.04, Debian 12, Rocky 9
- [ ] Idempotent (re-running doesn't break anything)
- [ ] Graceful failure with clear error messages
- [ ] E2E test: prepare fresh VM (can use Vagrant for testing)

### Definition of Done
User clicks "Prepare Server" on a fresh VM, watches progress, and ends with Docker installed and verified.

---

## Phase 4: App Deployment

**Goal:** Users browse an extensible catalog and deploy Docker applications to their servers with one click.

### Backend Deliverables
- App definition schema (YAML format):
  ```yaml
  id: nextcloud
  name: Nextcloud
  description: Personal cloud storage
  category: storage
  image: nextcloud:latest
  ports:
    - container: 80
      host: 8080
  volumes:
    - /var/nextcloud/data:/var/www/html
  env:
    - MYSQL_HOST: required
  ```
- Catalog loader (built-in + user custom directories)
- Docker deployment service:
  - Pull image
  - Create container with config
  - Start container
  - Health check
- Installation tracking (installed apps per server)
- Uninstall with cleanup (stop, remove container, optionally remove volumes)

### Frontend Deliverables
- App catalog page (grid/list view with search + category filter)
- App detail modal (description, ports, requirements)
- Install wizard:
  - Select target server
  - Configure ports/env vars
  - Confirm and deploy
- Installed apps view per server
- App status badges (running, stopped, error)
- Uninstall action with confirmation

### MCP Tools
- `list_catalog()` → all available apps
- `get_app_definition(app_id)` → full app config
- `install_app(server_id, app_id, config)` → installation_id
- `get_installed_apps(server_id)` → installed apps with status
- `uninstall_app(server_id, app_id, remove_data?)` → cleanup result
- `start_app(server_id, app_id)` / `stop_app(server_id, app_id)`

### Curated Apps for v1.0
- Portainer
- Nginx Proxy Manager
- Nextcloud
- Jellyfin
- Pi-hole

### Quality Gates
- [ ] Custom app definitions load correctly
- [ ] Install/uninstall cycle works cleanly
- [ ] E2E test: install Portainer, verify running, uninstall

### Definition of Done
User browses catalog, installs Portainer on a prepared server, sees it running, and can uninstall it.

---

## Phase 5: Monitoring & Logs

**Goal:** Built-in dashboard showing server health, app status, and activity logs. API available for integrations.

### Backend Deliverables
- Monitoring service (polls servers on interval):
  - CPU, memory, disk usage
  - Docker container status
  - Network connectivity
- Metrics storage in SQLite (time-series, configurable retention)
- Activity log service:
  - User actions (login, add server, install app)
  - System events (preparation complete, app crashed)
- Metrics API endpoints (JSON format)

### Frontend Deliverables
- Dashboard page:
  - Server health cards (CPU/RAM/disk bars)
  - App status overview (running/stopped counts)
  - Recent activity feed
- Server detail metrics:
  - Resource usage charts (last 24h, 7d, 30d)
  - Container resource breakdown
- Logs page:
  - Filterable by server, action type, date range
  - Search functionality
  - Pagination
- Auto-refresh toggle for real-time updates

### MCP Tools
- `get_server_metrics(server_id, period?)` → resource usage data
- `get_app_metrics(server_id, app_id, period?)` → container metrics
- `get_activity_logs(filters?)` → paginated log entries
- `get_dashboard_summary()` → aggregated stats for all servers

### API Endpoints (JSON)
- `GET /api/metrics/servers` → all server metrics
- `GET /api/metrics/servers/{id}` → single server
- `GET /api/logs` → activity logs with query params

### Quality Gates
- [ ] Metrics collection doesn't overload target servers
- [ ] Dashboard loads in < 2 seconds
- [ ] Log filtering works correctly
- [ ] API returns proper JSON with pagination

### Definition of Done
User sees dashboard with server health, drills into metrics, browses activity logs, and can query the API externally.

---

## Phase 6: Production Hardening

**Goal:** Security audit, backup/restore, RPM packaging, and documentation. Ready for public release.

### Security Hardening
- Input validation on all MCP tools (Pydantic strict mode)
- Rate limiting on auth endpoints
- User enumeration prevention (constant-time responses)
- Session timeout and forced logout
- Audit logging for sensitive actions
- Dependency vulnerability scan (pip-audit, npm audit)
- OWASP Top 10 review and fixes

### Backup & Restore
- Export command: `tomo export --output backup.enc`
  - Exports: users, servers, credentials, settings, app configs
  - Encrypted with user-provided password
- Import command: `tomo import backup.enc`
  - Validates backup integrity
  - Handles conflicts (overwrite vs skip)
- UI: Settings → Export/Import buttons

### RPM Packaging
- Spec file for rpmbuild
- Systemd service unit
- Post-install script:
  - Creates tomo user
  - Sets up data directory
  - Initializes database
- Config file: `/etc/tomo/config.yaml`
- Log location: `/var/log/tomo/`
- Data location: `/var/lib/tomo/`

### Documentation
- Installation guide (RPM + manual)
- User guide (all features)
- Admin guide (user management, backup, troubleshooting)
- API reference
- Custom app catalog format spec
- Reverse proxy setup examples (nginx, Caddy)

### Quality Gates
- [ ] Security audit passes (no critical/high issues)
- [ ] RPM installs cleanly on Rocky 9
- [ ] Backup/restore works end-to-end
- [ ] All docs reviewed and accurate
- [ ] Full E2E test suite passes

### Definition of Done
User installs via `dnf install`, runs through all features, exports backup, and can restore on fresh install.

---

## Summary

| Phase | Focus | Key Deliverable |
|-------|-------|-----------------|
| **1** | Foundation & Auth | Login, user management, app shell |
| **2** | Server Management | SSH connections, credential storage |
| **3** | Server Preparation | Auto-install Docker on VMs |
| **4** | App Deployment | Extensible catalog, install/uninstall |
| **5** | Monitoring & Logs | Dashboard, metrics, activity logs |
| **6** | Production Hardening | Security, backup, RPM, docs |

---

**Document Version:** 1.0
**Created:** 2025-12-25
