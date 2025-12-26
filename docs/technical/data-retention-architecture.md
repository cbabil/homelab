# Data Retention Technical Architecture

## System Architecture Overview

The Data Retention feature is implemented as a comprehensive, security-first system spanning both frontend React components and backend FastMCP services. The architecture emphasizes security, auditability, and operational safety.

### Component Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │ DataRetention   │    │ useRetention    │                  │
│  │ Settings.tsx    │◄──►│ Settings.ts     │                  │
│  └─────────────────┘    └─────────────────┘                  │
│           │                       │                          │
│           └─────────┬─────────────┘                          │
│                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           settingsService.ts                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend (Python FastMCP)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │ retention_      │◄──►│ retention_      │                  │
│  │ tools.py        │    │ service.py      │                  │
│  └─────────────────┘    └─────────────────┘                  │
│           │                       │                          │
│           └─────────┬─────────────┘                          │
│                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Database Layer                             │ │
│  │  - PostgreSQL/SQLite with transaction safety           │ │
│  │  - Audit logging tables                                │ │
│  │  - Retention policy storage                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Component Structure

#### DataRetentionSettings.tsx
**Location**: `/frontend/src/pages/settings/components/DataRetentionSettings.tsx`

**Purpose**: React component providing secure UI for retention configuration

**Key Features**:
- Dual-slider interface for log and other data retention
- Auto-cleanup toggle with safety warnings
- Multi-step confirmation dialogs with type-to-confirm
- Real-time validation with business logic warnings
- Preview mode integration

**Security Controls**:
```typescript
// Enhanced validation with security checks
useEffect(() => {
  if (!settings) return

  const errors: string[] = []
  let isDangerous = false

  // Check for potentially dangerous configurations
  if (settings.logRetentionDays < 14) {
    errors.push('Log retention below 14 days may affect debugging capabilities')
    isDangerous = true
  }

  if (settings.autoCleanupEnabled && (settings.logRetentionDays < 30)) {
    errors.push('Auto-cleanup with short retention periods requires extra caution')
    isDangerous = true
  }

  setValidationErrors(errors)
  setIsDangerousOperation(isDangerous)
}, [settings])
```

**Confirmation Workflow**:
1. Standard operations: Simple confirm/cancel dialog
2. High-risk operations: Type "DELETE DATA" confirmation
3. Preview required before execution
4. Visual indicators for dangerous configurations

#### LogsPage.tsx
**Location**: `/frontend/src/pages/logs/LogsPage.tsx`

**Purpose**: Provides operational log visibility and maintenance controls for administrators.

**Key Features**:
- Integrates with `LogsDataService` for filtered views and refresh support
- Adds a destructive "Purge Logs" control surfaced through `LogsHeader`
- Uses toast notifications for success/error feedback and updates the list after operations

**Safety Considerations**:
```tsx
const confirmed = window.confirm(
  'This will permanently delete all stored logs. Do you want to continue?'
)

if (!confirmed) {
  return
}

const result = await logsService.purge()
```

The purge action now lives on the dedicated Logs page rather than the retired Monitoring dashboard, keeping destructive operations colocated with detailed log review.

#### useRetentionSettings Hook
**Location**: `/frontend/src/hooks/useRetentionSettings.ts`

**Purpose**: State management and API integration for retention operations

**Key Responsibilities**:
- Settings state management with React hooks
- Validation logic for retention periods
- Integration with settingsService for persistence
- Preview operation coordination
- Error handling and user feedback

**Validation Implementation**:
```typescript
const validateRetentionSettings = (retentionSettings: DataRetentionSettings) => {
  if (retentionSettings.logRetentionDays < RETENTION_LIMITS.LOG_MIN_DAYS ||
      retentionSettings.logRetentionDays > RETENTION_LIMITS.LOG_MAX_DAYS) {
    return {
      valid: false,
      error: `Log retention must be between ${RETENTION_LIMITS.LOG_MIN_DAYS}-${RETENTION_LIMITS.LOG_MAX_DAYS} days`
    }
  }

  // Additional validation logic...
  return { valid: true }
}
```

### Type Definitions

#### settings.ts Types
**Location**: `/frontend/src/types/settings.ts`

