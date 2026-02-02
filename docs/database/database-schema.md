# Database Schema

## Overview

This document provides an overview of the tomo database schema. Detailed diagrams and table definitions are organized by domain in separate files.

## Entity Relationship Diagrams

| Domain | File | Tables |
|--------|------|--------|
| [User Management & Settings](diagrams/users-settings.md) | `users-settings.md` | `users`, `system_settings`, `user_settings` |
| [Server Management](diagrams/servers.md) | `servers.md` | `servers`, `server_credentials`, `server_preparations`, `preparation_logs` |
| [Applications & Deployment](diagrams/applications.md) | `applications.md` | `app_categories`, `applications`, `installed_apps` |
| [Marketplace](diagrams/marketplace.md) | `marketplace.md` | `marketplace_repos`, `marketplace_apps`, `app_ratings` |
| [Metrics & Monitoring](diagrams/metrics.md) | `metrics.md` | `server_metrics`, `container_metrics` |
| [Audit Log](diagrams/audit.md) | `audit.md` | `audit_log` |
| [System Logs](diagrams/logs.md) | `logs.md` | `log_entries` |

---

## Relationships Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RELATIONSHIP GRAPH                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  users                                                                      │
│     ├──1:N──► user_settings                                                │
│     ├──1:N──► app_ratings                                                  │
│     └──1:N──► audit_log                                                    │
│                                                                             │
│  servers                                                                    │
│     ├──1:1──► server_credentials                                           │
│     ├──1:N──► installed_apps ◄──N:1── applications ◄──N:1── app_categories │
│     ├──1:N──► server_metrics                                               │
│     ├──1:N──► container_metrics                                            │
│     └──1:N──► server_preparations ──1:N──► preparation_logs                │
│                                                                             │
│  marketplace_repos ──1:N──► marketplace_apps ──1:N──► app_ratings          │
│                                                                             │
│  audit_log (tracks all: users, servers, apps, settings, marketplace, etc.) │
│                                                                             │
│  Standalone: log_entries, system_settings                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Summary

| Domain | Tables | Count |
|--------|--------|-------|
| User Management | `users` | 1 |
| Server Management | `servers`, `server_credentials` | 2 |
| Applications | `app_categories`, `applications`, `installed_apps` | 3 |
| Marketplace | `marketplace_repos`, `marketplace_apps`, `app_ratings` | 3 |
| Settings | `system_settings`, `user_settings` | 2 |
| Audit | `audit_log` | 1 |
| Metrics | `server_metrics`, `container_metrics` | 2 |
| Logs | `log_entries` | 1 |
| Server Preparation | `server_preparations`, `preparation_logs` | 2 |
| **Total** | | **17** |

---

## Quick Reference

### All Tables

| Table | Domain | Primary Key | Description |
|-------|--------|-------------|-------------|
| `users` | User Management | `id` (TEXT) | User accounts |
| `system_settings` | Settings | `id` (INTEGER) | System-wide settings |
| `user_settings` | Settings | `id` (INTEGER) | User-specific overrides |
| `servers` | Server Management | `id` (TEXT) | Server connections |
| `server_credentials` | Server Management | `server_id` (TEXT) | Encrypted credentials |
| `server_preparations` | Server Preparation | `id` (TEXT) | Setup process tracking |
| `preparation_logs` | Server Preparation | `id` (TEXT) | Setup step logs |
| `app_categories` | Applications | `id` (TEXT) | Category definitions |
| `applications` | Applications | `id` (TEXT) | Local app catalog |
| `installed_apps` | Applications | `id` (TEXT) | Deployed instances |
| `marketplace_repos` | Marketplace | `id` (TEXT) | External repositories |
| `marketplace_apps` | Marketplace | `id` (TEXT) | Marketplace apps |
| `app_ratings` | Marketplace | `id` (TEXT) | User ratings |
| `server_metrics` | Metrics | `id` (TEXT) | Server resource usage |
| `container_metrics` | Metrics | `id` (TEXT) | Container resource usage |
| `audit_log` | Audit | `id` (TEXT) | Unified audit trail |
| `log_entries` | Logs | `id` (TEXT) | System event logs |

---

## Design Notes

- **Primary Keys**: Most tables use TEXT UUIDs; settings tables use INTEGER AUTOINCREMENT
- **Foreign Keys**: Enforced with ON DELETE CASCADE where appropriate
- **JSON Fields**: Used for flexible data (tags, config, requirements, metadata)
- **Timestamps**: ISO 8601 strings (TEXT) or DATETIME
- **Encryption**: Server credentials encrypted at rest (AES-256)
- **Unified Audit**: Single `audit_log` table tracks all system changes with integrity checksums
- **Sensitive Data**: Passwords/keys are redacted in audit `old_value`/`new_value` fields
- **Retention**: Configured via `system_settings` (e.g., `retention.audit_log_days`, `retention.logs_days`)

---

## Related Documents

- [Audit Schema Proposal](audit-schema-proposal.md) - Design rationale for unified audit approach
