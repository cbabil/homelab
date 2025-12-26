/**
 * Settings Service
 *
 * Service for managing user settings with database persistence via MCP
 * and localStorage fallback. Provides settings management API with
 * validation, migration support, and real-time synchronization.
 */

import {
  UserSettings,
  DEFAULT_SETTINGS,
  SETTINGS_STORAGE_KEYS,
  SettingsValidation,
  SettingsUpdateResult,
  SessionTimeout,
  SESSION_TIMEOUT_VALUES,
  RETENTION_LIMITS
} from '@/types/settings'
import { SettingsMcpClient } from '@/services/settingsMcpClient'
import { mcpLogger } from '@/services/systemLogger'

class SettingsService {
  private settings: UserSettings | null = null
  private listeners: Set<(settings: UserSettings) => void> = new Set()
  private mcpClient: SettingsMcpClient | null = null
  private userId: string = 'default'
  private useDatabase: boolean = true // Flag to control database vs localStorage

  /**
   * Initialize settings service and load from database or storage
   */
  async initialize(mcpClient?: SettingsMcpClient | null, userId: string = 'default'): Promise<UserSettings> {
    this.mcpClient = mcpClient || null
    this.userId = userId

    mcpLogger.info('Initializing settings service', {
      hasMcpClient: !!this.mcpClient,
      userId: this.userId
    })

    try {
      // Try to load from database first if MCP client is available
      if (this.mcpClient && this.mcpClient.isBackendConnected()) {
        const result = await this.loadFromDatabase()
        if (result.success && result.settings) {
          this.settings = result.settings
          this.useDatabase = true

          // Cache to localStorage for offline access
          await this.saveToLocalStorage(this.settings)

          mcpLogger.info('Settings loaded from database successfully')
          return this.settings
        } else {
          mcpLogger.warn('Failed to load from database, falling back to localStorage', { error: result.error })
        }
      }

      // Fallback to localStorage
      this.useDatabase = false
      const result = await this.loadFromLocalStorage()
      this.settings = result

      mcpLogger.info('Settings loaded from localStorage')
      return this.settings
    } catch (error) {
      mcpLogger.error('Failed to initialize settings', error)
      this.settings = { ...DEFAULT_SETTINGS }
      this.useDatabase = false
      return this.settings
    }
  }

  /**
   * Get current settings
   */
  getSettings(): UserSettings {
    if (!this.settings) {
      throw new Error('Settings not initialized. Call initialize() first.')
    }
    return { ...this.settings }
  }