**Core Types**:
```typescript
// Data retention settings with security constraints
export interface DataRetentionSettings {
  logRetentionDays: number // 7-365 days
  otherDataRetentionDays: number // 30-3650 days
  autoCleanupEnabled: boolean
  lastCleanupDate?: string
}

// Retention operation results
export interface RetentionOperationResult {
  success: boolean
  operation: RetentionOperationType
  preview?: RetentionPreviewResult
  deletedCounts?: Record<string, number>
  error?: string
}

// Validation constants
export const RETENTION_LIMITS = {
  LOG_MIN_DAYS: 7,
  LOG_MAX_DAYS: 365,
  OTHER_DATA_MIN_DAYS: 30,
  OTHER_DATA_MAX_DAYS: 3650,
} as const
```

## Backend Architecture

### Service Layer

#### retention_service.py
**Location**: `/backend/src/services/retention_service.py`

**Purpose**: Core business logic for data retention operations

**Key Methods**:
- `get_retention_settings()`: Retrieve current retention configuration
- `update_retention_settings()`: Update retention policies with validation
- `preview_cleanup()`: Dry-run cleanup operations showing impact
- `perform_cleanup()`: Execute actual data deletion with transaction safety
- `validate_admin_access()`: Verify administrator permissions and session

**Security Implementation**:
```python
async def validate_admin_access(self, user_id: str, session_token: str) -> SecurityValidationResult:
    """
    Comprehensive admin access validation for retention operations.
    Verifies user role, active session, and additional security checks.
    """
    try:
        # Validate session is active and belongs to user
        session_valid = await self.session_service.validate_session(session_token, user_id)
        if not session_valid:
            return SecurityValidationResult(
                is_valid=False,
                error_message="Invalid or expired session"
            )

        # Verify user has admin role
        is_admin = await self.auth_service.has_role(user_id, "data_retention_admin")
        if not is_admin:
            return SecurityValidationResult(
                is_valid=False,
                is_admin=False,
                error_message="Insufficient privileges for retention operations"
            )

        return SecurityValidationResult(
            is_valid=True,
            is_admin=True,
            session_valid=True,
            user_id=user_id
        )

    except Exception as e:
        logger.error("Admin validation failed", error=str(e))
        return SecurityValidationResult(
            is_valid=False,
            error_message=f"Validation error: {str(e)}"
        )
```

**Transaction Safety**:
```python
async def perform_cleanup(self, request: CleanupRequest) -> CleanupResult:
    """Execute cleanup with full transaction safety and audit logging."""
    operation_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        # Begin transaction
        async with self.database.transaction() as tx:
            # Perform deletions in batches
            total_deleted = 0
            for batch in self.get_deletion_batches(request):
                deleted_count = await self.delete_batch(tx, batch)
                total_deleted += deleted_count

                # Progress monitoring
                await self.update_operation_progress(operation_id, total_deleted)

            # Audit logging
            await self.audit_service.log_operation(
                operation_id=operation_id,
                operation_type=RetentionOperation.CLEANUP,
                admin_user_id=request.admin_user_id,
                records_affected=total_deleted,
                success=True
            )

            return CleanupResult(
                operation_id=operation_id,
                success=True,
                records_affected=total_deleted,
                # ... additional result data
            )

    except Exception as e:
        # Transaction automatically rolled back
        logger.error("Cleanup operation failed", operation_id=operation_id, error=str(e))

        # Log failure for audit
        await self.audit_service.log_operation(
            operation_id=operation_id,
            operation_type=RetentionOperation.CLEANUP,
            admin_user_id=request.admin_user_id,
            success=False,
            error_message=str(e)
        )

        return CleanupResult(
            operation_id=operation_id,
            success=False,
            error_message=str(e)
        )
```

### MCP Tools Layer

#### retention_tools.py
**Location**: `/backend/src/tools/retention_tools.py`

**Purpose**: FastMCP integration layer exposing retention operations

**Available Tools**:
1. `get_retention_settings`: Retrieve current retention configuration
2. `update_retention_settings`: Update retention policies with validation
3. `preview_cleanup`: Execute dry-run cleanup operations
4. `execute_cleanup`: Perform actual data deletion
5. `get_cleanup_history`: Retrieve audit history of operations
6. `validate_retention_policy`: Validate settings without saving

