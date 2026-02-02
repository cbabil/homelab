# Backup and Restore

This guide covers backing up and restoring your Tomo data.

---

## What Gets Backed Up

A full backup includes:

| Data | Description |
|------|-------------|
| **Database** | Servers, applications, settings |
| **Credentials** | Encrypted SSH keys and passwords |
| **Configuration** | All application settings |
| **Audit Logs** | Activity and security logs |

**Not included:**
- Application data on remote servers
- Docker volumes on remote servers
- Container images

---

## Backup Methods

### Web UI Backup

1. Go to **Settings** > **Backup**
2. Click **Export Backup**
3. Enter a backup password
4. Download the encrypted backup file

### CLI Backup

```bash
# Interactive backup
tomo backup export

# With options
tomo backup export --output ./backup.enc --password-file ./secret.txt
```

### Automated Backup

Set up scheduled backups:

1. Go to **Settings** > **Backup**
2. Enable **Scheduled Backups**
3. Configure:
   - Schedule (daily, weekly)
   - Retention (how many to keep)
   - Storage location

---

## Backup File Format

Backups are encrypted files with the extension `.tomo-backup`:

```
tomo-backup-2024-01-15.tomo-backup
```

**Security:**
- AES-256-GCM encryption
- PBKDF2 key derivation
- Password protected

---

## Restore from Backup

### Web UI Restore

1. Go to **Settings** > **Backup**
2. Click **Import Backup**
3. Select the backup file
4. Enter the backup password
5. Choose restore options:
   - **Full restore** - Replace all data
   - **Merge** - Add to existing data
6. Click **Restore**

### CLI Restore

```bash
# Interactive restore
tomo backup import

# With options
tomo backup import --file ./backup.enc --password-file ./secret.txt
```

### Restore Options

| Option | Description |
|--------|-------------|
| **Full Restore** | Replace all existing data |
| **Merge** | Add new data, skip duplicates |
| **Servers Only** | Restore only server configurations |
| **Settings Only** | Restore only application settings |

---

## Backup Best Practices

### Regular Backups

- **Daily:** For active installations
- **Weekly:** For stable installations
- **Before changes:** Before major updates or changes

### Secure Storage

Store backups:
- On a different physical device
- In cloud storage (encrypted)
- Off-site for disaster recovery

### Test Restores

Periodically test that backups can be restored:
1. Set up a test instance
2. Restore from backup
3. Verify data integrity

### Password Management

- Use a strong, unique password
- Store the password securely (password manager)
- Document recovery procedures

---

## Backup Storage Locations

### Local Storage

```bash
# Default location
/var/lib/tomo/backups/

# Custom location
BACKUP_PATH=/mnt/backups tomo backup export
```

### Remote Storage

Configure remote backup destinations:

1. Go to **Settings** > **Backup**
2. Click **Add Destination**
3. Choose type:
   - **S3/MinIO** - Object storage
   - **SFTP** - Remote server
   - **WebDAV** - Nextcloud, etc.

### Cloud Storage

For cloud storage, configure:

```bash
# S3-compatible storage
BACKUP_S3_ENDPOINT=s3.amazonaws.com
BACKUP_S3_BUCKET=tomo-backups
BACKUP_S3_ACCESS_KEY=your-access-key
BACKUP_S3_SECRET_KEY=your-secret-key
```

---

## Backup Verification

### Check Backup Integrity

```bash
tomo backup verify ./backup.enc
```

This verifies:
- File is not corrupted
- Encryption is valid
- Can be decrypted with password

### List Backup Contents

```bash
tomo backup list ./backup.enc
```

Shows what's in the backup without restoring.

---

## Disaster Recovery

### Full System Recovery

1. Install Tomo on new system
2. Create initial admin account
3. Go to **Settings** > **Backup**
4. Import backup file
5. Verify restored data
6. Update server connection settings if IPs changed

### Database Recovery

If only the database is corrupted:

```bash
# Stop the service
sudo systemctl stop tomo

# Replace database
cp /backup/tomo.db /var/lib/tomo/tomo.db

# Start the service
sudo systemctl start tomo
```

---

## Backup Encryption

### How It Works

1. Password → PBKDF2 (100,000 iterations) → Key
2. Random IV generated
3. Data encrypted with AES-256-GCM
4. Authentication tag appended

### Change Backup Password

When importing, you can set a new password:

```bash
tomo backup import --file backup.enc --new-password
```

---

## Troubleshooting

### Cannot Create Backup

| Issue | Solution |
|-------|----------|
| Permission denied | Check write permissions |
| Disk full | Free up space |
| Database locked | Wait for other operations |

### Cannot Restore Backup

| Issue | Solution |
|-------|----------|
| Wrong password | Verify password |
| Corrupted file | Use a different backup |
| Version mismatch | Update Tomo first |

### Backup Too Large

Reduce backup size:
1. Clean up old audit logs
2. Enable data retention policies
3. Exclude historical metrics

---

## CLI Reference

```bash
# Create backup
tomo backup export [--output <file>] [--password <pass>]

# Restore backup
tomo backup import <file> [--password <pass>] [--mode <full|merge>]

# Verify backup
tomo backup verify <file>

# List backup contents
tomo backup list <file>

# Schedule backup
tomo backup schedule --cron "0 2 * * *" --keep 7

# List scheduled backups
tomo backup schedule --list
```

---

## Backup File Retention

Configure retention to automatically delete old backups:

| Setting | Description |
|---------|-------------|
| **Keep Last N** | Keep the N most recent backups |
| **Keep Days** | Keep backups from last N days |
| **Keep Minimum** | Always keep at least N backups |

---

## Next Steps

- [[Security-Settings]] - Secure your installation
- [[Data-Retention]] - Configure data cleanup
- [[Troubleshooting]] - Solve problems
