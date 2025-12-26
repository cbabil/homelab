/**
 * useRetentionSettings Hook Tests
 *
 * Unit tests for the retention settings hook including:
 * - Settings initialization and state management
 * - Settings service integration
 * - Preview cleanup operations and validation
 * - Settings validation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useRetentionSettings } from '../useRetentionSettings'

// Mock settings service with proper structure
vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn().mockResolvedValue({
      system: {
        dataRetention: {
          logRetentionDays: 14,
          otherDataRetentionDays: 14,
          autoCleanupEnabled: false,
          lastCleanupDate: undefined
        }
      }
    }),
    getSettings: vi.fn().mockReturnValue({
      system: {
        dataRetention: {
          logRetentionDays: 14,
          otherDataRetentionDays: 14,
          autoCleanupEnabled: false,
          lastCleanupDate: undefined
        }
      }
    }),
    updateSettings: vi.fn().mockResolvedValue({
      success: true,
      settings: {
        system: {
          dataRetention: {
            logRetentionDays: 14,
            otherDataRetentionDays: 14,
            autoCleanupEnabled: false,
            lastCleanupDate: undefined
          }
        }
      }
    })
  }
}))

// Import the mocked service
import { settingsService } from '@/services/settingsService'
const mockSettingsService = vi.mocked(settingsService)

describe('useRetentionSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Reset settings service mock to default state
    mockSettingsService.initialize.mockResolvedValue({
      system: {
        dataRetention: {
          logRetentionDays: 14,
          otherDataRetentionDays: 14,
          autoCleanupEnabled: false,
          lastCleanupDate: undefined
        }
      }
    })

    mockSettingsService.getSettings.mockReturnValue({
      system: {
        dataRetention: {
          logRetentionDays: 14,
          otherDataRetentionDays: 14,
          autoCleanupEnabled: false,
          lastCleanupDate: undefined
        }
      }
    })

    mockSettingsService.updateSettings.mockResolvedValue({
      success: true,
      settings: {
        system: {
          dataRetention: {
            logRetentionDays: 14,
            otherDataRetentionDays: 14,
            autoCleanupEnabled: false,
            lastCleanupDate: undefined
          }
        }
      }
    })
  })

  describe('Settings Initialization', () => {
    it('should initialize with loading state', () => {
      const { result } = renderHook(() => useRetentionSettings())

      expect(result.current.isLoading).toBe(true)
      expect(result.current.settings).toBeNull()
      expect(result.current.error).toBeNull()
    })

    it('should load settings successfully', async () => {
      mockSettingsService.getSettings.mockReturnValue({
        system: {
          dataRetention: {
            logRetentionDays: 30,
            otherDataRetentionDays: 365,
            autoCleanupEnabled: false,
            lastCleanupDate: undefined
          }
        }
      })

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.settings).toEqual({
        logRetentionDays: 30,
        otherDataRetentionDays: 365,
        autoCleanupEnabled: false,
        lastCleanupDate: undefined
      })
      expect(result.current.error).toBeNull()
      expect(mockSettingsService.initialize).toHaveBeenCalled()
      expect(mockSettingsService.getSettings).toHaveBeenCalled()
    })

    it('should handle settings loading errors', async () => {
      // Mock initialize to reject
      mockSettingsService.initialize.mockRejectedValue(new Error('Failed to load settings'))

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.settings).toBeNull()
      expect(result.current.error).toBe('Failed to load settings')
    })
  })

  describe('Settings Updates', () => {
    beforeEach(() => {
      // Initialize with default settings
      mockSettingsService.getSettings.mockReturnValue({
        system: {
          dataRetention: {
            logRetentionDays: 30,
            otherDataRetentionDays: 365,
            autoCleanupEnabled: false,
            lastCleanupDate: undefined
          }
        }
      })
    })

    it('should update settings successfully', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Mock successful update
      mockSettingsService.updateSettings.mockResolvedValue({
        success: true,
        settings: {
          system: {
            dataRetention: {
              logRetentionDays: 60,
              otherDataRetentionDays: 365,
              autoCleanupEnabled: false,
              lastCleanupDate: undefined
            }
          }
        }
      })

      await act(async () => {
        await result.current.updateRetentionSettings({ logRetentionDays: 60 })
      })

      expect(mockSettingsService.updateSettings).toHaveBeenCalledWith('system', {
        dataRetention: {
          logRetentionDays: 60,
          otherDataRetentionDays: 365,
          autoCleanupEnabled: false,
          lastCleanupDate: undefined
        }
      })

      expect(result.current.settings?.logRetentionDays).toBe(60)
    })

    it('should handle update failures', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      mockSettingsService.updateSettings.mockResolvedValue({
        success: false,
        error: 'Update failed'
      })

      await act(async () => {
        await result.current.updateRetentionSettings({ logRetentionDays: 60 })
      })

      expect(result.current.error).toBe('Update failed')
    })

    it('should validate settings before update', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Try to update with invalid values (below minimum)
      await act(async () => {
        await result.current.updateRetentionSettings({ logRetentionDays: 5 })
      })

      // Should not call update service with invalid values
      expect(mockSettingsService.updateSettings).not.toHaveBeenCalled()
    })
  })

  describe('Preview Cleanup Operations', () => {
    beforeEach(() => {
      // Initialize with settings
      mockSettingsService.getSettings.mockReturnValue({
        system: {
          dataRetention: {
            logRetentionDays: 30,
            otherDataRetentionDays: 365,
            autoCleanupEnabled: false,
            lastCleanupDate: undefined
          }
        }
      })
    })

    it('should preview cleanup successfully', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let previewResult
      await act(async () => {
        previewResult = await result.current.previewCleanup()
      })

      expect(previewResult.success).toBe(true)
      expect(result.current.previewResult).toBeDefined()
      expect(result.current.previewResult?.logEntriesAffected).toBeGreaterThanOrEqual(0)
      expect(result.current.previewResult?.otherDataAffected).toBeGreaterThanOrEqual(0)
    })

    it('should handle preview when settings not loaded', async () => {
      mockSettingsService.getSettings.mockReturnValue(null)

      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let previewResult
      await act(async () => {
        previewResult = await result.current.previewCleanup()
      })

      expect(previewResult.success).toBe(false)
      expect(previewResult.error).toBe('Settings not loaded')
    })
  })

  describe('Data Validation and Limits', () => {
    it('should provide correct validation limits', () => {
      const { result } = renderHook(() => useRetentionSettings())

      expect(result.current.limits).toEqual({
        LOG_MIN_DAYS: 14,
        LOG_MAX_DAYS: 365,
        OTHER_DATA_MIN_DAYS: 14,
        OTHER_DATA_MAX_DAYS: 365
      })
    })

    it('should validate settings against limits', async () => {
      const { result } = renderHook(() => useRetentionSettings())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test log retention validation
      let validation = result.current.validateRetentionSettings({
        logRetentionDays: 5,
        otherDataRetentionDays: 14,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(false)

      validation = result.current.validateRetentionSettings({
        logRetentionDays: 400,
        otherDataRetentionDays: 14,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(false)

      validation = result.current.validateRetentionSettings({
        logRetentionDays: 30,
        otherDataRetentionDays: 14,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(true)

      // Test other data retention validation
      validation = result.current.validateRetentionSettings({
        logRetentionDays: 14,
        otherDataRetentionDays: 5,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(false)

      validation = result.current.validateRetentionSettings({
        logRetentionDays: 14,
        otherDataRetentionDays: 400,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(false)

      validation = result.current.validateRetentionSettings({
        logRetentionDays: 14,
        otherDataRetentionDays: 365,
        autoCleanupEnabled: false
      })
      expect(validation.valid).toBe(true)
    })
  })
})