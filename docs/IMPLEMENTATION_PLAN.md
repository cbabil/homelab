# Data Retention Feature Implementation Plan

## Overview
Add configurable data retention settings to the homelab management application, enabling automatic cleanup of logs and other data based on user-defined retention periods.

## Complexity Assessment
**Medium-High Complexity (4 stages)**
- Backend data deletion operations require security review
- Frontend-backend integration with new settings section
- Database operations for automated cleanup
- Testing of data deletion without data loss

## Stages

### Stage 1: Backend Data Retention Models & Types
**Goal**: Establish backend foundation for data retention settings and operations

**Deliverables**:
- Add retention settings types to backend models
- Create data retention service with cleanup operations for logs
- Implement secure deletion operations for log_entries table
- Add retention policy validation and safety checks

**Success Criteria**:
- Backend models support log retention days (7-365 days) and other data retention days (30-3650 days)
- Log cleanup service can delete entries older than specified days from log_entries table
- Deletion operations include transaction rollback on errors
- Logging of all deletion operations for audit purposes
- Unit tests for retention service operations

**Test Cases**:
- Test log deletion with various retention periods (7, 30, 90 days)
- Test that recent logs are preserved correctly
- Test transaction rollback on deletion errors
- Test deletion operation audit logging

### Stage 2: Backend API Integration & MCP Tools
**Goal**: Expose data retention management through FastMCP tools

**Deliverables**:
- Create retention management MCP tools for getting/setting retention policies
- Add data cleanup execution tool with admin-only access
- Integrate retention settings with existing database service patterns
- Implement preview mode for cleanup operations (dry-run)

**Success Criteria**:
- MCP tools allow reading current retention settings
- MCP tools allow updating retention policies with validation
- Admin-only cleanup execution tool works with dry-run capability
- Tools follow existing MCP patterns from auth_tools.py and app_tools.py
- Error handling and structured logging for all operations

**Test Cases**:
- Test retention settings retrieval via MCP
- Test retention policy updates with valid/invalid values
- Test dry-run cleanup shows affected record counts without deletion
- Test admin access control for cleanup operations

### Stage 3: Frontend Settings UI Components
**Goal**: Add data retention section to Settings/General page with interactive controls

**Deliverables**:
- Add DataRetentionSettings component to GeneralSettings.tsx
- Implement retention period sliders for logs (7-365 days) and other data (30-3650 days)
- Add retention settings types to frontend settings.ts
- Create settings service integration for retention policies
- Add form validation and user feedback

**Success Criteria**:
- Data retention section appears in Settings/General page
- Sliders have appropriate min/max values and step increments
- Settings integrate with existing settingsService patterns
- Real-time validation of retention periods
- Visual feedback for save success/error states
- Follows existing UI patterns from SecuritySettings.tsx

**Test Cases**:
- Test slider controls update retention values correctly
- Test form validation prevents invalid retention periods
- Test settings persistence through page refresh
- Test error handling for failed saves
- Test accessibility of slider controls

### Stage 4: Automated Cleanup & Integration Testing
**Goal**: Complete end-to-end data retention feature with automated cleanup and comprehensive testing

**Deliverables**:
- Add automated cleanup scheduling/triggers (if applicable)
- Complete integration between frontend settings and backend deletion
- Add comprehensive E2E tests for retention feature
- Implement cleanup status/history reporting
- Security review documentation for data deletion operations

**Success Criteria**:
- End-to-end workflow: set retention policy → data gets cleaned up according to schedule
- Frontend settings changes trigger appropriate backend updates
- Cleanup operations provide status feedback to users
- All deletion operations are logged and auditable
- E2E tests cover complete retention workflow
- Security review confirms safe data deletion practices

**Test Cases**:
- Test complete workflow: change settings → verify cleanup behavior
- Test that cleanup respects current retention settings
- Test cleanup status reporting in UI
- Test that cleanup operations don't affect active user sessions
- Test data recovery scenarios (confirm permanent deletion as expected)

## Dependencies & Integration Points

**Existing Patterns to Follow**:
- Settings structure: Follow `types/settings.ts` and `services/settingsService.ts` patterns
- UI components: Use `SettingRow` component from GeneralSettings.tsx
- Backend services: Follow database service patterns from `services/database_service.py`
- MCP tools: Follow patterns from `tools/auth_tools.py` and `tools/app_tools.py`

**Database Integration**:
- Extend log_entries table operations for date-based deletion
- Use existing async database connection patterns from `database/connection.py`
- Follow transaction management from `database_service.py`

**Security Considerations**:
- Data deletion operations require admin privileges
- All deletion operations must be logged for audit
- Implement transaction rollback for failed deletions
- Provide dry-run mode for preview before actual deletion
- Document data recovery implications (permanent deletion)

## Risk Mitigation
- **Data Loss Prevention**: Implement minimum retention periods and validation
- **Performance Impact**: Use indexed date queries and batch deletion operations
- **Transaction Safety**: Wrap all deletions in database transactions with rollback
- **Security**: Restrict cleanup operations to admin users only
- **Testing**: Comprehensive unit and integration tests before production deployment

