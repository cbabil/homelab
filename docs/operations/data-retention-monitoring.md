# Data Retention Operations and Monitoring Guide

## Operations Overview

This document provides comprehensive guidance for monitoring, maintaining, and troubleshooting the data retention system in production environments.

## System Monitoring

### Key Performance Indicators (KPIs)

#### Storage Metrics
- **Total Storage Used**: Monitor overall database storage consumption
- **Storage Growth Rate**: Track daily/weekly storage increase trends
- **Space Freed by Cleanup**: Measure effectiveness of retention operations
- **Storage Utilization**: Percentage of available storage in use

**Monitoring Commands**:
```bash
# Check database size
psql -c "SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size;"

# Monitor table sizes
psql -c "SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check log entry counts by age
psql -c "SELECT
  date_trunc('day', created_at) as day,
  count(*) as entries
FROM log_entries
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY date_trunc('day', created_at)
ORDER BY day DESC;"
```

#### Performance Metrics
- **Cleanup Operation Duration**: Time taken for retention operations
- **Database Query Performance**: Response times for retention queries
- **Transaction Rollback Rate**: Frequency of failed operations
- **Concurrent Operation Impact**: Effect on system performance during cleanup

**Monitoring Queries**:
```sql
-- Average cleanup operation duration (from audit logs)
SELECT
  operation_type,
  retention_type,
  AVG(duration_seconds) as avg_duration,
  MAX(duration_seconds) as max_duration,
  COUNT(*) as operation_count
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '7 days'
  AND success = true
GROUP BY operation_type, retention_type;

-- Failed operation analysis
SELECT
  DATE(timestamp) as date,
  operation_type,
  COUNT(*) as failures,
  STRING_AGG(DISTINCT error_message, '; ') as common_errors
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
  AND success = false
GROUP BY DATE(timestamp), operation_type
ORDER BY date DESC;
```

#### Security Metrics
- **Admin Access Patterns**: Monitor frequency and timing of admin operations
- **Failed Authentication Attempts**: Track unauthorized access attempts
- **Unusual Operation Patterns**: Identify potentially suspicious activity
- **Compliance Audit Events**: Monitor regulatory compliance status

### Real-Time Monitoring Setup

#### Log File Monitoring
Monitor application logs for retention-related events:

```bash
# Monitor retention operations in real-time
tail -f /var/log/tomo/backend.log | grep -i "retention"

# Watch for security events
tail -f /var/log/tomo/backend.log | grep -E "(retention.*admin|retention.*failed|retention.*security)"

# Monitor cleanup progress
tail -f /var/log/tomo/backend.log | grep -E "(cleanup.*progress|cleanup.*complete)"
```

#### Database Monitoring
Set up automated monitoring for database events:

```sql
-- Create monitoring view for retention operations
CREATE OR REPLACE VIEW retention_monitoring AS
SELECT
  operation_id,
  timestamp,
  operation_type,
  retention_type,
  admin_user_id,
  success,
  records_affected,
  duration_seconds,
  CASE
    WHEN duration_seconds > 300 THEN 'SLOW'
    WHEN records_affected > 50000 THEN 'LARGE'
    WHEN success = false THEN 'FAILED'
    ELSE 'NORMAL'
  END as status_flag
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- Query for anomalies
SELECT * FROM retention_monitoring
WHERE status_flag IN ('SLOW', 'LARGE', 'FAILED')
ORDER BY timestamp DESC;
```

### Alerting Configuration

#### Critical Alerts (Immediate Response Required)
1. **Cleanup Operation Failures**: Any failed retention operation
2. **Unauthorized Access**: Non-admin users attempting retention operations
3. **Database Transaction Failures**: Rollbacks during cleanup operations
4. **Storage Critical**: Available storage below 10% threshold

**Alert Script Example**:
```bash
#!/bin/bash
# /opt/tomo/scripts/retention-alerts.sh

# Check for failed operations in last hour
FAILED_OPS=$(psql -t -c "SELECT COUNT(*) FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '1 hour' AND success = false;")

if [ "$FAILED_OPS" -gt 0 ]; then
    echo "CRITICAL: $FAILED_OPS retention operations failed in the last hour"
    # Send alert to monitoring system
    curl -X POST "https://monitoring.company.com/alerts" \
         -H "Content-Type: application/json" \
         -d "{\"level\": \"critical\", \"message\": \"Retention operation failures\", \"count\": $FAILED_OPS}"
fi

# Check storage usage
STORAGE_USAGE=$(df -h /var/lib/postgresql/data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$STORAGE_USAGE" -gt 90 ]; then
    echo "WARNING: Database storage usage at ${STORAGE_USAGE}%"
fi
```