**Security Controls per Tool**:
```python
async def execute_cleanup(self, request_data: Dict[str, Any], ctx: Context = None) -> Dict[str, Any]:
    """Execute data cleanup operations with comprehensive security validation."""

    # Extract client metadata for audit logging
    client_ip = ctx.meta.get('clientIp', 'unknown') if ctx else 'unknown'
    user_agent = ctx.meta.get('userAgent', 'unknown') if ctx else 'unknown'

    # Validate and parse cleanup request
    try:
        request = CleanupRequest(**request_data)
    except Exception as validation_error:
        return {
            "success": False,
            "message": f"Invalid cleanup request: {str(validation_error)}",
            "error": "REQUEST_VALIDATION_ERROR"
        }

    # Additional security check for non-dry-run operations
    if not request.dry_run:
        logger.warning("Non-dry-run cleanup operation requested",
                     admin_user_id=request.admin_user_id,
                     retention_type=request.retention_type,
                     client_ip=client_ip)

        # Require explicit force_cleanup flag for actual deletion
        if not request.force_cleanup:
            return {
                "success": False,
                "message": "Actual cleanup requires force_cleanup flag and prior dry-run",
                "error": "FORCE_CLEANUP_REQUIRED"
            }
```

### Data Models

#### retention.py Models
**Location**: `/backend/src/models/retention.py`

**Key Models**:

```python
class DataRetentionSettings(BaseModel):
    """Data retention policy settings with business logic validation."""

    log_retention_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Log retention period in days (7-365)"
    )

    user_data_retention_days: int = Field(
        default=365,
        ge=30,
        le=3650,
        description="User data retention period in days (30-3650)"
    )

    audit_log_retention_days: int = Field(
        default=2555,  # 7 years for compliance
        ge=365,
        le=3650,
        description="Audit log retention period in days (365-3650)"
    )

    @validator('audit_log_retention_days')
    def validate_audit_retention(cls, v):
        """Validate audit log retention period for compliance."""
        if v < 365:
            raise ValueError('Audit logs must be retained for at least 1 year')
        return v

class CleanupRequest(BaseModel):
    """Request for cleanup operations with security validation."""

    retention_type: RetentionType = Field(..., description="Type of data to clean up")
    dry_run: bool = Field(default=True, description="Whether to perform dry-run (mandatory for first request)")
    admin_user_id: str = Field(..., min_length=1, description="Admin user requesting cleanup")
    session_token: str = Field(..., min_length=1, description="Session token for verification")
    force_cleanup: bool = Field(default=False, description="Force cleanup even if risky")

class CleanupResult(BaseModel):
    """Result of cleanup operations with comprehensive audit information."""

    operation_id: str = Field(..., description="Unique operation identifier")
    retention_type: RetentionType = Field(..., description="Type of data cleaned")
    operation: RetentionOperation = Field(..., description="Type of operation performed")
    success: bool = Field(..., description="Operation success status")
    records_affected: int = Field(default=0, ge=0, description="Number of records affected")
    admin_user_id: str = Field(..., description="Admin user who performed operation")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")
```

## Database Architecture

### Schema Design

#### Retention Settings Table
```sql
CREATE TABLE retention_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    log_retention_days INTEGER NOT NULL CHECK (log_retention_days BETWEEN 7 AND 365),
    user_data_retention_days INTEGER NOT NULL CHECK (user_data_retention_days BETWEEN 30 AND 3650),
    metrics_retention_days INTEGER NOT NULL CHECK (metrics_retention_days BETWEEN 7 AND 730),
    audit_log_retention_days INTEGER NOT NULL CHECK (audit_log_retention_days BETWEEN 365 AND 3650),
    auto_cleanup_enabled BOOLEAN DEFAULT FALSE,
    cleanup_batch_size INTEGER DEFAULT 1000 CHECK (cleanup_batch_size BETWEEN 100 AND 10000),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id VARCHAR(255),
    UNIQUE(user_id)
);
```

