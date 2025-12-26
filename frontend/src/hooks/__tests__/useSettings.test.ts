/**
 * useSettings Hook Tests
 * 
 * Unit tests for settings hook functionality including
 * initialization, updates, and subscription management.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useSettings, useSessionTimeout } from '../useSettings'
import { settingsService } from '@/services/settingsService'
import { DEFAULT_SETTINGS } from '@/types/settings'

// Mock settings service
vi.mock('@/services/settingsService', () => ({
  settingsService: {
    initialize: vi.fn(),
    updateSettings: vi.fn(),
    resetSettings: vi.fn(),
    getSessionTimeoutMs: vi.fn(),
    subscribe: vi.fn()
  }
}))

const mockSettingsService = settingsService as any

describe('useSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('should initialize settings on mount', async () => {
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      
      const { result } = renderHook(() => useSettings())
      
      expect(result.current.isLoading).toBe(true)
      expect(mockSettingsService.initialize).toHaveBeenCalledOnce()
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
      
      expect(result.current.settings).toEqual(DEFAULT_SETTINGS)
      expect(result.current.error).toBeNull()
    })

    it('should handle initialization errors', async () => {
      const error = new Error('Failed to initialize')
      mockSettingsService.initialize.mockRejectedValue(error)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
      
      expect(result.current.error).toBe('Failed to initialize')
      expect(result.current.settings).toBeNull()
    })

    it('should subscribe to settings changes', async () => {
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      const unsubscribe = vi.fn()
      mockSettingsService.subscribe.mockReturnValue(unsubscribe)
      
      const { unmount } = renderHook(() => useSettings())
      
      expect(mockSettingsService.subscribe).toHaveBeenCalledWith(
        expect.any(Function)
      )
      
      unmount()
      expect(unsubscribe).toHaveBeenCalled()
    })
  })

  describe('updateSettings', () => {
    it('should call service updateSettings', async () => {
      const updatedSettings = {
        ...DEFAULT_SETTINGS,
        ui: { ...DEFAULT_SETTINGS.ui, theme: 'light' as const }
      }
      
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      mockSettingsService.updateSettings.mockResolvedValue({
        success: true,
        settings: updatedSettings
      })
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.settings).toBeDefined()
      })
      
      let updateResult: any
      await act(async () => {
        updateResult = await result.current.updateSettings('ui', { theme: 'light' })
      })
      
      expect(mockSettingsService.updateSettings).toHaveBeenCalledWith(
        'ui',
        { theme: 'light' }
      )
      expect(updateResult.success).toBe(true)
    })

    it('should handle update errors', async () => {
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      mockSettingsService.updateSettings.mockResolvedValue({
        success: false,
        error: 'Update failed'
      })
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.settings).toBeDefined()
      })
      
      let updateResult: any
      await act(async () => {
        updateResult = await result.current.updateSettings('ui', { theme: 'light' })
      })
      
      expect(updateResult.success).toBe(false)
      expect(result.current.error).toBe('Update failed')
    })
  })

  describe('resetSettings', () => {
    it('should call service resetSettings', async () => {
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      mockSettingsService.resetSettings.mockResolvedValue({
        success: true,
        settings: DEFAULT_SETTINGS
      })
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.settings).toBeDefined()
      })
      
      let resetResult: any
      await act(async () => {
        resetResult = await result.current.resetSettings()
      })
      
      expect(mockSettingsService.resetSettings).toHaveBeenCalled()
      expect(resetResult.success).toBe(true)
    })
  })

  describe('getSessionTimeoutMs', () => {
    it('should return session timeout in milliseconds', async () => {
      mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
      mockSettingsService.subscribe.mockReturnValue(() => {})
      mockSettingsService.getSessionTimeoutMs.mockReturnValue(3600000)
      
      const { result } = renderHook(() => useSettings())
      
      await waitFor(() => {
        expect(result.current.settings).toBeDefined()
      })
      
      const timeoutMs = result.current.getSessionTimeoutMs()
      
      expect(timeoutMs).toBe(3600000)
      expect(mockSettingsService.getSessionTimeoutMs).toHaveBeenCalled()
    })
  })
})

describe('useSessionTimeout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should provide session timeout specific functionality', async () => {
    mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
    mockSettingsService.subscribe.mockReturnValue(() => {})
    mockSettingsService.getSessionTimeoutMs.mockReturnValue(3600000)
    mockSettingsService.updateSettings.mockResolvedValue({
      success: true,
      settings: DEFAULT_SETTINGS
    })
    
    const { result } = renderHook(() => useSessionTimeout())
    
    await waitFor(() => {
      expect(result.current.timeout).toBeDefined()
    })
    
    expect(result.current.timeout).toBe('1h')
    expect(result.current.timeoutMs).toBe(3600000)
    expect(result.current.idleDetection).toBe(true)
    expect(result.current.showWarningMinutes).toBe(5)
    expect(result.current.extendOnActivity).toBe(true)
  })

  it('should update session timeout', async () => {
    mockSettingsService.initialize.mockResolvedValue(DEFAULT_SETTINGS)
    mockSettingsService.subscribe.mockReturnValue(() => {})
    mockSettingsService.updateSettings.mockResolvedValue({
      success: true,
      settings: DEFAULT_SETTINGS
    })
    
    const { result } = renderHook(() => useSessionTimeout())
    
    await waitFor(() => {
      expect(result.current.timeout).toBeDefined()
    })
    
    await act(async () => {
      await result.current.updateTimeout('4h')
    })
    
    expect(mockSettingsService.updateSettings).toHaveBeenCalledWith(
      'security',
      {
        session: {
          ...DEFAULT_SETTINGS.security.session,
          timeout: '4h'
        }
      }
    )
  })
})