# Data Retention User Guide

## Overview

The Data Retention feature provides automated cleanup of logs and other data based on configurable retention policies. This feature helps manage storage space while ensuring important data is preserved according to your requirements.

> **Important:** Data deletion is permanent and cannot be undone. Always preview cleanup operations before execution.

## Accessing Data Retention Settings

1. Navigate to **Settings** in the sidebar
2. Select **General** tab
3. Scroll down to the **Data Retention** section

## Configuration Options

### Auto-cleanup Toggle
- **Purpose**: Enables/disables automatic cleanup operations
- **Default**: Disabled for safety
- **Recommendation**: Only enable after thoroughly testing with preview mode

### Log Retention Slider
- **Range**: 7-365 days
- **Purpose**: Controls how long system logs are kept
- **Default**: 30 days
- **Impact**: Affects troubleshooting and audit capabilities

**Guidelines:**
- **7-13 days**: Minimal retention, suitable for high-volume systems with external log storage
- **14-30 days**: Standard retention, good balance of storage and debugging capability
- **31-90 days**: Extended retention for detailed analysis needs
- **91-365 days**: Long-term retention for compliance requirements

### Other Data Retention Slider
- **Range**: 30-3650 days (10 years maximum)
- **Purpose**: Controls retention of non-log data including metrics and user data
- **Default**: 365 days (1 year)
- **Step**: 30-day increments

**Data Types Affected:**
- User activity metrics
- System performance data
- Non-audit operational data
- Temporary files and cache

## Using Preview Mode

### Step 1: Configure Retention Periods
1. Adjust sliders to desired retention periods
2. Review any validation warnings that appear
3. Settings are automatically saved when changed

### Step 2: Preview Cleanup
1. Click **Preview Cleanup** button
2. Wait for analysis to complete
3. Review the preview dialog showing:
   - Number of log entries to be deleted
   - Number of other records to be deleted
   - Estimated storage space to be freed
   - Affected database tables

### Step 3: Make Informed Decision
- **Low Impact**: Few records, small space savings
- **Medium Impact**: Moderate cleanup, verify retention periods are appropriate
- **High Impact**: Large deletion, consider extending retention periods

## Executing Cleanup Operations

### Standard Cleanup Process
1. Complete preview process first
2. Click **Continue** in preview dialog
3. Confirm deletion in the security dialog
4. Monitor operation progress

### High-Risk Operations
For potentially dangerous configurations (short retention periods), additional security measures apply:

1. **Enhanced Warnings**: Orange alerts for risky configurations
2. **Confirmation Text**: Must type "DELETE DATA" exactly
3. **Multi-step Verification**: Cannot proceed without proper confirmation

### Risk Indicators
The system identifies high-risk operations based on:
- Log retention below 14 days
- Other data retention below 90 days
- Auto-cleanup enabled with short retention periods

## Security Features

### Multi-layer Protection
- **Preview First**: Mandatory dry-run before actual deletion
- **Admin Verification**: Operations require administrative privileges
- **Session Validation**: Active, valid admin session required
- **Audit Logging**: All operations logged for compliance

### Confirmation Requirements
- **Standard Operations**: Simple confirm/cancel dialog
- **High-Risk Operations**: Type-to-confirm with "DELETE DATA" text
- **Auto-cleanup**: Additional verification for automated operations

## Best Practices

### Retention Period Planning
1. **Start Conservative**: Begin with longer retention periods
2. **Monitor Usage**: Track how often older data is accessed
3. **Adjust Gradually**: Reduce retention periods incrementally
4. **Document Decisions**: Record retention policy decisions

### Regular Maintenance
- **Monthly Review**: Check retention settings and cleanup results
- **Storage Monitoring**: Monitor available disk space trends
- **Policy Updates**: Update retention periods based on usage patterns
- **Compliance Check**: Verify retention meets regulatory requirements

### Before First Use
1. **Backup Critical Data**: Ensure important data is backed up
2. **Test with Preview**: Run multiple preview operations
3. **Start with Longer Periods**: Use conservative retention settings initially
4. **Monitor Results**: Watch cleanup operations closely at first

## Troubleshooting

### Common Issues

#### Settings Not Saving
- **Cause**: Network connectivity or session timeout
- **Solution**: Refresh page and verify admin session is active
- **Prevention**: Save changes promptly after making adjustments

#### Preview Shows No Data
- **Cause**: No data older than retention periods exists
- **Solution**: Normal behavior, no action needed
- **Note**: Preview will show results once data ages beyond retention periods

#### Large Number of Records in Preview
- **Cause**: Very short retention periods or accumulated old data
- **Solution**: Consider extending retention periods before cleanup
- **Safety**: Use preview mode to understand impact before proceeding

#### Cleanup Operation Failed
- **Cause**: Database connectivity or permission issues
- **Solution**: Check system logs and contact administrator
- **Recovery**: Operations are transactional and safe to retry

### Error Messages

#### "User ID is required"
- **Cause**: Session expired or authentication issue
- **Solution**: Log out and log back in with admin credentials

#### "Invalid settings data"
- **Cause**: Retention periods outside valid ranges
- **Solution**: Verify slider values are within permitted ranges

#### "Force cleanup required"
- **Cause**: Attempting actual deletion without required security confirmations
- **Solution**: Complete preview process and security confirmations first

### Getting Help

For additional support:
1. Check system logs for detailed error messages
2. Contact your system administrator
3. Review audit logs for operation history
4. Consult technical documentation for advanced troubleshooting

## Data Recovery

> **Critical Warning:** Data deletion is permanent and irreversible.

The system does not provide data recovery capabilities after cleanup operations. Ensure:
- Regular system backups are in place
- Retention periods are carefully planned
- Preview mode is always used before execution
- Critical data is preserved outside the cleanup scope

## Compliance Considerations

### Audit Requirements
- All operations are logged with timestamps and user identification
- Audit logs have extended retention (minimum 1 year, typically 7 years)
- Failed operations are logged with error details
- Security events are tracked separately

### Regulatory Compliance
Consider legal and regulatory requirements:
- **GDPR**: Right to erasure vs. audit trail requirements
- **SOX**: Financial record retention requirements
- **HIPAA**: Healthcare data retention mandates
- **Industry-specific**: Check sector-specific retention requirements

## Version History

**Version 1.0** (2025-01-14)
- Initial release with dual-slider configuration
- Preview and security confirmation workflows
- Admin-only operations with audit logging
- Comprehensive validation and safety checks