#### Warning Alerts (Response Within 4 Hours)
1. **Long-Running Operations**: Cleanup operations exceeding normal duration
2. **High Storage Growth**: Unusual increase in data volume
3. **Frequent Admin Access**: Unusual patterns in admin retention access
4. **Performance Degradation**: Slow response times during operations

#### Information Alerts (Daily Review)
1. **Successful Operations**: Summary of completed retention operations
2. **Storage Trends**: Daily storage utilization reports
3. **Compliance Status**: Retention policy compliance summary
4. **System Health**: Overall retention system status

## Operational Procedures

### Daily Operations Checklist

#### Morning Review (Start of Business)
- [ ] **Check System Status**: Verify retention service is running
- [ ] **Review Overnight Operations**: Check logs for any overnight cleanup operations
- [ ] **Storage Utilization**: Monitor current storage usage and trends
- [ ] **Error Log Review**: Check for any errors or warnings
- [ ] **Performance Metrics**: Review system performance indicators

**Daily Status Script**:
```bash
#!/bin/bash
# /opt/tomo/scripts/daily-retention-status.sh

echo "=== Daily Retention Status Report - $(date) ==="

# Check service status
echo "Service Status:"
systemctl status tomo-backend | grep -E "(Active|Main PID)"

# Last 24 hours operations summary
echo -e "\nLast 24 Hours Operations:"
psql -c "SELECT
  operation_type,
  COUNT(*) as total_ops,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
  SUM(records_affected) as total_records_affected
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY operation_type;"

# Storage usage
echo -e "\nStorage Usage:"
df -h /var/lib/postgresql/data | grep -E "(Filesystem|/dev)"

# Recent errors
echo -e "\nRecent Errors:"
psql -c "SELECT timestamp, operation_type, error_message
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND success = false
ORDER BY timestamp DESC
LIMIT 5;"
```

#### Weekly Review (End of Week)
- [ ] **Retention Policy Review**: Verify current retention settings are appropriate
- [ ] **Performance Analysis**: Analyze cleanup operation performance trends
- [ ] **Storage Trend Analysis**: Review weekly storage growth patterns
- [ ] **Security Audit**: Review admin access patterns and security events
- [ ] **Compliance Check**: Verify retention policies meet regulatory requirements

### Maintenance Procedures

#### Database Maintenance
Regular database maintenance for optimal retention performance:

```sql
-- Vacuum and analyze retention-related tables
VACUUM ANALYZE log_entries;
VACUUM ANALYZE retention_settings;
VACUUM ANALYZE retention_audit_log;

-- Update table statistics
ANALYZE log_entries;
ANALYZE retention_audit_log;

-- Check index usage and optimization
SELECT
  schemaname,
  tablename,
  indexname,
  num_scans,
  tuples_read,
  tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename IN ('log_entries', 'retention_audit_log')
ORDER BY num_scans DESC;
```

#### Log Rotation and Archival
Manage application log files to prevent storage issues:

```bash
#!/bin/bash
# /opt/tomo/scripts/log-maintenance.sh

# Rotate application logs
logrotate /etc/logrotate.d/tomo

# Archive old retention audit logs to external storage
pg_dump --table=retention_audit_log \
        --data-only \
        --where="timestamp < NOW() - INTERVAL '1 year'" \
        tomo_db > /backup/retention_audit_$(date +%Y%m%d).sql

# Compress archived logs
gzip /backup/retention_audit_$(date +%Y%m%d).sql
```

#### Performance Optimization
Regular performance tuning for retention operations:

```sql
-- Identify slow queries
SELECT
  query,
  mean_time,
  calls,
  total_time
FROM pg_stat_statements
WHERE query LIKE '%retention%'
  OR query LIKE '%log_entries%'
ORDER BY mean_time DESC
LIMIT 10;

-- Check for missing indexes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE tablename = 'log_entries'
  AND attname IN ('created_at', 'level', 'source');
```