  /**
   * Update specific settings section
   */
  async updateSettings(
    section: keyof Omit<UserSettings, 'lastUpdated' | 'version'>,
    updates: Partial<UserSettings[typeof section]>
  ): Promise<SettingsUpdateResult> {
    if (!this.settings) {
      return { success: false, error: 'Settings not initialized' }
    }

    try {
      const newSettings: UserSettings = {
        ...this.settings,
        [section]: { ...this.settings[section], ...updates },
        lastUpdated: new Date().toISOString(),
        version: this.settings.version + 1
      }

      // Validate locally first
      const validation = this.validateSettings(newSettings)

      if (!validation.isValid) {
        return {
          success: false,
          error: `Validation failed: ${validation.errors.join(', ')}`
        }
      }

      // Try to save to database first
      if (this.useDatabase && this.mcpClient && this.mcpClient.isBackendConnected()) {
        const result = await this.saveToDatabase(newSettings)
        if (result.success) {
          this.settings = result.settings || newSettings
          // Also save to localStorage as cache
          await this.saveToLocalStorage(this.settings)
          this.notifyListeners(this.settings)
          return { success: true, settings: this.settings }
        } else {
          mcpLogger.warn('Failed to save to database, falling back to localStorage', { error: result.error })
          // Continue to localStorage fallback
        }
      }

      // Fallback to localStorage
      await this.saveToLocalStorage(newSettings)
      this.settings = newSettings
      this.notifyListeners(newSettings)

      return { success: true, settings: newSettings }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Reset settings to defaults
   */
  async resetSettings(): Promise<SettingsUpdateResult> {
    try {
      const defaultSettings: UserSettings = {
        ...DEFAULT_SETTINGS,
        lastUpdated: new Date().toISOString(),
        version: 1
      }

      // Try database reset first (admin operation)
      if (this.useDatabase && this.mcpClient && this.mcpClient.isBackendConnected()) {
        const result = await this.mcpClient.resetUserSettings(this.userId)
        if (result.success && result.settings) {
          this.settings = result.settings
          // Cache to localStorage
          await this.saveToLocalStorage(this.settings)
          this.notifyListeners(this.settings)
          return { success: true, settings: this.settings }
        } else {
          mcpLogger.warn('Failed to reset via database, using local reset', { error: result.error })
        }
      }

      // Fallback to local reset
      await this.saveToLocalStorage(defaultSettings)
      this.settings = defaultSettings
      this.notifyListeners(defaultSettings)

      return { success: true, settings: defaultSettings }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to reset'
      }
    }
  }

  /**
   * Get session timeout in milliseconds
   */
  getSessionTimeoutMs(): number {
    if (!this.settings) {
      return SESSION_TIMEOUT_VALUES[DEFAULT_SETTINGS.security.session.timeout]
    }
    return SESSION_TIMEOUT_VALUES[this.settings.security.session.timeout]
  }

  /**
   * Subscribe to settings changes
   */
  subscribe(callback: (settings: UserSettings) => void): () => void {
    this.listeners.add(callback)
    return () => this.listeners.delete(callback)
  }

  /**
   * Load settings from database via MCP
   */
  private async loadFromDatabase(): Promise<SettingsUpdateResult> {
    if (!this.mcpClient) {
      return { success: false, error: 'MCP client not available' }
    }

    try {
      const result = await this.mcpClient.getSettings(this.userId)
      if (result.success && result.settings) {
        const migrated = this.migrateSettings(result.settings)
        const validation = this.validateSettings(migrated)

        if (validation.isValid) {
          return { success: true, settings: migrated }
        } else {
          mcpLogger.warn('Settings validation failed for database data', validation.errors)
          return { success: false, error: 'Invalid settings data from database' }
        }
      }
      return result
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Database load failed'
      }
    }
  }

