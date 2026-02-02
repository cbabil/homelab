# CLI Backup Commands

This page covers CLI commands for backup and restore operations.

---

## Backup Export

Create an encrypted backup of your Tomo data.

### Basic Usage

```bash
tomo backup export
```

**Interactive prompts:**
- Backup password
- Confirm password

### With Options

```bash
tomo backup export \
  --output /backups/tomo-$(date +%Y%m%d).backup \
  --password-file /secure/backup-password.txt
```

### Options

| Option | Description |
|--------|-------------|
| `--output`, `-o` | Output file path |
| `--password`, `-p` | Backup password |
| `--password-file` | Read password from file |
| `--exclude` | Exclude data types |
| `--include` | Include only specific types |

### Data Types

| Type | Description |
|------|-------------|
| `servers` | Server configurations |
| `apps` | Application deployments |
| `users` | User accounts |
| `settings` | System settings |
| `logs` | Activity and audit logs |
| `all` | Everything (default) |

### Examples

**Backup servers only:**
```bash
tomo backup export --include servers --output servers.backup
```

**Backup everything except logs:**
```bash
tomo backup export --exclude logs --output data.backup
```

---

## Backup Import

Restore data from a backup file.

### Basic Usage

```bash
tomo backup import backup-file.backup
```

**Interactive prompts:**
- Backup password
- Restore mode

### With Options

```bash
tomo backup import \
  --file /backups/tomo-20240115.backup \
  --password-file /secure/backup-password.txt \
  --mode full
```

### Options

| Option | Description |
|--------|-------------|
| `--file`, `-f` | Backup file path |
| `--password`, `-p` | Backup password |
| `--password-file` | Read password from file |
| `--mode` | Restore mode (full/merge) |
| `--include` | Restore only specific types |
| `--dry-run` | Preview without restoring |

### Restore Modes

| Mode | Description |
|------|-------------|
| `full` | Replace all existing data |
| `merge` | Add new data, skip duplicates |

### Examples

**Merge servers from backup:**
```bash
tomo backup import backup.backup --mode merge --include servers
```

**Dry run to preview:**
```bash
tomo backup import backup.backup --dry-run
```

---

## Backup List

List available backup files.

```bash
tomo backup list
```

**Options:**

| Option | Description |
|--------|-------------|
| `--path` | Directory to scan |
| `--json` | JSON output |

**Output:**
```
FILE                              DATE        SIZE    VERSION
tomo-20240115.backup           2024-01-15  2.4 MB  1.0.0
tomo-20240108.backup           2024-01-08  2.3 MB  1.0.0
tomo-20240101.backup           2024-01-01  2.1 MB  0.9.0
```

---

## Backup Verify

Verify backup file integrity.

```bash
tomo backup verify backup-file.backup
```

**Interactive prompts:**
- Backup password

**Options:**

| Option | Description |
|--------|-------------|
| `--password`, `-p` | Backup password |
| `--password-file` | Read password from file |

**Output:**
```
Backup verification:
  File:           tomo-20240115.backup
  Created:        2024-01-15 10:30:00 UTC
  Version:        1.0.0
  Encryption:     AES-256-GCM
  Integrity:      ✓ Valid
  Contents:
    - Servers:    5 entries
    - Apps:       12 entries
    - Users:      3 entries
    - Settings:   ✓ Present
```

---

## Backup Info

Show backup metadata without decrypting content.

```bash
tomo backup info backup-file.backup
```

**Output:**
```
File:     tomo-20240115.backup
Size:     2.4 MB
Created:  2024-01-15 10:30:00 UTC
Version:  1.0.0
```

---

## Scheduled Backups

Configure automatic backup schedule.

### Create Schedule

```bash
tomo backup schedule \
  --cron "0 2 * * *" \
  --output /backups/ \
  --keep 7 \
  --password-file /secure/backup-password.txt
```

**Options:**

| Option | Description |
|--------|-------------|
| `--cron` | Cron expression |
| `--output` | Output directory |
| `--keep` | Number of backups to retain |
| `--password` | Backup password |
| `--password-file` | Password file |

