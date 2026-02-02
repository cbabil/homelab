# Tomo Management - TODO

## Summary

**Total Items: 78**

---

## Easy (Quick Wins) - 20 items

These can be done quickly with minimal complexity.

### Assets & Branding
- [ ] Add logos from tomo/assets (source PNGs have transparency issue)
- [x] Add copyright footer to /login, /setup, and main app layout

### Project Files
- [x] Add LICENSE file to project root (MIT)
- [x] Add CONTRIBUTING.md guidelines for contributors
- [x] Add CHANGELOG.md to track version history

### Code Cleanup
- [x] Remove console.log statements from production code
- [x] Fix ESLint disables and @ts-ignore comments (added config override)

### Bug Fixes
- [x] Fix `lib/git_sync.py:157` - `parse_app_yaml` missing `required` field when parsing string env vars with "=" (e.g., `DATABASE_URL=postgres://localhost/db`)

### CI/CD Setup
- [x] Set up Dependabot for dependency security scanning
- [x] Add code coverage reporting to CI (Codecov v4)

### Documentation (Simple)
- [x] Document environment variables (docs/ENV_REFERENCE.md)
- [x] Document installation methods (docs/INSTALLATION.md)

### User Guides (Short)
- [x] Write User Guide: CLI Reference (docs/CLI_REFERENCE.md)
- [x] Write User Guide: Troubleshooting & FAQ (docs/TROUBLESHOOTING.md)

### Quick Tests
- [x] Playwright E2E tests for sign out functionality
- [x] Playwright E2E tests for dark/light theme toggle
- [x] Playwright E2E tests for clear cache functionality
- [x] Write tests for sign out functionality (authOperations.test.ts)
- [x] Write unit tests for clear cache functionality (cacheUtils.test.ts)
- [x] Add CLI tests for auth.ts

---

## Medium (Moderate Effort) - 38 items

These require more work but are straightforward.

### i18n Compliance (All Pages)
- [x] Make /login page i18n compliant and write tests
- [x] Make /setup page i18n compliant and write tests
- [x] Make side menu i18n compliant and write unit tests
- [x] Make dashboard page i18n compliant and write unit tests
- [x] Make servers page i18n compliant and write unit tests
- [x] Make applications page i18n compliant and write unit tests
- [x] Make access logs page i18n compliant and write unit tests
- [x] Make audit logs page i18n compliant and write unit tests
- [x] Make marketplace page i18n compliant and write unit tests
- [x] Make profile page i18n compliant and write unit tests
- [x] Make settings page i18n compliant and write unit tests

### Playwright E2E Tests
- [x] Playwright E2E tests for /login page (auth-flow.e2e.test.ts)
- [x] Playwright E2E tests for /setup page (setup-page.spec.ts)
- [x] Playwright E2E tests for dashboard page (dashboard.spec.ts)
- [x] Playwright E2E tests for servers page (servers-page.spec.ts)
- [x] Playwright E2E tests for applications page (applications-layout.spec.ts)
- [x] Playwright E2E tests for access logs page (logs-page.spec.ts)
- [x] Playwright E2E tests for audit logs page (logs-page.spec.ts)
- [x] Playwright E2E tests for marketplace page (marketplace-page.spec.ts)
- [x] Playwright E2E tests for notifications (notifications.spec.ts)
- [x] Playwright E2E tests for profile page (profile-page.spec.ts)
- [x] Playwright E2E tests for settings page (multiple settings specs)

### Unit Tests
- [x] Fix SecuritySettings.test.tsx frontend tests
- [x] Write unit tests for every settings tab
- [x] Add CLI tests for mcp-client.ts
- [x] Add CLI tests for patch.ts (update functionality)
- [x] Add CLI integration tests for commands (admin, user, update)

### Code Quality
- [x] Fix type safety issues (already well-typed, `any` only in tests)
- [x] Add React ErrorBoundary component for graceful error handling
- [x] Add loading skeletons instead of spinners for better UX

### User Guides (Detailed)
- [x] Write User Guide: Getting Started / Quick Start (docs/user-guides/QUICK_START.md)
- [x] Write User Guide: Server Management (docs/user-guides/SERVER_MANAGEMENT.md)
- [x] Write User Guide: Application Deployment from Marketplace (docs/user-guides/APPLICATION_DEPLOYMENT.md)
- [x] Write User Guide: Settings & Configuration (docs/user-guides/SETTINGS_CONFIGURATION.md)
- [x] Write User Guide: User Management & Security (docs/user-guides/USER_MANAGEMENT.md)
- [x] Write User Guide: Backup & Restore (docs/user-guides/BACKUP_RESTORE.md)