## Notes
- Feature affects data persistence - thorough testing required
- Security review mandatory for data deletion operations
- Follow 100-line function limit across all implementations
- Document all deletion operations for compliance/audit purposes

---

# Applications Catalog Persistence

## Overview
Persist the application marketplace catalog inside `homelab.db`, replacing the static frontend dataset. The catalog includes application categories and a `connected_server_id` field to record which server hosts an installed application.

## Scope & Deliverables
- Add `app_categories` and `applications` tables with SQLAlchemy models bound to `homelab.db`.
- Seed the database with the existing frontend application list during initialization.
- Update the MCP application tools (`search_apps`, `get_app_details`) to read from the database-backed service.
- Extend the frontend data service layer to consume the MCP tools and remove all hardcoded application data.
- Surface category metadata dynamically in navigation, filters, and forms (navigation now shows “All Apps” plus category-specific shortcuts, without a separate installed link).
- Add a “Clear Cache” action to the user profile dropdown that clears local storage caches, auth/session data, and in-memory data service caches for a clean refresh.
- Standardise the backend data directory configuration: `.env` now sets `DATA_DIRECTORY=data`, and the database manager resolves it relative to the backend directory so the server and tooling share the same SQLite file.
- Introduced `backend/src/exceptions/app_exceptions.py` to centralise application-related exceptions (e.g., `ApplicationLogWriteError`).
- Added `backend/src/app_logging/app_logs.py` with helpers (e.g., `build_empty_search_log`) so services no longer inline log-entry construction; this keeps logging consistent and easier to maintain.

## Success Criteria
- Application data loads from the backend via MCP without referencing `mockApps`.
- Each application exposes an optional `connectedServerId` derived from the new database column.
- Navigation stats and filters reflect the persisted application catalog.
- Implementation documentation describes the new tables and initialization behaviour.

## Testing
- Manual verification that the Applications page renders the seeded catalog and filtering works as expected.
- Manual backup export to confirm application data flows through the new data service.
- Unit coverage for navigation continues to pass with mocked application data.

## Notes
- Application add/update/delete operations remain in-memory placeholders until backend mutations are implemented.
- Seeding executes only when the catalog tables are empty to preserve user modifications.
- Clearing caches is a client-side convenience; backend data remains untouched but the next MCP fetch repopulates the UI from persisted sources.
- Configuration changes require restarting the FastMCP backend so it re-reads `DATA_DIRECTORY` and reconnects to the correct database path (`data/homelab.db`).

---

# Security Logging Enhancement (Login & Logout)

## Overview
Capture frontend login and logout activity as "Security" category events so the Logs page can surface authentication history alongside existing system/application logs.

## Scope & Deliverables
- Extend the frontend `systemLogger` with a dedicated `securityLogger` helper.
- Emit structured security logs from `useAuthActions` during login attempts, successes, failures, and logout flows.
- Update the Logs UI to include a "Security" filter and shared filtering utility so authentication events are easy to isolate.
- Add unit coverage for the new filter helper and security logging behaviour.

## Success Criteria
- Login and logout actions generate Security-category log entries with contextual metadata (username, token/session info when applicable).
- Logs page displays a "Security" tab showing the new entries without impacting other filters.
- Tests validate filter behaviour and confirm loggers fire for success and failure paths.

## Testing
- Unit test `filterLogsByKey` to ensure security filtering returns only security-tagged entries.
- Unit test `useAuthActions` logging to ensure info/warn/error calls fire with expected payloads for login success/failure and logout.
- Manual QA: perform login/logout in the app and verify the Logs → Security tab shows the new events.

## Notes
- Instrumentation follows the 120-line per file/function limit by keeping new helpers concise.
- React changes adhere to hooks best practices (stable callbacks, memoised filtering, dependency lists).

---

# Backend Environment Configuration

## Overview
Ensure the FastMCP backend reads environment overrides from `.env` so deployments can adjust directories and secrets without modifying source files.

## Scope & Deliverables
- Update `ConfigService` to load `.env` values before resolving configuration defaults.
- Provide a `.env_example` template documenting supported keys (initially `DATA_DIRECTORY`).
- Introduce an `APP_ENV` flag letting deployments distinguish between development, staging, and production.
- Remove legacy `config.json` / `credentials.enc` usage; configuration now derives solely from environment variables.
- Document supported `.env` keys (`DATA_DIRECTORY`, `APP_ENV`) for contributors.

## Success Criteria
- Backend boots with values exported in `.env` when present, falling back gracefully when the file is absent.
- Contributors can copy `.env_example` to `.env` and immediately run the backend with the documented defaults.
- Configuration objects expose the active environment so other services can branch behaviour when needed.
- Configuration output only reflects documented `.env` keys so behaviour stays predictable.

## Testing
- Manual: rename `.env` and confirm defaults apply; restore `.env` and confirm values propagate (e.g., `DATA_DIRECTORY`).
- Unit/integration coverage not required at this stage; existing ConfigService usage covers the path.

## Notes
- Implementation respects the 120-line guidance by keeping the loader helper concise.
- Logging records whether the `.env` file was detected, aiding troubleshooting.
