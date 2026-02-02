/**
 * Settings MCP Client Tests
 *
 * Comprehensive tests for the SettingsMcpClient including
 * MCP communication, error handling, and type safety.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SettingsMcpClient } from '../settingsMcpClient'

// Mock MCP client interface matching MCPProvider's client type
interface MockMcpClient {
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<{ success: boolean; data?: T; error?: string }>
}

// Mock the MCP provider (not needed here - no vi.mock() call)
const mockMcpClient: MockMcpClient = {
  callTool: vi.fn()
}

const mockIsConnected = vi.fn()

describe('SettingsMcpClient', () => {
  let client: SettingsMcpClient

  beforeEach(() => {
    client = new SettingsMcpClient(mockMcpClient as ReturnType<typeof import('@/providers/MCPProvider').useMCP>['client'], mockIsConnected)
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Constructor and Initialization', () => {
    it('should initialize with MCP client and connection checker', () => {
      expect(client).toBeInstanceOf(SettingsMcpClient)
    })

    it('should check backend connectivity', () => {
      mockIsConnected.mockReturnValue(true)
      expect(client.isBackendConnected()).toBe(true)

      mockIsConnected.mockReturnValue(false)
      expect(client.isBackendConnected()).toBe(false)
    })
  })

  describe('Settings Retrieval', () => {
    it('should get settings successfully', async () => {
      const mockSettings = {
        'ui.theme': 'dark',
        'ui.language': 'en',
        'system.timeout': 30
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: mockSettings
      })

      const result = await client.getSettings()

      expect(result.success).toBe(true)
      expect(result.settings).toEqual(mockSettings)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_settings',
        expect.objectContaining({
          user_id: 'default'
        })
      )
    })

    it('should get settings with user ID', async () => {
      const mockSettings = {
        'ui.theme': 'dark'
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: mockSettings
      })

      const result = await client.getSettings('user_123')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_settings',
        expect.objectContaining({
          user_id: 'user_123'
        })
      )
    })

    it('should handle backend error responses', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'AUTHENTICATION_REQUIRED'
      })

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('AUTHENTICATION_REQUIRED')
    })

    it('should handle MCP call errors during get', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue(new Error('MCP call failed'))

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP call failed')
    })
  })

  describe('Settings Updates', () => {
    const testSettings: Partial<import('@/types/settings').UserSettings> = {
      ui: {
        theme: 'dark',
        language: 'en',
        timezone: 'UTC',
        notifications: true,
        compactMode: false,
        sidebarCollapsed: false
      }
    }

    it('should update settings successfully', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: testSettings
      })

      const result = await client.updateSettings('default', testSettings)

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'update_settings',
        expect.objectContaining({
          user_id: 'default',
          settings: testSettings,
          validate_only: false
        })
      )
    })

    it('should validate only when requested', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { is_valid: true }
      })

      const settingsToValidate: Partial<import('@/types/settings').UserSettings> = {
        ui: { theme: 'dark', language: 'en', timezone: 'UTC', notifications: true, compactMode: false, sidebarCollapsed: false }
      }
      await client.updateSettings('default', settingsToValidate, { validateOnly: true })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'update_settings',
        expect.objectContaining({
          validate_only: true
        })
      )
    })

    it('should handle update errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'VALIDATION_ERROR'
      })

      const settingsWithError: Partial<import('@/types/settings').UserSettings> = {
        ui: { theme: 'dark', language: 'en', timezone: 'UTC', notifications: true, compactMode: false, sidebarCollapsed: false }
      }
      const result = await client.updateSettings('default', settingsWithError)

      expect(result.success).toBe(false)
      expect(result.error).toBe('VALIDATION_ERROR')
    })
  })

  describe('Settings Validation', () => {
    it('should validate settings successfully', async () => {
      const validationResult = {
        isValid: true,
        errors: [],
        warnings: []
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: validationResult
      })

      const result = await client.validateSettings({
        ui: { theme: 'dark' }
      } as never)

      expect(result.isValid).toBe(true)
      expect(result.errors).toEqual([])
    })

    it('should return validation errors', async () => {
      const validationResult = {
        isValid: false,
        errors: ['Invalid theme value'],
        warnings: ['Theme may not be supported']
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: validationResult
      })

      const result = await client.validateSettings({
        ui: { theme: 'invalid' }
      } as never)

      expect(result.isValid).toBe(false)
      expect(result.errors).toContain('Invalid theme value')
    })

    it('should handle validation service errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Validation service error'
      })

      const result = await client.validateSettings({} as never)

      expect(result.isValid).toBe(false)
      expect(result.errors).toContain('Validation service error')
    })
  })

  describe('Schema Operations', () => {
    it('should get settings schema successfully', async () => {
      const mockSchema = {
        schema: {
          'ui.theme': {
            type: 'string',
            enum: ['light', 'dark']
          }
        },
        constraints: {}
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: mockSchema
      })

      const result = await client.getSettingsSchema()

      expect(result).toBeDefined()
      expect(result?.schema).toEqual(mockSchema.schema)
    })

    it('should handle schema retrieval errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Schema service error'
      })

      const result = await client.getSettingsSchema()

      expect(result).toBeNull()
    })
  })

  describe('Reset User Settings', () => {
    it('should reset user settings successfully', async () => {
      // First call for reset, second for fetching updated settings
      vi.mocked(mockMcpClient.callTool)
        .mockResolvedValueOnce({
          success: true,
          data: { deleted_count: 5, user_id: 'default' }
        })
        .mockResolvedValueOnce({
          success: true,
          data: { 'ui.theme': 'dark' }
        })

      const result = await client.resetUserSettings('default')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'reset_user_settings',
        expect.objectContaining({
          user_id: 'default'
        })
      )
    })

    it('should reset user settings with category', async () => {
      vi.mocked(mockMcpClient.callTool)
        .mockResolvedValueOnce({
          success: true,
          data: { deleted_count: 2, user_id: 'default' }
        })
        .mockResolvedValueOnce({
          success: true,
          data: { 'ui.theme': 'dark' }
        })

      const result = await client.resetUserSettings('default', 'ui')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'reset_user_settings',
        expect.objectContaining({
          user_id: 'default',
          category: 'ui'
        })
      )
    })

    it('should handle reset errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Reset failed'
      })

      const result = await client.resetUserSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Reset failed')
    })
  })

  describe('Reset System Settings', () => {
    it('should reset system settings successfully', async () => {
      vi.mocked(mockMcpClient.callTool)
        .mockResolvedValueOnce({
          success: true,
          data: { reset_count: 3 }
        })
        .mockResolvedValueOnce({
          success: true,
          data: { 'ui.theme': 'dark' }
        })

      const result = await client.resetSystemSettings('admin')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'reset_system_settings',
        expect.objectContaining({
          user_id: 'admin'
        })
      )
    })

    it('should handle admin required error', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Admin privileges required'
      })

      const result = await client.resetSystemSettings('regular_user')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Admin privileges required')
    })

    it('should reset system settings with category', async () => {
      vi.mocked(mockMcpClient.callTool)
        .mockResolvedValueOnce({
          success: true,
          data: { reset_count: 1 }
        })
        .mockResolvedValueOnce({
          success: true,
          data: {}
        })

      const result = await client.resetSystemSettings('admin', 'security')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'reset_system_settings',
        expect.objectContaining({
          user_id: 'admin',
          category: 'security'
        })
      )
    })
  })

  describe('Get Default Settings', () => {
    it('should get default settings successfully', async () => {
      const mockDefaults = {
        defaults: {
          'ui.theme': { value: 'dark', category: 'ui', data_type: 'string' },
          'ui.language': { value: 'en', category: 'ui', data_type: 'string' }
        }
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: mockDefaults
      })

      const result = await client.getDefaultSettings()

      expect(result.success).toBe(true)
      expect(result.defaults).toEqual(mockDefaults.defaults)
    })

    it('should get default settings with category filter', async () => {
      const mockDefaults = {
        defaults: {
          'security.timeout': { value: 3600, category: 'security', data_type: 'number' }
        }
      }

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: mockDefaults
      })

      const result = await client.getDefaultSettings('security')

      expect(result.success).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_default_settings',
        expect.objectContaining({
          category: 'security'
        })
      )
    })

    it('should handle get defaults errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Failed to get defaults'
      })

      const result = await client.getDefaultSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Failed to get defaults')
    })
  })

  describe('Database Initialization', () => {
    it('should initialize database successfully', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { success: true }
      })

      const result = await client.initializeDatabase()

      expect(result).toBe(true)
      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'initialize_settings_database',
        {}
      )
    })

    it('should handle initialization failure', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Database initialization failed'
      })

      const result = await client.initializeDatabase()

      expect(result).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should handle MCP exceptions gracefully', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue(new Error('Connection lost'))

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Connection lost')
    })

    it('should handle unknown errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue('string error')

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Unknown error')
    })
  })
})