### Developer Documentation
- [x] Document API/MCP tools for developers (docs/mcp/tools.md)
- [x] Document database schema (docs/DATABASE_SCHEMA.md)

---

## Hard (Significant Effort) - 20 items

These require substantial development work or complex implementation.

### Features
- [x] Auto-connect marketplace after admin account creation on /setup (SetupPage.tsx)
- [x] Replace fake notification data with real backend (notifications table, MCP tools, NotificationProvider)
- [x] Fix Access Logs page to use backend sessions table (sessionMcpClient.ts, useRealSessionData.ts)
- [x] Add Forgot Password UI flow on login page (ForgotPasswordPage.tsx, routes in App.tsx)
- [x] Implement DataRetentionSettings cleanup with CSRF protection (csrf_service.py, retention tools, useRetentionSettings.ts)

### UI/Architecture
- [x] Consolidate UI framework (MUI vs Tailwind mixed in DeploymentModal) - Created Modal.tsx and Input.tsx, converted DeploymentModal, DeploymentConfigForm, LockedAccountsModal to Tailwind (24 files still use MUI elsewhere)
- [x] Rework settings/general UI for better user experience (Created Select.tsx, converted to Tailwind, added descriptions)
- [x] Add accessibility features (aria-labels, keyboard navigation, ARIA roles) - Added focus trap to Modal, aria-labels to Button/Input/Toggle, Toast announcements with role/aria-live, skip navigation link in AppLayout
- [x] Add tests for 54+ untested UI components

### Security
- [x] Make settings/security NIST compliant (password blocklist service, length-based policy, HIBP integration)
- [x] Implement agent token rotation mechanism (AgentService rotation methods, scheduler, WebSocket RPC, CLI/MCP tools)

### Code Quality (Technical Debt)
- [x] Split agent/src/lib/validation.py (429 lines) into focused modules:
  - `validation/constants.py` (70 lines) - Security constants
  - `validation/volume_validation.py` (70 lines) - Volume mount validation
  - `validation/docker_validation.py` (129 lines) - Docker run/params validation
  - `validation/command_validation.py` (199 lines) - Command allowlist & validator
  - `validation/__init__.py` (48 lines) - Package exports
- [x] Split database_service.py (2338 lines) into focused services:
  - `database/user_service.py` - User CRUD, password management, preferences
  - `database/server_service.py` - Server CRUD, credentials, metrics
  - `database/session_service.py` - Sessions, account locks, login attempts
  - `database/app_service.py` - Installations, preparations, app management
  - `database/system_service.py` - System info, migrations, component versions
  - `database/export_service.py` - Export/import operations
  - `database/metrics_service.py` - Metrics and activity logs
  - `database/schema_init.py` - Table initialization and migrations
  - `database/base.py` - Connection manager and security constants
  - `database_service.py` - Facade for backward compatibility

### Installation & Deployment
- [x] Create .devcontainer for Docker-based development/installation (.devcontainer/)
- [x] Create Docker Compose for production deployment (docker-compose.yml, docker/)
- [x] Create installation script (bash) for bare-metal Linux servers (install.sh)
- [ ] Create Ansible playbook for automated deployment
- [ ] Create RPM package for RHEL/CentOS/Fedora/Rocky Linux
- [x] Create DEB package for Debian/Ubuntu (packaging/debian/, packaging/build-deb.sh)

### CI/CD
- [x] Set up GitHub Actions for CI (build, lint, test) (.github/workflows/test.yml)
- [x] Set up GitHub Actions for automated releases (.github/workflows/release.yml)

---

## Difficulty Summary

| Difficulty | Count | Est. Time Each |
|------------|-------|----------------|
| Easy | 20 | < 1 hour |
| Medium | 38 | 1-4 hours |
| Hard | 20 | 4+ hours |

---

## Suggested Order of Execution

### Phase 1: Quick Wins (Easy)
Start with easy items to build momentum and clean up the codebase.

### Phase 2: Core Functionality (Medium - Features/Tests)
Focus on i18n, E2E tests, and user guides to improve quality.

### Phase 3: Infrastructure (Hard - Deployment)
Build out installation options and CI/CD pipeline.

### Phase 4: Polish (Hard - UI/Security)
Final polish with accessibility, NIST compliance, and UI consolidation.