  /**
   * Save settings to database via MCP
   */
  private async saveToDatabase(settings: UserSettings): Promise<SettingsUpdateResult> {
    if (!this.mcpClient) {
      return { success: false, error: 'MCP client not available' }
    }

    try {
      const result = await this.mcpClient.updateSettings(this.userId, settings)
      return result
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Database save failed'
      }
    }
  }

  /**
   * Load settings from localStorage
   */
  private async loadFromLocalStorage(): Promise<UserSettings> {
    try {
      const stored = localStorage.getItem(SETTINGS_STORAGE_KEYS.USER_SETTINGS)

      if (stored) {
        const parsedSettings = JSON.parse(stored) as UserSettings
        const migrated = this.migrateSettings(parsedSettings)
        const validated = this.validateSettings(migrated)

        if (validated.isValid) {
          return migrated
        }
      }

      // Fallback to defaults if no valid settings found
      const defaultSettings = { ...DEFAULT_SETTINGS }
      await this.saveToLocalStorage(defaultSettings)
      return defaultSettings
    } catch (error) {
      mcpLogger.error('Failed to load from localStorage', error)
      return { ...DEFAULT_SETTINGS }
    }
  }

  /**
   * Save settings to localStorage
   */
  private async saveToLocalStorage(settings: UserSettings): Promise<void> {
    try {
      localStorage.setItem(
        SETTINGS_STORAGE_KEYS.USER_SETTINGS,
        JSON.stringify(settings)
      )
      localStorage.setItem(
        SETTINGS_STORAGE_KEYS.SETTINGS_VERSION,
        settings.version.toString()
      )
    } catch (error) {
      throw new Error(`Failed to save settings: ${error}`)
    }
  }

  /**
   * Validate settings object
   */
  private validateSettings(settings: UserSettings): SettingsValidation {
    const errors: string[] = []
    const warnings: string[] = []

    // Validate session timeout
    const validTimeouts = Object.keys(SESSION_TIMEOUT_VALUES) as SessionTimeout[]
    if (!validTimeouts.includes(settings.security.session.timeout)) {
      errors.push('Invalid session timeout value')
    }

    // Validate numeric values
    if (settings.security.session.showWarningMinutes < 1 || 
        settings.security.session.showWarningMinutes > 30) {
      warnings.push('Warning minutes should be between 1-30')
    }

    if (settings.system.refreshInterval < 5) {
      warnings.push('Refresh interval too low, may impact performance')
    }

    // Validate retention settings
    const retention = settings.system.dataRetention
    if (retention.logRetentionDays < RETENTION_LIMITS.LOG_MIN_DAYS ||
        retention.logRetentionDays > RETENTION_LIMITS.LOG_MAX_DAYS) {
      errors.push(`Log retention days must be between ${RETENTION_LIMITS.LOG_MIN_DAYS}-${RETENTION_LIMITS.LOG_MAX_DAYS}`)
    }

    if (retention.otherDataRetentionDays < RETENTION_LIMITS.OTHER_DATA_MIN_DAYS ||
        retention.otherDataRetentionDays > RETENTION_LIMITS.OTHER_DATA_MAX_DAYS) {
      errors.push(`Other data retention days must be between ${RETENTION_LIMITS.OTHER_DATA_MIN_DAYS}-${RETENTION_LIMITS.OTHER_DATA_MAX_DAYS}`)
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    }
  }

  /**
   * Migrate settings from older versions
   */
  private migrateSettings(settings: any): UserSettings {
    // Handle version 1 (current) - no migration needed
    if (settings.version === 1) {
      return settings as UserSettings
    }

    // For older or missing versions, merge with defaults
    return {
      ...DEFAULT_SETTINGS,
      ...settings,
      lastUpdated: new Date().toISOString(),
      version: 1
    }
  }

  /**
   * Set MCP client for database operations
   */
  setMcpClient(mcpClient: SettingsMcpClient | null): void {
    this.mcpClient = mcpClient
    mcpLogger.info('MCP client updated', { hasMcpClient: !!mcpClient })
  }

  /**
   * Check if using database persistence
   */
  isUsingDatabase(): boolean {
    return this.useDatabase && !!this.mcpClient && this.mcpClient.isBackendConnected()
  }

  /**
   * Force sync from database (useful for refreshing settings)
   */
  async syncFromDatabase(): Promise<SettingsUpdateResult> {
    if (!this.mcpClient || !this.mcpClient.isBackendConnected()) {
      return { success: false, error: 'Database not available' }
    }

    const result = await this.loadFromDatabase()
    if (result.success && result.settings) {
      this.settings = result.settings
      await this.saveToLocalStorage(this.settings)
      this.notifyListeners(this.settings)
      this.useDatabase = true
    }
    return result
  }

  /**
   * Get settings audit trail (admin only)
   */
  async getSettingsAudit(limit: number = 50, offset: number = 0) {
    if (!this.mcpClient) {
      return []
    }
    return await this.mcpClient.getSettingsAudit(this.userId, limit, offset)
  }

  /**
   * Notify all listeners of settings changes
   */
  private notifyListeners(settings: UserSettings): void {
    this.listeners.forEach(callback => {
      try {
        callback(settings)
      } catch (error) {
        mcpLogger.error('Settings listener error:', error)
      }
    })
  }
}

// Export singleton instance
export const settingsService = new SettingsService()
export default settingsService