# NIST SP 800-63B-4 Compliance Tasks

This directory contains implementation tasks for making the Tomo security settings compliant with NIST SP 800-63B-4.

## Tasks by Priority

| Priority | Task | Description | Difficulty | Est. Time |
|----------|------|-------------|------------|-----------|
| **P1** | [05-database-settings](./05-database-settings.md) | Add NIST settings to database | Easy | 30 min |
| **P1** | [02-blocklist-data](./02-blocklist-data.md) | Create blocklist data files | Easy | 30 min |
| **P2** | [01-blocklist-service](./01-blocklist-service.md) | Create password blocklist service | Medium | 2 hrs |
| **P2** | [09-i18n-labels](./09-i18n-labels.md) | Add internationalization labels | Easy | 30 min |
| **P3** | [03-backend-validation](./03-backend-validation.md) | Update password validation logic | Medium | 2 hrs |
| **P3** | [07-password-strength-indicator](./07-password-strength-indicator.md) | Update password strength display | Medium | 1.5 hrs |
| **P4** | [04-registration-model](./04-registration-model.md) | Update registration validation | Easy | 30 min |
| **P4** | [08-frontend-validation](./08-frontend-validation.md) | Update frontend validation | Medium | 1.5 hrs |
| **P5** | [06-frontend-settings-ui](./06-frontend-settings-ui.md) | Update Security Settings UI | Medium | 2 hrs |
| **P6** | [10-unit-tests](./10-unit-tests.md) | Write unit tests | Medium | 2 hrs |
| **P7** | [11-e2e-tests](./11-e2e-tests.md) | Write E2E tests | Medium | 2 hrs |

## Priority Explanation

| Priority | Rationale |
|----------|-----------|
| **P1** | Foundation - Settings define feature flags, blocklist data needed for service |
| **P2** | Core backend - Blocklist service is critical; i18n can run in parallel |
| **P3** | Validation logic - Backend validation uses blocklist; strength indicator is standalone |
| **P4** | Model updates - Depends on backend validation being ready |
| **P5** | UI integration - Needs all backend and frontend pieces ready |
| **P6** | Unit testing - After implementation, verify components work |
| **P7** | E2E testing - Final verification of complete workflow |

## Execution Order (Dependency Graph)

```
P1: Foundation (can run in parallel)
  ┌─────────────────────┐    ┌─────────────────────┐
  │ 05-database-settings│    │ 02-blocklist-data   │
  └─────────┬───────────┘    └─────────┬───────────┘
            │                          │
            ▼                          ▼
P2: Core Services (can run in parallel)
  ┌─────────────────────┐    ┌─────────────────────┐
  │ 09-i18n-labels      │    │ 01-blocklist-service│
  └─────────┬───────────┘    └─────────┬───────────┘
            │                          │
            │                          ▼
            │              P3: Validation Logic
            │              ┌─────────────────────┐
            │              │ 03-backend-validation│
            │              └─────────┬───────────┘
            │                        │
            │                        ▼
            │              P4: Model Updates
            │              ┌─────────────────────┐
            │              │ 04-registration-model│
            │              └─────────┬───────────┘
            │                        │
            ▼                        │
P3: Frontend Components              │
  ┌─────────────────────┐            │
  │ 07-password-strength│            │
  └─────────┬───────────┘            │
            │                        │
            ▼                        │
P4: Frontend Validation              │
  ┌─────────────────────┐            │
  │ 08-frontend-valid   │            │
  └─────────┬───────────┘            │
            │                        │
            └────────────┬───────────┘
                         │
                         ▼
              P5: UI Integration
              ┌─────────────────────┐
              │ 06-frontend-settings│
              └─────────┬───────────┘
                        │
                        ▼
              P6: Unit Testing
              ┌─────────────────────┐
              │ 10-unit-tests       │
              └─────────┬───────────┘
                        │
                        ▼
              P7: E2E Testing
              ┌─────────────────────┐
              │ 11-e2e-tests        │
              └─────────────────────┘
```

## Quick Start

**Phase 1** - Start these in parallel:
- Task 05: Add database settings
- Task 02: Create blocklist data files

**Phase 2** - After Phase 1:
- Task 01: Create blocklist service
- Task 09: Add i18n labels (parallel with 01)

**Phase 3** - After blocklist service ready:
- Task 03: Update backend validation
- Task 07: Update password strength indicator (parallel with 03)

**Phase 4** - After validation logic:
- Task 04: Update registration model
- Task 08: Update frontend validation

**Phase 5** - After all components ready:
- Task 06: Update Security Settings UI

**Phase 6-7** - After implementation:
- Task 10: Unit tests
- Task 11: E2E tests

## Related Documentation

- [NIST_PASSWORD_COMPLIANCE.md](../NIST_PASSWORD_COMPLIANCE.md) - Full implementation plan
- [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html) - Official guidelines
