# Backup & Restore Guide

This guide covers how to backup and restore your Tomo configuration and data.

## Overview

Regular backups protect your tomo configuration from:

- Hardware failures
- Accidental deletions
- Corrupted data
- System migrations

## What's Included in Backups

### Full Backup Contents

| Category | Data Included |
|----------|---------------|
| **Servers** | All server configurations, credentials (encrypted) |
| **Applications** | Deployment configurations |
| **Settings** | All system settings |
| **Users** | User accounts (passwords hashed) |
| **Preferences** | UI preferences, themes |
| **Repositories** | Marketplace repository configs |

### What's NOT Included

| Category | Reason |
|----------|--------|
| Application data | Stored on servers, backup separately |
| Container images | Re-downloaded on restore |
| Logs | Can grow very large, optional |
| Session data | Temporary, not needed |

## Creating Backups

### From the Web Interface

1. Navigate to **Settings** > **System**
2. Find the "Backup & Restore" section
3. Click **Create Backup**
4. Wait for backup generation
5. Download the backup file

### Backup File Format

Backups are saved as JSON files:

```
tomo-backup-2024-01-15T10-30-00.json
```

The filename includes the timestamp for easy identification.

### Backup File Contents

```json
{
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "application_version": "2.1.0",
  "data": {
    "servers": [...],
    "settings": {...},
    "users": [...],
    "repositories": [...]
  }
}
```

## Automated Backups

### Setting Up Automated Backups

1. Go to **Settings** > **System**
2. Find "Automated Backups" section
3. Enable automated backups
4. Configure schedule:

| Option | Description |
|--------|-------------|
| Daily | Backup every day at specified time |
| Weekly | Backup once per week |
| Monthly | Backup on the 1st of each month |

### Backup Retention

Configure how many backups to keep:

- **Keep last N backups**: Automatically delete older backups
- **Keep backups for N days**: Time-based retention
- **Keep all**: No automatic deletion (watch disk space)

### Backup Location

Automated backups are stored in:
- Default: Application data directory
- Custom: Configure in settings

## Restoring from Backup

### Full Restore

Restore all data from a backup:

1. Go to **Settings** > **System**
2. Click **Restore Backup**
3. Select your backup file
4. Choose **Full Restore**
5. Confirm the warning
6. Wait for restore to complete
7. Application will restart

> **Warning**: Full restore replaces ALL current data.

### Selective Restore

Restore only specific data:

1. Click **Restore Backup**
2. Select your backup file
3. Choose **Selective Restore**
4. Check items to restore:
   - [ ] Servers
   - [ ] Settings
   - [ ] Users
   - [ ] Repositories
5. Click **Restore Selected**

### Restore Options

| Option | Description |
|--------|-------------|
| Merge | Add backup data, keep existing |
| Replace | Remove existing, use backup data |
| Skip duplicates | Don't overwrite matching items |

## Best Practices

### Backup Schedule

| Scenario | Recommended Schedule |
|----------|---------------------|
| Active development | Daily |
| Production tomo | Weekly |
| Stable, rarely changed | Monthly |
| Before major changes | Manual backup |

### Backup Storage

1. **Local storage** - Quick access, but risky if disk fails
2. **External drive** - Good for home users
3. **Cloud storage** - Best protection, requires upload
4. **Multiple locations** - Recommended for important data

### Backup Verification

Periodically test your backups:

1. Create a test environment
2. Restore backup to test instance
3. Verify data is complete and correct
4. Document any issues

### Retention Policy

Balance storage vs. recovery needs:

| Retention | Use Case |
|-----------|----------|
| 7 days | Limited storage, frequent backups |
| 30 days | Standard tomo |
| 90 days | Compliance requirements |
| 1 year | Audit requirements |

## Migration

### Migrating to New Server

1. **On old server:**
   - Create full backup
   - Download backup file
   - Note application version

2. **On new server:**
   - Install Tomo (same or newer version)
   - Complete initial setup
   - Restore from backup

### Migrating Between Versions

Backups are forward-compatible:
- Old backups can be restored to newer versions
- Data is migrated automatically

> **Note**: Downgrading (new backup to old version) is not supported.

## Troubleshooting

### "Backup Failed"

1. Check disk space
2. Verify write permissions
3. Check for database errors
4. Review application logs

### "Restore Failed"

1. Verify backup file is not corrupted
2. Check backup version compatibility
3. Ensure sufficient disk space
4. Check for conflicting data

### "Backup File Corrupted"

If backup file is damaged:

1. Try an older backup
2. Check for partial backups
3. Recover what you can manually
4. Implement better backup practices

### "Missing Data After Restore"

1. Verify correct backup was used
2. Check restore options (full vs selective)
3. Look for merge conflicts
4. Check application logs

## Command Line Backup

### Using the CLI

For advanced users, backups can be managed via CLI:

```bash
# Create backup
tomo backup create --output /path/to/backup.json

# Restore backup
tomo backup restore --input /path/to/backup.json

# List available backups
tomo backup list
```

### Scripting Backups

Example backup script:

```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR="/backups/tomo"
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="${BACKUP_DIR}/tomo-backup-${DATE}.json"

# Create backup
tomo backup create --output "${BACKUP_FILE}"

# Keep only last 7 days
find "${BACKUP_DIR}" -name "*.json" -mtime +7 -delete

# Optional: Copy to remote storage
# rsync -av "${BACKUP_FILE}" remote:/backups/
```

## Database Backup

### Direct Database Backup

For complete data protection, also backup the database:

```bash
# SQLite database backup
cp /path/to/tomo.db /backup/tomo-db-$(date +%Y%m%d).db

# Or use sqlite3 backup command
sqlite3 /path/to/tomo.db ".backup '/backup/tomo.db'"
```

### Database Location

Default database path:
- Linux: `~/.tomo/tomo.db` or `/var/lib/tomo/tomo.db`
- Custom: Check configuration

## Disaster Recovery

### Recovery Procedure

1. **Assess damage** - What data is lost?
2. **Identify latest backup** - Find most recent valid backup
3. **Prepare environment** - Fresh install if needed
4. **Restore backup** - Use restore procedure
5. **Verify restoration** - Check all data is present
6. **Update passwords** - Change credentials if breach suspected
7. **Document incident** - Record what happened for future reference

### Recovery Time Objectives

Plan your backup strategy based on acceptable downtime:

| RTO | Backup Strategy |
|-----|-----------------|
| < 1 hour | Frequent backups, automated restore |
| < 4 hours | Daily backups, documented restore |
| < 24 hours | Weekly backups, manual restore |

### Recovery Point Objectives

Plan based on acceptable data loss:

| RPO | Backup Frequency |
|-----|------------------|
| < 1 hour | Continuous or hourly |
| < 24 hours | Daily |
| < 1 week | Weekly |

---

## Quick Reference

### Creating a Backup

1. Settings > System > Create Backup
2. Download the file
3. Store safely

### Restoring a Backup

1. Settings > System > Restore Backup
2. Select file
3. Choose restore type
4. Confirm and wait

### Backup Checklist

- [ ] Regular backup schedule configured
- [ ] Backups stored in multiple locations
- [ ] Backups tested periodically
- [ ] Retention policy in place
- [ ] Recovery procedure documented

---

**Related Guides:**
- [Quick Start Guide](./QUICK_START.md)
- [Settings & Configuration Guide](./SETTINGS_CONFIGURATION.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
