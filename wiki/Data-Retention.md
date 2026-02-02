# Data Retention

This guide covers configuring data retention policies to manage storage and comply with data governance requirements.

---

## Overview

Data retention policies control how long different types of data are kept:

| Data Type | Purpose | Default Retention |
|-----------|---------|-------------------|
| **Activity Logs** | User actions and events | 90 days |
| **Audit Logs** | Security and compliance | 365 days |
| **Metrics Data** | Server performance history | 30 days |
| **Session Data** | Expired sessions | 7 days |

---

## Configuring Retention

### Via Web UI

1. Go to **Settings** > **Data Retention**
2. Configure each data type:
   - Retention period (days)
   - Cleanup schedule
3. Click **Save**

### Via Environment Variables

```bash
# Retention periods (days)
RETENTION_ACTIVITY_LOGS=90
RETENTION_AUDIT_LOGS=365
RETENTION_METRICS=30
RETENTION_SESSIONS=7
```

---

## Retention Policies

### Activity Logs

Records of user actions and system events:
- Login/logout events
- Server connections
- Application deployments
- Configuration changes

**Recommended retention:** 30-90 days

### Audit Logs

Security and compliance records:
- Authentication attempts
- Permission changes
- Security events
- Administrative actions

**Recommended retention:** 365 days (or as required by compliance)

### Metrics Data

Server performance measurements:
- CPU, memory, disk usage
- Network statistics
- Container metrics

**Recommended retention:** 7-30 days

### Session Data

Expired session records:
- User sessions
- Authentication tokens
- Temporary data

**Recommended retention:** 7 days

---

## Cleanup Process

### Automatic Cleanup

Data cleanup runs automatically:

| Schedule | Time |
|----------|------|
| **Daily** | 3:00 AM (configurable) |

### Manual Cleanup

Trigger immediate cleanup:

1. Go to **Settings** > **Data Retention**
2. Click **Run Cleanup Now**

Or via CLI:

```bash
tomo retention cleanup
```

### Dry Run

See what would be deleted without actually deleting:

```bash
tomo retention cleanup --dry-run
```

---

## Retention by Data Category

### Log Retention

| Log Type | Minimum | Recommended | Maximum |
|----------|---------|-------------|---------|
| Activity | 7 days | 30 days | 180 days |
| Audit | 90 days | 365 days | 2555 days |
| Error | 30 days | 90 days | 365 days |

### Metrics Retention

| Metric Type | Minimum | Recommended | Maximum |
|-------------|---------|-------------|---------|
| Real-time | 1 day | 7 days | 30 days |
| Hourly aggregate | 7 days | 30 days | 90 days |
| Daily aggregate | 30 days | 90 days | 365 days |

---

## Compliance Considerations

### GDPR

For GDPR compliance:
- Set reasonable retention periods
- Enable automatic cleanup
- Provide data export capability
- Document retention policies

### Industry Standards

| Standard | Typical Requirement |
|----------|---------------------|
| **SOC 2** | 1 year minimum for audit logs |
| **HIPAA** | 6 years for health data |
| **PCI-DSS** | 1 year for audit trails |

Consult your compliance requirements before configuring retention.

---

## Storage Management

### Check Storage Usage

1. Go to **Settings** > **Data Retention**
2. View **Storage Usage** section:
   - Database size
   - Logs size
   - Metrics size

Or via CLI:

```bash
tomo retention status
```

### Optimize Storage

If storage is high:

1. Reduce retention periods
2. Run manual cleanup
3. Export old data before deletion
4. Consider archiving to external storage

### Database Optimization

After cleanup, optimize the database:

```bash
tomo db optimize
```

This reclaims space from deleted records.

---

## Export Before Deletion

### Export Logs

Before data expires, export for long-term storage:

```bash
# Export logs older than 90 days
tomo logs export --older-than 90 --output logs-archive.json
```

### Export Metrics

```bash
# Export metrics
tomo metrics export --from 2024-01-01 --to 2024-03-31 --output metrics-q1.json
```

### Archive to External Storage

Configure automatic archiving:

1. Go to **Settings** > **Data Retention** > **Archiving**
2. Enable archiving
3. Configure destination (S3, SFTP, etc.)
4. Set archive schedule

---

## Retention Exceptions

### Exclude Specific Data

Keep certain records regardless of retention:

1. Go to **Settings** > **Data Retention** > **Exceptions**
2. Add exception rules:
   - Specific users
   - Specific events
   - Date ranges

### Indefinite Retention

For data that should never be deleted:

```bash
# Mark events for indefinite retention
tomo retention keep --event-id <id>
```

---

## Monitoring Retention

### Retention Dashboard

View retention status:
- Data volume by type
- Upcoming deletions
- Last cleanup run
- Next scheduled cleanup

### Notifications

Configure alerts:
- Storage threshold warnings
- Cleanup completion
- Cleanup failures

---

## CLI Reference

```bash
# View retention status
tomo retention status

# Run cleanup
tomo retention cleanup [--dry-run]

# Configure retention
tomo retention set --type activity --days 90

# View current settings
tomo retention show

# Export before deletion
tomo retention export --type audit --before 2024-01-01

# Mark for indefinite retention
tomo retention keep --event-id <id>
```

---

## Troubleshooting

### Cleanup Not Running

| Issue | Solution |
|-------|----------|
| Scheduler disabled | Enable in settings |
| Permission error | Check file permissions |
| Database locked | Wait for other operations |

### Data Still Growing

| Issue | Solution |
|-------|----------|
| High activity | Reduce retention period |
| Cleanup failing | Check logs for errors |
| Metrics sampling | Reduce metrics frequency |

### Recovery After Accidental Deletion

If retention is set too short:
- Restore from backup
- Check archive storage
- Data cannot be recovered if not backed up

---

## Best Practices

1. **Start conservative** - Set longer retention, reduce later
2. **Document policies** - Record why each setting was chosen
3. **Test cleanup** - Use dry-run before enabling
4. **Monitor storage** - Set up alerts for thresholds
5. **Archive important data** - Export before deletion
6. **Review regularly** - Adjust based on needs

---

## Next Steps

- [[Backup-and-Restore]] - Protect your data
- [[Security-Settings]] - Configure security
- [[Session-Management]] - Manage sessions
