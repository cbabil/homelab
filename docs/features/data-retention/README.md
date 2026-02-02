# Data Retention

This section documents the data retention feature, including configuration, monitoring, and compliance.

## Documents

| Document | Description |
|---------|-------------|
| [User Guide](../data-retention-user-guide.md) | How to configure data retention |
| [Architecture](../../technical/data-retention-architecture.md) | Technical implementation |
| [Monitoring](../../operations/data-retention-monitoring.md) | Monitoring retention policies |
| [Compliance](../../compliance/data-retention-security-compliance.md) | Security and compliance |
| [Admin Procedures](../../admin/data-retention-security-procedures.md) | Administrative procedures |

## Overview

Data retention policies help you:
- **Manage storage** - Automatically cleanup old data
- **Comply with regulations** - Meet data retention requirements
- **Maintain performance** - Keep database size manageable

## Quick Start

### Configure Retention Period

1. Navigate to **Settings**
2. Go to **Data Retention** section
3. Set log retention period (days)
4. Enable automatic cleanup
5. Save settings

### View Cleanup Status

1. Go to **Settings > Data Retention**
2. View last cleanup timestamp
3. Check pending deletions

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Log Retention Days | 90 | How long to keep activity logs |
| Cleanup Enabled | false | Enable automatic cleanup |
| Cleanup Schedule | daily | When to run cleanup |

## Related Documentation

- [Settings Architecture](../../architecture/settings.md) - Settings system design
- [Operations](../../operations/README.md) - Operations overview