#### Audit Trail Table
```sql
CREATE TABLE retention_audit_log (
    id SERIAL PRIMARY KEY,
    operation_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation_type VARCHAR(50) NOT NULL, -- 'dry_run', 'cleanup', 'settings_update'
    retention_type VARCHAR(50), -- 'logs', 'user_data', 'metrics', 'audit_logs'
    admin_user_id VARCHAR(255) NOT NULL,
    client_ip INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    records_affected INTEGER DEFAULT 0,
    space_freed_mb DECIMAL(10,2) DEFAULT 0.0,
    duration_seconds DECIMAL(10,3) DEFAULT 0.0,
    error_message TEXT,
    metadata JSONB,
    CONSTRAINT valid_operation_type CHECK (operation_type IN ('dry_run', 'cleanup', 'settings_update', 'policy_validation'))
);

-- Indexes for efficient audit queries
CREATE INDEX idx_retention_audit_timestamp ON retention_audit_log(timestamp DESC);
CREATE INDEX idx_retention_audit_admin_user ON retention_audit_log(admin_user_id);
CREATE INDEX idx_retention_audit_operation ON retention_audit_log(operation_type, success);
```

### Transaction Management

**Transaction Scope**: Each cleanup operation is wrapped in a database transaction to ensure consistency:

1. **Begin Transaction**: Start database transaction
2. **Validate Permissions**: Check admin access within transaction
3. **Execute Deletions**: Perform deletions in batches
4. **Update Audit Log**: Record operation details
5. **Commit/Rollback**: Commit on success, automatic rollback on error

**Batch Processing**: Large deletions are processed in configurable batches (default 1,000 records) to:
- Prevent long-running transactions
- Allow for progress monitoring
- Enable operation cancellation
- Reduce database lock contention

## API Reference

### MCP Tool Specifications

#### get_retention_settings
**Purpose**: Retrieve current retention configuration for authenticated user

**Parameters**:
- `user_id` (string, required): User identifier for settings retrieval

**Response**:
```json
{
  "success": true,
  "data": {
    "log_retention_days": 30,
    "user_data_retention_days": 365,
    "metrics_retention_days": 90,
    "audit_log_retention_days": 2555,
    "auto_cleanup_enabled": false,
    "cleanup_batch_size": 1000,
    "last_updated": "2025-01-14T10:30:00Z",
    "updated_by_user_id": "admin123"
  },
  "message": "Retention settings retrieved successfully"
}
```

#### update_retention_settings
**Purpose**: Update retention configuration with validation and audit logging

**Parameters**:
- `settings_data` (object, required): New retention settings
- `user_id` (string, required): Admin user making the update

**Request Example**:
```json
{
  "settings_data": {
    "log_retention_days": 45,
    "user_data_retention_days": 730,
    "auto_cleanup_enabled": true
  },
  "user_id": "admin123"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "log_retention_days": 45,
    "user_data_retention_days": 730,
    "auto_cleanup_enabled": true,
    // ... full updated settings
  },
  "message": "Retention settings updated successfully"
}
```

#### preview_cleanup
**Purpose**: Perform dry-run cleanup operation showing impact without actual deletion

**Parameters**:
- `request_data` (object, required): Cleanup request with dry_run=true

**Request Example**:
```json
{
  "retention_type": "logs",
  "dry_run": true,
  "admin_user_id": "admin123",
  "session_token": "sess_abc123...",
  "batch_size": 1000
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "retention_type": "logs",
    "affected_records": 15420,
    "oldest_record_date": "2024-10-15T08:30:00Z",
    "newest_record_date": "2024-12-15T16:45:00Z",
    "estimated_space_freed_mb": 245.7,
    "cutoff_date": "2024-12-15T00:00:00Z"
  },
  "message": "Cleanup preview completed successfully"
}
```

#### execute_cleanup
**Purpose**: Execute actual cleanup operation with full security validation

**Parameters**:
- `request_data` (object, required): Cleanup request with force_cleanup=true

