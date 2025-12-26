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
}

// Data retention settings with security constraints
export interface DataRetentionSettings {
  logRetentionDays: number // 14-365 days
  otherDataRetentionDays: number // 14-365 days
  autoCleanupEnabled: boolean
  lastCleanupDate?: string
}

// System and performance settings
export interface SystemSettings {
  autoRefresh: boolean
  refreshInterval: number // seconds
  maxLogEntries: number
  enableDebugMode: boolean
  dataRetention: DataRetentionSettings
}

// Complete user settings interface
export interface UserSettings {
  security: SecuritySettings
  ui: UISettings
  system: SystemSettings
  lastUpdated: string
  version: number
}

// Settings storage keys
export const SETTINGS_STORAGE_KEYS = {
  USER_SETTINGS: 'homelab-user-settings',
  SETTINGS_VERSION: 'homelab-settings-version'
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
    enableDebugMode: false,
    dataRetention: {
      logRetentionDays: 14, // Default 14 days for logs
      otherDataRetentionDays: 14, // Default 14 days for other data
      autoCleanupEnabled: false, // Disabled by default for safety
      lastCleanupDate: undefined
    }
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

// Data retention validation constants
export const RETENTION_LIMITS = {
  LOG_MIN_DAYS: 14,
  LOG_MAX_DAYS: 365,
  OTHER_DATA_MIN_DAYS: 14,
  OTHER_DATA_MAX_DAYS: 365,
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