### Backup and Recovery

#### Backup Procedures
Ensure retention data and configuration are properly backed up:

```bash
#!/bin/bash
# /opt/tomo/scripts/retention-backup.sh

BACKUP_DIR="/backup/retention/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup retention settings
pg_dump --table=retention_settings tomo_db > "$BACKUP_DIR/retention_settings.sql"

# Backup audit logs (last 90 days)
pg_dump --table=retention_audit_log \
        --where="timestamp > NOW() - INTERVAL '90 days'" \
        tomo_db > "$BACKUP_DIR/retention_audit_recent.sql"

# Backup application configuration
cp /opt/tomo/config/retention.conf "$BACKUP_DIR/"

# Create backup manifest
echo "Retention backup created: $(date)" > "$BACKUP_DIR/manifest.txt"
echo "Settings: retention_settings.sql" >> "$BACKUP_DIR/manifest.txt"
echo "Audit logs: retention_audit_recent.sql" >> "$BACKUP_DIR/manifest.txt"
echo "Config: retention.conf" >> "$BACKUP_DIR/manifest.txt"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C /backup/retention "$(date +%Y%m%d)"
rm -rf "$BACKUP_DIR"
```

#### Recovery Procedures
Steps for recovering retention system after failures:

1. **Service Recovery**:
```bash
# Restart retention service
systemctl restart tomo-backend

# Verify service startup
systemctl status tomo-backend
tail -f /var/log/tomo/backend.log
```

2. **Data Recovery**:
```bash
# Restore retention settings
psql tomo_db < /backup/retention/20250114/retention_settings.sql

# Restore audit logs if needed
psql tomo_db < /backup/retention/20250114/retention_audit_recent.sql

# Verify data integrity
psql -c "SELECT COUNT(*) FROM retention_settings;"
psql -c "SELECT MAX(timestamp) FROM retention_audit_log;"
```

3. **Configuration Recovery**:
```bash
# Restore configuration
cp /backup/retention/20250114/retention.conf /opt/tomo/config/

# Restart service with restored config
systemctl restart tomo-backend
```

## Troubleshooting Guide

### Common Issues and Resolutions

#### Issue: Cleanup Operations Timing Out
**Symptoms**: Operations start but never complete, or take exceptionally long time

**Investigation Steps**:
1. Check database locks:
```sql
SELECT
  pl.pid,
  pl.mode,
  pl.locktype,
  pl.relation::regclass,
  pl.page,
  pl.tuple,
  pl.transactionid
FROM pg_locks pl
LEFT JOIN pg_stat_activity psa ON pl.pid = psa.pid
WHERE psa.query LIKE '%retention%' OR psa.query LIKE '%log_entries%';
```

2. Check system resources:
```bash
top -p $(pgrep -f "tomo-backend")
iostat -x 1 5
```

3. Review operation parameters:
```sql
SELECT * FROM retention_audit_log
WHERE success = false
  AND error_message LIKE '%timeout%'
ORDER BY timestamp DESC LIMIT 5;
```

**Resolution**:
- Reduce batch size in retention settings
- Schedule operations during off-peak hours
- Consider adding database indexes on date columns
- Increase database timeout configurations

#### Issue: High Memory Usage During Operations
**Symptoms**: System memory consumption spikes during retention operations

**Investigation**:
```bash
# Monitor memory usage during operations
free -h
ps aux --sort=-%mem | head -10

# Check database memory usage
psql -c "SELECT * FROM pg_stat_database WHERE datname = 'tomo_db';"
```

**Resolution**:
- Reduce batch size for cleanup operations
- Configure PostgreSQL memory settings appropriately
- Monitor for memory leaks in application code
- Consider operating during low-usage periods

#### Issue: Unauthorized Access Attempts
**Symptoms**: Security alerts for retention operations from non-admin users

**Investigation**:
```sql
-- Check recent access attempts
SELECT
  timestamp,
  admin_user_id,
  client_ip,
  operation_type,
  success,
  error_message
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND (success = false OR admin_user_id NOT IN (SELECT user_id FROM admin_users))
ORDER BY timestamp DESC;
```