**Request Example**:
```json
{
  "retention_type": "logs",
  "dry_run": false,
  "admin_user_id": "admin123",
  "session_token": "sess_abc123...",
  "force_cleanup": true,
  "batch_size": 1000
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "operation_id": "op_789xyz...",
    "retention_type": "logs",
    "operation": "cleanup",
    "success": true,
    "records_affected": 15420,
    "space_freed_mb": 245.7,
    "duration_seconds": 127.45,
    "start_time": "2025-01-14T15:30:00Z",
    "end_time": "2025-01-14T15:32:07Z",
    "admin_user_id": "admin123"
  },
  "message": "Cleanup operation completed"
}
```

### Error Handling

#### Common Error Codes
- `MISSING_USER_ID`: User ID required for operation
- `MISSING_SETTINGS_DATA`: Settings data required for update
- `SETTINGS_VALIDATION_ERROR`: Invalid settings data provided
- `REQUEST_VALIDATION_ERROR`: Invalid cleanup request format
- `FORCE_CLEANUP_REQUIRED`: Actual cleanup requires force flag
- `INSUFFICIENT_PRIVILEGES`: User lacks required admin permissions
- `SESSION_EXPIRED`: Admin session no longer valid
- `PREVIEW_FAILED`: Preview operation could not be completed
- `CLEANUP_EXECUTION_FAILED`: Cleanup operation failed during execution

#### Error Response Format
```json
{
  "success": false,
  "message": "Detailed error description",
  "error": "ERROR_CODE",
  "details": {
    "validation_errors": ["Specific validation failure"],
    "suggested_actions": ["Recommended remediation steps"]
  }
}
```

## Security Architecture

### Multi-Layer Security Model

1. **Authentication Layer**: Session-based authentication with token validation
2. **Authorization Layer**: Role-based access control with admin-only operations
3. **Input Validation**: Comprehensive validation at both frontend and backend
4. **Operation Security**: Mandatory preview, explicit confirmation, and audit logging
5. **Data Protection**: Transaction safety with automatic rollback on errors

### Security Controls Matrix

| Operation | Authentication | Authorization | Validation | Audit | Transaction |
|-----------|----------------|---------------|------------|--------|-------------|
| View Settings | ✓ Session | ✓ User Role | ✓ Input | ✓ Access Log | N/A |
| Update Settings | ✓ Session | ✓ Admin Role | ✓ Business Logic | ✓ Change Log | ✓ Safe Update |
| Preview Cleanup | ✓ Session | ✓ Admin Role | ✓ Request Format | ✓ Operation Log | ✓ Read-Only |
| Execute Cleanup | ✓ Session | ✓ Admin Role | ✓ Multi-Layer | ✓ Full Audit | ✓ Transaction Safe |

### Audit Trail Architecture

**Audit Data Collection**: Every retention operation generates comprehensive audit records including:
- Operation metadata (type, timing, scope)
- User context (admin ID, session, IP address)
- System context (application version, database state)
- Results (success/failure, records affected, errors)

**Audit Data Protection**:
- Separate database table with extended retention (7+ years)
- Cryptographic integrity protection
- Restricted access controls
- Backup and archival procedures

**Audit Data Analysis**:
- Real-time security monitoring
- Compliance reporting capabilities
- Anomaly detection for unusual patterns
- Historical trend analysis

## Performance Considerations

### Scalability Design
- **Batch Processing**: Large operations divided into manageable batches
- **Progress Monitoring**: Real-time progress updates for long operations
- **Resource Management**: Configurable batch sizes and timeouts
- **Database Optimization**: Indexed queries and efficient deletion strategies

### Performance Monitoring
- **Operation Timing**: Track duration of cleanup operations
- **Database Impact**: Monitor database performance during operations
- **Resource Usage**: Track memory and CPU usage during large operations
- **Storage Impact**: Measure actual space freed vs. estimates

### Optimization Strategies
- **Index Optimization**: Proper indexes on date fields for efficient queries
- **Batch Tuning**: Configurable batch sizes based on system capacity
- **Off-Peak Scheduling**: Recommend operations during low-activity periods
- **Resource Limiting**: Prevent operations from overwhelming system resources

---

**Document Version**: 1.0
**Last Updated**: 2025-01-14
**Component Versions**: Frontend v1.0, Backend v1.0
**API Version**: v1.0
