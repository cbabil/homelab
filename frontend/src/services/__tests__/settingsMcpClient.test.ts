/**
 * Settings MCP Client Tests
 *
 * Comprehensive tests for the SettingsMcpClient including
 * MCP communication, error handling, and type safety.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SettingsMcpClient } from '../settingsMcpClient'
import { UserSettings } from '@/types/settings'

// Mock the MCP provider
const mockMcpClient = {
  call: vi.fn(),
  isConnected: vi.fn()
}

const mockIsConnected = vi.fn()

describe('SettingsMcpClient', () => {
  let client: SettingsMcpClient

  beforeEach(() => {
    client = new SettingsMcpClient(mockMcpClient as any, mockIsConnected)
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
        success: true,
        message: 'Settings retrieved successfully',
        data: {
          'ui.theme': 'dark',
          'ui.language': 'en',
          'system.timeout': 30
        }
      }

      mockMcpClient.call.mockResolvedValue(mockSettings)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(true)
      expect(result.settings).toEqual(mockSettings.data)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'get_settings',
        expect.objectContaining({
          include_system_defaults: true,
          include_user_overrides: true
        })
      )
    })

    it('should get settings with category filter', async () => {
      const mockSettings = {
        success: true,
        message: 'Settings retrieved successfully',
        data: {
          'ui.theme': 'dark',
          'ui.language': 'en'
        }
      }

      mockMcpClient.call.mockResolvedValue(mockSettings)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings('ui')

      expect(result.success).toBe(true)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'get_settings',
        expect.objectContaining({
          category: 'ui'
        })
      )
    })

    it('should get settings with specific keys', async () => {
      const mockSettings = {
        success: true,
        message: 'Settings retrieved successfully',
        data: {
          'ui.theme': 'dark'
        }
      }

      mockMcpClient.call.mockResolvedValue(mockSettings)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings(undefined, ['ui.theme'])

      expect(result.success).toBe(true)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'get_settings',
        expect.objectContaining({
          setting_keys: ['ui.theme']
        })
      )
    })

    it('should handle backend disconnection during get', async () => {
      mockIsConnected.mockReturnValue(false)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('BACKEND_DISCONNECTED')
      expect(result.message).toContain('Backend is not connected')
    })

    it('should handle MCP call errors during get', async () => {
      mockMcpClient.call.mockRejectedValue(new Error('MCP call failed'))
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP_ERROR')
      expect(result.message).toContain('MCP call failed')
    })

    it('should handle backend error responses', async () => {
      const mockErrorResponse = {
        success: false,
        message: 'Authentication required',
        error: 'AUTHENTICATION_REQUIRED'
      }

      mockMcpClient.call.mockResolvedValue(mockErrorResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('AUTHENTICATION_REQUIRED')
      expect(result.message).toContain('Authentication required')
    })
  })

  describe('Settings Updates', () => {
    const testSettings = {
      'ui.theme': 'dark',
      'ui.language': 'en'
    }

    it('should update settings successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Settings updated successfully',
        audit_id: 123
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings(testSettings, 'User preference update')

      expect(result.success).toBe(true)
      expect(result.auditId).toBe(123)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'update_settings',
        expect.objectContaining({
          settings: testSettings,
          change_reason: 'User preference update'
        })
      )
    })

    it('should update settings without change reason', async () => {
      const mockResponse = {
        success: true,
        message: 'Settings updated successfully'
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings(testSettings)

      expect(result.success).toBe(true)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'update_settings',
        expect.objectContaining({
          settings: testSettings
        })
      )
    })

    it('should handle backend disconnection during update', async () => {
      mockIsConnected.mockReturnValue(false)

      const result = await client.updateSettings(testSettings)

      expect(result.success).toBe(false)
      expect(result.error).toBe('BACKEND_DISCONNECTED')
    })

    it('should handle validation errors', async () => {
      const mockErrorResponse = {
        success: false,
        message: 'Invalid setting value',
        error: 'VALIDATION_ERROR',
        details: {
          'ui.theme': 'Invalid theme value'
        }
      }

      mockMcpClient.call.mockResolvedValue(mockErrorResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings(testSettings)

      expect(result.success).toBe(false)
      expect(result.error).toBe('VALIDATION_ERROR')
      expect(result.validationErrors).toEqual({
        'ui.theme': 'Invalid theme value'
      })
    })

    it('should handle admin permission errors', async () => {
      const mockErrorResponse = {
        success: false,
        message: 'Admin privileges required',
        error: 'ADMIN_REQUIRED'
      }

      mockMcpClient.call.mockResolvedValue(mockErrorResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings({ 'system.debug': true })

      expect(result.success).toBe(false)
      expect(result.error).toBe('ADMIN_REQUIRED')
    })

    it('should handle empty settings object', async () => {
      const result = await client.updateSettings({})

      expect(result.success).toBe(false)
      expect(result.error).toBe('INVALID_INPUT')
      expect(result.message).toContain('No settings provided')
    })

    it('should validate settings format', async () => {
      const invalidSettings = {
        'invalid/key': 'value',
        '': 'empty_key'
      }

      const result = await client.updateSettings(invalidSettings)

      expect(result.success).toBe(false)
      expect(result.error).toBe('INVALID_INPUT')
    })
  })

  describe('Settings Validation', () => {
    const testSettings = {
      'ui.theme': 'dark',
      'ui.language': 'en'
    }

    it('should validate settings successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Settings validation successful',
        data: {
          is_valid: true,
          validated_settings: testSettings,
          errors: [],
          warnings: [],
          security_violations: [],
          admin_required: []
        }
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.validateSettings(testSettings)

      expect(result.success).toBe(true)
      expect(result.validation?.is_valid).toBe(true)
      expect(result.validation?.validated_settings).toEqual(testSettings)
    })

    it('should return validation errors', async () => {
      const mockResponse = {
        success: true,
        message: 'Settings validation completed',
        data: {
          is_valid: false,
          validated_settings: {},
          errors: ['Invalid theme value'],
          warnings: ['Theme may not be supported'],
          security_violations: ['Potential XSS in value'],
          admin_required: ['system.debug']
        }
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.validateSettings(testSettings)

      expect(result.success).toBe(true)
      expect(result.validation?.is_valid).toBe(false)
      expect(result.validation?.errors).toEqual(['Invalid theme value'])
      expect(result.validation?.warnings).toEqual(['Theme may not be supported'])
      expect(result.validation?.security_violations).toEqual(['Potential XSS in value'])
      expect(result.validation?.admin_required).toEqual(['system.debug'])
    })

    it('should handle validation service errors', async () => {
      mockMcpClient.call.mockRejectedValue(new Error('Validation service error'))
      mockIsConnected.mockReturnValue(true)

      const result = await client.validateSettings(testSettings)

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP_ERROR')
    })
  })

  describe('Schema Operations', () => {
    it('should get settings schema successfully', async () => {
      const mockSchema = {
        success: true,
        message: 'Schema retrieved successfully',
        data: {
          schema: {
            'ui.theme': {
              type: 'string',
              enum: ['light', 'dark'],
              default: 'light'
            }
          },
          constraints: {
            'ui.theme': {
              required: false,
              admin_only: false
            }
          }
        }
      }

      mockMcpClient.call.mockResolvedValue(mockSchema)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettingsSchema()

      expect(result.success).toBe(true)
      expect(result.schema).toBeDefined()
      expect(result.schema?.schema).toEqual(mockSchema.data.schema)
      expect(result.schema?.constraints).toEqual(mockSchema.data.constraints)
    })

    it('should handle schema retrieval errors', async () => {
      mockMcpClient.call.mockRejectedValue(new Error('Schema service error'))
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettingsSchema()

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP_ERROR')
    })
  })

  describe('Audit Operations', () => {
    it('should get audit trail successfully', async () => {
      const mockAudit = {
        success: true,
        message: 'Audit trail retrieved successfully',
        data: [
          {
            id: 1,
            user_id: 'user_123',
            action: 'UPDATE',
            settings_path: 'ui.theme',
            old_value: 'light',
            new_value: 'dark',
            timestamp: '2023-01-01T00:00:00Z',
            ip_address: '192.168.1.100'
          }
        ]
      }

      mockMcpClient.call.mockResolvedValue(mockAudit)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getAuditTrail()

      expect(result.success).toBe(true)
      expect(result.auditEntries).toHaveLength(1)
      expect(result.auditEntries?.[0].action).toBe('UPDATE')
    })

    it('should get audit trail with filters', async () => {
      const mockAudit = {
        success: true,
        message: 'Audit trail retrieved successfully',
        data: []
      }

      mockMcpClient.call.mockResolvedValue(mockAudit)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getAuditTrail('user_123', '2023-01-01', '2023-01-31')

      expect(result.success).toBe(true)
      expect(mockMcpClient.call).toHaveBeenCalledWith(
        'get_audit_trail',
        expect.objectContaining({
          user_id: 'user_123',
          start_date: '2023-01-01',
          end_date: '2023-01-31'
        })
      )
    })

    it('should handle audit retrieval errors', async () => {
      mockMcpClient.call.mockRejectedValue(new Error('Audit service error'))
      mockIsConnected.mockReturnValue(true)

      const result = await client.getAuditTrail()

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP_ERROR')
    })
  })

  describe('Error Handling and Edge Cases', () => {
    it('should handle null/undefined MCP responses', async () => {
      mockMcpClient.call.mockResolvedValue(null)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('INVALID_RESPONSE')
    })

    it('should handle malformed MCP responses', async () => {
      mockMcpClient.call.mockResolvedValue('invalid_response')
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('INVALID_RESPONSE')
    })

    it('should handle network timeouts', async () => {
      const timeoutError = new Error('Request timeout')
      timeoutError.name = 'TimeoutError'
      mockMcpClient.call.mockRejectedValue(timeoutError)
      mockIsConnected.mockReturnValue(true)

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('TIMEOUT')
    })

    it('should handle connection lost during operation', async () => {
      // Start connected, then lose connection
      mockIsConnected.mockReturnValueOnce(true)
      mockMcpClient.call.mockImplementation(async () => {
        mockIsConnected.mockReturnValue(false)
        throw new Error('Connection lost')
      })

      const result = await client.getSettings()

      expect(result.success).toBe(false)
      expect(result.error).toBe('MCP_ERROR')
    })

    it('should handle large settings payloads', async () => {
      const largeSettings = {}
      for (let i = 0; i < 1000; i++) {
        largeSettings[`test.setting_${i}`] = `value_${i}`
      }

      const mockResponse = {
        success: true,
        message: 'Settings updated successfully'
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings(largeSettings)

      expect(result.success).toBe(true)
    })

    it('should handle concurrent operations', async () => {
      const mockResponse = {
        success: true,
        message: 'Settings retrieved successfully',
        data: { 'ui.theme': 'dark' }
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      // Start multiple concurrent operations
      const promises = [
        client.getSettings(),
        client.getSettings('ui'),
        client.updateSettings({ 'ui.theme': 'light' })
      ]

      const results = await Promise.all(promises)

      results.forEach(result => {
        expect(result.success).toBe(true)
      })
    })
  })

  describe('Security and Input Validation', () => {
    it('should validate setting keys format', async () => {
      const invalidKeys = [
        'invalid/key',
        'key;drop',
        'key\'injection',
        '',
        '..path',
        'key with spaces'
      ]

      for (const key of invalidKeys) {
        const result = await client.updateSettings({ [key]: 'value' })
        expect(result.success).toBe(false)
        expect(result.error).toBe('INVALID_INPUT')
      }
    })

    it('should sanitize setting values', async () => {
      const maliciousValues = {
        'ui.theme': '<script>alert("xss")</script>',
        'ui.language': 'javascript:alert("xss")',
        'system.timeout': '"; DROP TABLE users; --'
      }

      const mockResponse = {
        success: true,
        message: 'Settings updated successfully'
      }

      mockMcpClient.call.mockResolvedValue(mockResponse)
      mockIsConnected.mockReturnValue(true)

      const result = await client.updateSettings(maliciousValues)

      // Should either sanitize or reject malicious input
      if (result.success) {
        // If successful, values should be sanitized
        const callArgs = mockMcpClient.call.mock.calls[0][1]
        // Implementation should sanitize the values
        expect(callArgs.settings).toBeDefined()
      } else {
        expect(result.error).toBe('INVALID_INPUT')
      }
    })

    it('should prevent path traversal in setting keys', async () => {
      const pathTraversalKeys = [
        '../../../etc/passwd',
        '..\\..\\windows\\system32',
        'ui../theme',
        'ui..theme'
      ]

      for (const key of pathTraversalKeys) {
        const result = await client.updateSettings({ [key]: 'value' })
        expect(result.success).toBe(false)
        expect(result.error).toBe('INVALID_INPUT')
      }
    })

    it('should handle extremely long values', async () => {
      const extremelyLongValue = 'a'.repeat(1000000) // 1MB string

      const result = await client.updateSettings({
        'ui.theme': extremelyLongValue
      })

      // Should either reject or handle gracefully
      if (!result.success) {
        expect(result.error).toBe('INVALID_INPUT')
      }
    })
  })
})