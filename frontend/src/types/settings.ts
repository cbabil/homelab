/**
 * Settings Types
 * 
 * Type definitions for user settings including session configuration,
 * security preferences, and application settings.
 */

// Session timeout configuration options
export type SessionTimeout = '15m' | '30m' | '1h' | '4h' | '8h' | '24h'

// Session management settings
export interface SessionSettings {
  timeout: SessionTimeout
  idleDetection: boolean
  showWarningMinutes: number
  extendOnActivity: boolean
}

// Security settings
export interface SecuritySettings {
  session: SessionSettings
  requirePasswordChange: boolean
  passwordChangeInterval: number // days
  twoFactorEnabled: boolean
}

// User interface preferences
export interface UISettings {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string // IANA timezone identifier
  notifications: boolean
  compactMode: boolean
  sidebarCollapsed: boolean
  refreshRate?: number // Auto-refresh interval in seconds
  defaultPage?: string // Default page to show on login
}

// Retention settings (fetched from backend via MCP)
export interface RetentionSettings {
  log_retention: number   // 7-365 days - applies to all log types
  data_retention: number  // 7-365 days - applies to all data types
  last_updated?: string
  updated_by_user_id?: string
}

// Application management settings
export interface ApplicationSettings {
  autoRefreshStatus: boolean // Auto-refresh Docker status on page load
  statusRefreshInterval: number // seconds, 0 = only on page load, >0 = periodic refresh
}

// Notification preferences
export interface NotificationSettings {
  serverAlerts: boolean      // Alert on server status changes
  resourceAlerts: boolean    // Alert on resource thresholds
  updateAlerts: boolean      // Alert on available updates
}

// Server connection settings
export interface ServerConnectionSettings {
  connectionTimeout: number  // SSH connection timeout in seconds
  retryCount: number         // Number of retry attempts
  autoRetry: boolean         // Automatically retry failed connections
}

// Agent settings
export interface AgentConnectionSettings {
  preferAgent: boolean      // Prefer agent over SSH when available
  autoUpdate: boolean       // Auto-update agents when new versions available
  heartbeatInterval: number // Heartbeat interval in seconds
  heartbeatTimeout: number  // Timeout before marking agent as stale
  commandTimeout: number    // Command execution timeout in seconds
}

// System and performance settings
export interface SystemSettings {
  autoRefresh: boolean
  refreshInterval: number // seconds
  maxLogEntries: number
  enableDebugMode: boolean
}

// Complete user settings interface
export interface UserSettings {
  security: SecuritySettings
  ui: UISettings
  system: SystemSettings
  applications: ApplicationSettings
  notifications: NotificationSettings
  servers: ServerConnectionSettings
  agent: AgentConnectionSettings
  lastUpdated: string
  version: number
}

// Settings storage keys
export const SETTINGS_STORAGE_KEYS = {
  USER_SETTINGS: 'tomo-user-settings',
  SETTINGS_VERSION: 'tomo-settings-version'
} as const

// Default settings configuration
export const DEFAULT_SETTINGS: UserSettings = {
  security: {
    session: {
      timeout: '1h',
      idleDetection: true,
      showWarningMinutes: 5,
      extendOnActivity: true
    },
    requirePasswordChange: false,
    passwordChangeInterval: 90,
    twoFactorEnabled: false
  },
  ui: {
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    notifications: true,
    compactMode: false,
    sidebarCollapsed: false
  },
  system: {
    autoRefresh: true,
    refreshInterval: 30,
    maxLogEntries: 1000,
    enableDebugMode: false
  },
  applications: {
    autoRefreshStatus: true, // Auto-check Docker status on page load
    statusRefreshInterval: 0 // 0 = only on page load, no periodic refresh
  },
  notifications: {
    serverAlerts: true,
    resourceAlerts: true,
    updateAlerts: false
  },
  servers: {
    connectionTimeout: 30,
    retryCount: 3,
    autoRetry: true
  },
  agent: {
    preferAgent: true,
    autoUpdate: true,
    heartbeatInterval: 30,
    heartbeatTimeout: 90,
    commandTimeout: 120
  },
  lastUpdated: new Date().toISOString(),
  version: 1
}

// Session timeout values in milliseconds
export const SESSION_TIMEOUT_VALUES: Record<SessionTimeout, number> = {
  '15m': 15 * 60 * 1000,
  '30m': 30 * 60 * 1000,
  '1h': 60 * 60 * 1000,
  '4h': 4 * 60 * 60 * 1000,
  '8h': 8 * 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000
}

// Retention validation constants
export const RETENTION_LIMITS = {
  LOG_MIN: 7,
  LOG_MAX: 365,
  DATA_MIN: 7,
  DATA_MAX: 365,
} as const

// Data retention operation types
export type RetentionOperationType = 'preview' | 'execute'

export interface RetentionPreviewResult {
  logEntriesAffected: number
  otherDataAffected: number
  estimatedSpaceFreed: string
  affectedTables: string[]
}

export interface RetentionOperationResult {
  success: boolean
  operation: RetentionOperationType
  preview?: RetentionPreviewResult
  deletedCounts?: Record<string, number>
  error?: string
}

// Settings validation interface
export interface SettingsValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

// Settings update result
export interface SettingsUpdateResult {
  success: boolean
  settings?: UserSettings
  error?: string
}