**Resolution**:
- Verify user role assignments
- Review session management configuration
- Check for compromised user accounts
- Update access control policies if needed
- Consider additional security measures (IP restrictions, etc.)

#### Issue: Database Transaction Rollbacks
**Symptoms**: Operations fail with transaction rollback errors

**Investigation**:
```sql
-- Check for transaction conflicts
SELECT
  timestamp,
  operation_id,
  error_message,
  duration_seconds
FROM retention_audit_log
WHERE success = false
  AND error_message LIKE '%transaction%'
ORDER BY timestamp DESC;
```

**Resolution**:
- Check for concurrent database operations
- Verify database configuration for transaction handling
- Review application transaction management code
- Consider adjusting transaction timeout settings

### Performance Optimization

#### Query Optimization
Ensure efficient queries for retention operations:

```sql
-- Create optimized indexes for retention queries
CREATE INDEX CONCURRENTLY idx_log_entries_created_at_partial
ON log_entries(created_at)
WHERE created_at < NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY idx_audit_log_timestamp_desc
ON retention_audit_log(timestamp DESC);

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS)
DELETE FROM log_entries
WHERE created_at < NOW() - INTERVAL '30 days'
LIMIT 1000;
```

#### Batch Size Tuning
Optimize batch sizes based on system performance:

```python
# In retention service configuration
# Start with conservative batch sizes
INITIAL_BATCH_SIZE = 500

# Monitor performance and adjust
# - Increase if operations are too slow
# - Decrease if causing memory/performance issues
# - Typical range: 100-5000 depending on system capacity
```

#### Database Configuration
Optimize PostgreSQL settings for retention operations:

```
# postgresql.conf optimizations for retention operations
work_mem = 256MB                    # Increase for large operations
maintenance_work_mem = 1GB          # For VACUUM and cleanup operations
checkpoint_completion_target = 0.9  # Smooth checkpoint distribution
wal_buffers = 64MB                  # Adequate WAL buffering
random_page_cost = 1.1              # For SSD storage
effective_cache_size = 4GB          # Based on available RAM
```

## Compliance Monitoring

### Audit Trail Verification
Regular verification of audit trail completeness:

```sql
-- Check audit log completeness
SELECT
  DATE(timestamp) as audit_date,
  COUNT(*) as total_operations,
  COUNT(DISTINCT admin_user_id) as unique_admins,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_ops,
  SUM(records_affected) as total_records_processed
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY audit_date DESC;

-- Verify no gaps in audit logging
SELECT
  operation_type,
  MIN(timestamp) as first_logged,
  MAX(timestamp) as last_logged,
  COUNT(*) as total_logged
FROM retention_audit_log
GROUP BY operation_type;
```

### Compliance Reporting
Generate compliance reports for regulatory requirements:

```sql
-- Monthly compliance report
SELECT
  DATE_TRUNC('month', timestamp) as month,
  retention_type,
  COUNT(*) as operations_count,
  SUM(records_affected) as total_records_deleted,
  COUNT(DISTINCT admin_user_id) as unique_operators,
  AVG(duration_seconds) as avg_operation_time
FROM retention_audit_log
WHERE timestamp > NOW() - INTERVAL '12 months'
  AND success = true
  AND operation_type = 'cleanup'
GROUP BY DATE_TRUNC('month', timestamp), retention_type
ORDER BY month DESC, retention_type;
```

### Data Retention Policy Compliance
Monitor adherence to retention policies:

```sql
-- Check for data beyond retention periods
SELECT
  'log_entries' as table_name,
  COUNT(*) as records_beyond_retention,
  MIN(created_at) as oldest_record
FROM log_entries le
JOIN retention_settings rs ON rs.user_id = 'system'
WHERE le.created_at < NOW() - (rs.log_retention_days || ' days')::INTERVAL

UNION ALL

-- Similar checks for other data types
SELECT
  'user_activity' as table_name,
  COUNT(*) as records_beyond_retention,
  MIN(created_at) as oldest_record
FROM user_activity ua
JOIN retention_settings rs ON rs.user_id = 'system'
WHERE ua.created_at < NOW() - (rs.user_data_retention_days || ' days')::INTERVAL;
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-14
**Review Schedule**: Monthly
**Document Owner**: Operations Team