### Cron Examples

| Schedule | Cron Expression |
|----------|-----------------|
| Daily at 2 AM | `0 2 * * *` |
| Weekly Sunday 3 AM | `0 3 * * 0` |
| Monthly 1st at 4 AM | `0 4 1 * *` |

### List Schedules

```bash
tomo backup schedule --list
```

### Remove Schedule

```bash
tomo backup schedule --remove
```

---

## Scripting Examples

### Daily Backup Script

```bash
#!/bin/bash
# daily-backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/tomo"
PASSWORD_FILE="/secure/backup-password.txt"
KEEP_DAYS=7

# Create backup
tomo backup export \
  --output "$BACKUP_DIR/tomo-$DATE.backup" \
  --password-file "$PASSWORD_FILE"

# Verify backup
tomo backup verify \
  "$BACKUP_DIR/tomo-$DATE.backup" \
  --password-file "$PASSWORD_FILE"

# Remove old backups
find "$BACKUP_DIR" -name "tomo-*.backup" -mtime +$KEEP_DAYS -delete
```

### Remote Backup

```bash
#!/bin/bash
# remote-backup.sh

LOCAL_BACKUP="/tmp/tomo-$(date +%Y%m%d).backup"
REMOTE_HOST="backup-server"
REMOTE_PATH="/backups/tomo/"

# Create backup
tomo backup export --output "$LOCAL_BACKUP" --password-file /secure/pass.txt

# Upload to remote
scp "$LOCAL_BACKUP" "$REMOTE_HOST:$REMOTE_PATH"

# Cleanup local
rm "$LOCAL_BACKUP"
```

### S3 Backup

```bash
#!/bin/bash
# s3-backup.sh

DATE=$(date +%Y%m%d)
BACKUP_FILE="/tmp/tomo-$DATE.backup"
S3_BUCKET="s3://my-bucket/tomo-backups/"

# Create backup
tomo backup export --output "$BACKUP_FILE" --password-file /secure/pass.txt

# Upload to S3
aws s3 cp "$BACKUP_FILE" "$S3_BUCKET"

# Cleanup
rm "$BACKUP_FILE"
```

### Backup Rotation

```bash
#!/bin/bash
# Implement grandfather-father-son rotation

BACKUP_DIR="/backups/tomo"

# Daily (keep 7)
find "$BACKUP_DIR/daily" -mtime +7 -delete

# Weekly (keep 4)
find "$BACKUP_DIR/weekly" -mtime +28 -delete

# Monthly (keep 12)
find "$BACKUP_DIR/monthly" -mtime +365 -delete

# Create today's backup
tomo backup export --output "$BACKUP_DIR/daily/$(date +%Y%m%d).backup"

# Copy to weekly on Sundays
if [ "$(date +%u)" -eq 7 ]; then
  cp "$BACKUP_DIR/daily/$(date +%Y%m%d).backup" "$BACKUP_DIR/weekly/"
fi

# Copy to monthly on 1st
if [ "$(date +%d)" -eq 01 ]; then
  cp "$BACKUP_DIR/daily/$(date +%Y%m%d).backup" "$BACKUP_DIR/monthly/"
fi
```

---

## Troubleshooting

### Backup Fails

| Issue | Solution |
|-------|----------|
| Permission denied | Check write permissions |
| Disk full | Free up space |
| Database locked | Wait for other operations |

### Restore Fails

| Issue | Solution |
|-------|----------|
| Wrong password | Verify password |
| Corrupted file | Use different backup |
| Version mismatch | Update Tomo first |

### Password Lost

Unfortunately, if you lose the backup password, the backup cannot be recovered. The encryption is designed to be secure.

---

## Best Practices

1. **Test restores regularly** - Verify backups work
2. **Store passwords securely** - Use a password manager
3. **Keep multiple copies** - Different locations
4. **Automate** - Don't rely on manual backups
5. **Monitor** - Alert on backup failures

---

## Next Steps

- [[CLI-Agent-Commands]] - Agent commands
- [[CLI-Admin-Commands]] - Admin commands
- [[Backup-and-Restore]] - Backup concepts
