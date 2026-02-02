/**
 * Settings MCP Client
 *
 * MCP client for settings operations with database persistence.
 * Provides type-safe interface for backend settings management.
 */

import { useMCP } from '@/providers/MCPProvider'
import {
  UserSettings,
  SettingsValidation,
  SettingsUpdateResult
} from '@/types/settings'
import { mcpLogger } from '@/services/systemLogger'

// Backend settings operation types
export interface SettingsSchema {
  schema: Record<string, unknown>
  constraints: Record<string, unknown>
}

export interface SettingsOperationOptions {
  validateOnly?: boolean
  adminAuth?: boolean
}

/**
 * MCP-based Settings Client
 *
 * Handles all settings operations through the backend MCP tools
 * with proper error handling and type safety.
 */
export class SettingsMcpClient {
  private mcpClient: ReturnType<typeof useMCP>['client']
  private isConnected: () => boolean

  constructor(mcpClient: ReturnType<typeof useMCP>['client'], isConnected: () => boolean) {
    this.mcpClient = mcpClient
    this.isConnected = isConnected
    mcpLogger.info('Settings MCP Client initialized')
  }

  /**
   * Get user settings from database
   */
  async getSettings(userId: string = 'default'): Promise<SettingsUpdateResult> {
    try {
      mcpLogger.info('Getting settings from backend', { userId })

      const response = await this.mcpClient.callTool<UserSettings>('get_settings', {
        user_id: userId
      })

      if (!response.success) {
        mcpLogger.error('Failed to get settings', { error: response.error })
        return {
          success: false,
          error: response.error || 'Failed to retrieve settings'
        }
      }

      mcpLogger.info('Settings retrieved successfully', { userId })
      return {
        success: true,
        settings: response.data
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings retrieval failed', { error: errorMessage })
      return {
        success: false,
        error: errorMessage
      }
    }
  }

  /**
   * Update user settings in database
   */
  async updateSettings(
    userId: string = 'default',
    updates: Partial<UserSettings>,
    options: SettingsOperationOptions = {}
  ): Promise<SettingsUpdateResult> {
    try {
      mcpLogger.info('Updating settings in backend', { userId, updates: Object.keys(updates) })

      const response = await this.mcpClient.callTool<UserSettings>('update_settings', {
        user_id: userId,
        settings: updates,
        validate_only: options.validateOnly || false
      })

      if (!response.success) {
        mcpLogger.error('Failed to update settings', { error: response.error })
        return {
          success: false,
          error: response.error || 'Failed to update settings'
        }
      }

      mcpLogger.info('Settings updated successfully', { userId })
      return {
        success: true,
        settings: response.data
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings update failed', { error: errorMessage })
      return {
        success: false,
        error: errorMessage
      }
    }
  }

  /**
   * Validate settings without saving
   */
  async validateSettings(settings: UserSettings): Promise<SettingsValidation> {
    try {
      mcpLogger.info('Validating settings via backend')

      const response = await this.mcpClient.callTool<SettingsValidation>('validate_settings', {
        settings
      })

      if (!response.success) {
        mcpLogger.error('Settings validation failed', { error: response.error })
        return {
          isValid: false,
          errors: [response.error || 'Validation failed'],
          warnings: []
        }
      }

      mcpLogger.info('Settings validation completed', { isValid: response.data?.isValid })
      return response.data || {
        isValid: false,
        errors: ['Invalid validation response'],
        warnings: []
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings validation exception', { error: errorMessage })
      return {
        isValid: false,
        errors: [errorMessage],
        warnings: []
      }
    }
  }

  /**
   * Get settings schema for validation
   */
  async getSettingsSchema(): Promise<SettingsSchema | null> {
    try {
      mcpLogger.info('Getting settings schema from backend')

      const response = await this.mcpClient.callTool<SettingsSchema>('get_settings_schema', {})

      if (!response.success) {
        mcpLogger.error('Failed to get settings schema', { error: response.error })
        return null
      }

      mcpLogger.info('Settings schema retrieved successfully')
      return response.data || null
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings schema retrieval failed', { error: errorMessage })
      return null
    }
  }

  /**
   * Reset user settings to defaults by deleting user overrides
   */
  async resetUserSettings(userId: string = 'default', category?: string): Promise<SettingsUpdateResult> {
    try {
      mcpLogger.info('Resetting user settings via backend', { userId, category })

      const response = await this.mcpClient.callTool<{ deleted_count: number; user_id: string }>('reset_user_settings', {
        user_id: userId,
        category: category
      })

      if (!response.success) {
        mcpLogger.error('Failed to reset user settings', { error: response.error })
        return {
          success: false,
          error: response.error || 'Failed to reset settings'
        }
      }

      mcpLogger.info('User settings reset successfully', {
        userId,
        deletedCount: response.data?.deleted_count
      })

      // After reset, fetch the current settings (which will be system defaults)
      const settingsResponse = await this.getSettings(userId)

      return {
        success: true,
        settings: settingsResponse.settings
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Settings reset failed', { error: errorMessage })
      return {
        success: false,
        error: errorMessage
      }
    }
  }

  /**
   * Reset system settings to factory defaults (admin only)
   */
  async resetSystemSettings(userId: string = 'default', category?: string): Promise<SettingsUpdateResult> {
    try {
      mcpLogger.info('Resetting system settings to defaults via backend', { userId, category })

      const response = await this.mcpClient.callTool<{ reset_count: number }>('reset_system_settings', {
        user_id: userId,
        category: category
      })

      if (!response.success) {
        mcpLogger.error('Failed to reset system settings', { error: response.error })
        return {
          success: false,
          error: response.error || 'Failed to reset system settings'
        }
      }

      mcpLogger.info('System settings reset successfully', {
        userId,
        resetCount: response.data?.reset_count
      })

      // After reset, fetch the current settings
      const settingsResponse = await this.getSettings(userId)

      return {
        success: true,
        settings: settingsResponse.settings
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('System settings reset failed', { error: errorMessage })
      return {
        success: false,
        error: errorMessage
      }
    }
  }

  /**
   * Get factory default settings values
   */
  async getDefaultSettings(category?: string): Promise<{ success: boolean; defaults?: Record<string, unknown>; error?: string }> {
    try {
      mcpLogger.info('Getting default settings', { category })

      const response = await this.mcpClient.callTool<{ defaults: Record<string, unknown> }>('get_default_settings', {
        category: category
      })

      if (!response.success) {
        mcpLogger.error('Failed to get default settings', { error: response.error })
        return {
          success: false,
          error: response.error || 'Failed to get default settings'
        }
      }

      mcpLogger.info('Default settings retrieved successfully')
      return {
        success: true,
        defaults: response.data?.defaults
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Get default settings failed', { error: errorMessage })
      return {
        success: false,
        error: errorMessage
      }
    }
  }

  /**
   * Initialize settings database (admin only)
   */
  async initializeDatabase(): Promise<boolean> {
    try {
      mcpLogger.info('Initializing settings database')

      const response = await this.mcpClient.callTool<{ success: boolean }>('initialize_settings_database', {})

      if (!response.success) {
        mcpLogger.error('Failed to initialize database', { error: response.error })
        return false
      }

      mcpLogger.info('Settings database initialized successfully')
      return response.data?.success || false
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Database initialization failed', { error: errorMessage })
      return false
    }
  }

  /**
   * Check if the MCP client is connected
   */
  isBackendConnected(): boolean {
    return this.isConnected()
  }
}

/**
 * Hook to get Settings MCP Client
 */
export function useSettingsMcpClient(): SettingsMcpClient | null {
  try {
    const { client, isConnected } = useMCP()
    return new SettingsMcpClient(client, () => isConnected)
  } catch (_error) {
    // useMCP will throw if not within MCPProvider
    mcpLogger.warn('Settings MCP Client not available - no MCP provider')
    return null
  }
}