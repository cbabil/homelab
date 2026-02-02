/**
 * Unit tests for Settings State Hook
 *
 * Tests state initialization, localStorage persistence, and MCP config management.
 * Covers localStorage loading, saving, and error handling.
 */

import { describe, it, expect, beforeEach, vi, afterAll } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSettingsState } from './useSettingsState'

// Mock MCP provider
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    isConnected: false,
    error: null
  })
}))

// Mock settings context - track updateSettings calls
const mockUpdateSettings = vi.fn().mockResolvedValue({ success: true })

vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: {
      notifications: { serverAlerts: true, resourceAlerts: true, updateAlerts: false },
      servers: { connectionTimeout: 30, retryCount: 3, autoRetry: true }
    },
    updateSettings: mockUpdateSettings
  })
}))

// Mock the SettingsSavingContext
vi.mock('./SettingsSavingContext', () => ({
  useSettingsSaving: () => ({
    isSaving: false,
    setIsSaving: vi.fn()
  })
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

// Mock console.warn to avoid noise in tests
const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

describe('useSettingsState', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterAll(() => {
    consoleSpy.mockRestore()
  })

  describe('initialization', () => {
    it('should initialize with default values', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      
      const { result } = renderHook(() => useSettingsState())

      expect(result.current.activeTab).toBe('general')
      expect(result.current.activeServerTab).toBe('ssh')
      expect(result.current.serverAlerts).toBe(true)
      expect(result.current.resourceAlerts).toBe(true)
      expect(result.current.updateAlerts).toBe(false)
      expect(result.current.autoRetry).toBe(true)
      expect(result.current.connectionTimeout).toBe('30')
      expect(result.current.retryCount).toBe('3')
      expect(result.current.isEditingMcpConfig).toBe(false)
      expect(result.current.mcpConfigText).toBe('')
      expect(result.current.originalMcpConfig).toBe('')
      expect(result.current.mcpConfigError).toBe('')
      expect(result.current.mcpConnectionStatus).toBe('disconnected')
      expect(result.current.mcpConnectionError).toBe('')
      expect(result.current.sortBy).toBe('lastActivity')
      expect(result.current.sortOrder).toBe('desc')
    })

    it('should load MCP config from localStorage', () => {
      const savedConfig = {
        mcpServers: {
          'tomo': {
            type: 'http',
            url: 'http://localhost:9000',
            name: 'Custom Assistant'
          }
        }
      }
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(savedConfig))
      
      const { result } = renderHook(() => useSettingsState())

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('tomo-mcp-config')
      expect(result.current.mcpConfig).toEqual(savedConfig)
    })

    it('should use default config when localStorage is empty', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      const { result } = renderHook(() => useSettingsState())

      expect(result.current.mcpConfig).toEqual({
        mcpServers: {
          'tomo': {
            type: 'http',
            url: '/mcp',
            name: 'Tomo',
            description: 'Local tomo management MCP server'
          }
        }
      })
    })

    it('should handle corrupted localStorage data', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json}')

      const { result } = renderHook(() => useSettingsState())

      expect(console.warn).toHaveBeenCalledWith(
        '[Settings] Failed to load MCP config from localStorage',
        expect.any(Error)
      )
      expect(result.current.mcpConfig).toEqual({
        mcpServers: {
          'tomo': {
            type: 'http',
            url: '/mcp',
            name: 'Tomo',
            description: 'Local tomo management MCP server'
          }
        }
      })
    })

    it('should have default session data', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      
      const { result } = renderHook(() => useSettingsState())

      expect(result.current.sessions).toHaveLength(2)
      expect(result.current.sessions[0].id).toBe('sess_****7a2f')
      expect(result.current.sessions[0].status).toBe('active')
      expect(result.current.sessions[1].id).toBe('sess_****9b4c')
      expect(result.current.sessions[1].status).toBe('idle')
    })
  })

  describe('MCP config persistence', () => {
    it('should save config to localStorage when setMcpConfig is called', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      
      const { result } = renderHook(() => useSettingsState())
      
      const newConfig = {
        mcpServers: {
          'new-server': {
            type: 'http',
            url: 'http://localhost:9000',
            name: 'New Server'
          }
        }
      }

      act(() => {
        result.current.setMcpConfig(newConfig)
      })

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'tomo-mcp-config',
        JSON.stringify(newConfig)
      )
      expect(result.current.mcpConfig).toEqual(newConfig)
    })

    it('should handle localStorage save errors gracefully', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const { result } = renderHook(() => useSettingsState())

      const newConfig = { mcpServers: { 'test': { url: 'test' } } }

      act(() => {
        result.current.setMcpConfig(newConfig)
      })

      expect(console.warn).toHaveBeenCalledWith(
        '[Settings] Failed to save MCP config to localStorage',
        expect.any(Error)
      )
      expect(result.current.mcpConfig).toEqual(newConfig)
    })
  })

  describe('state setters', () => {
    it('should update activeTab', () => {
      const { result } = renderHook(() => useSettingsState())
      
      act(() => {
        result.current.setActiveTab('servers')
      })

      expect(result.current.activeTab).toBe('servers')
    })

    it('should update MCP editing state', () => {
      const { result } = renderHook(() => useSettingsState())
      
      act(() => {
        result.current.setIsEditingMcpConfig(true)
        result.current.setMcpConfigText('{"test": "config"}')
        result.current.setOriginalMcpConfig('{"original": "config"}')
        result.current.setMcpConfigError('Test error')
      })

      expect(result.current.isEditingMcpConfig).toBe(true)
      expect(result.current.mcpConfigText).toBe('{"test": "config"}')
      expect(result.current.originalMcpConfig).toBe('{"original": "config"}')
      expect(result.current.mcpConfigError).toBe('Test error')
    })

    it('should update connection state', () => {
      const { result } = renderHook(() => useSettingsState())
      
      act(() => {
        result.current.setMcpConnectionStatus('connected')
        result.current.setMcpConnectionError('Connection error')
      })

      expect(result.current.mcpConnectionStatus).toBe('connected')
      expect(result.current.mcpConnectionError).toBe('Connection error')
    })

    it('should update sorting state', () => {
      const { result } = renderHook(() => useSettingsState())

      act(() => {
        result.current.setSortBy('userId')
        result.current.setSortOrder('asc')
      })

      expect(result.current.sortBy).toBe('userId')
      expect(result.current.sortOrder).toBe('asc')
    })

    it('should update session data', () => {
      const { result } = renderHook(() => useSettingsState())

      const newSessions = [
        {
          id: 'new-session',
          userId: 'user-1',
          username: 'testuser',
          status: 'active' as const,
          started: new Date(),
          lastActivity: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
          location: 'Test Location',
          ip: '127.0.0.1',
          isCurrent: false
        }
      ]

      act(() => {
        result.current.setSessions(newSessions)
      })

      expect(result.current.sessions).toEqual(newSessions)
    })

    it('should update alert settings', async () => {
      const { result } = renderHook(() => useSettingsState())

      await act(async () => {
        result.current.setServerAlerts(false)
        result.current.setResourceAlerts(false)
        result.current.setUpdateAlerts(true)
      })

      // Verify updateSettings was called with correct values
      expect(mockUpdateSettings).toHaveBeenCalledWith('notifications', { serverAlerts: false })
      expect(mockUpdateSettings).toHaveBeenCalledWith('notifications', { resourceAlerts: false })
      expect(mockUpdateSettings).toHaveBeenCalledWith('notifications', { updateAlerts: true })
    })

    it('should update connection settings', async () => {
      const { result } = renderHook(() => useSettingsState())

      await act(async () => {
        result.current.setAutoRetry(false)
        result.current.setConnectionTimeout('45')
        result.current.setRetryCount('5')
      })

      // Verify updateSettings was called with correct values
      expect(mockUpdateSettings).toHaveBeenCalledWith('servers', { autoRetry: false })
      expect(mockUpdateSettings).toHaveBeenCalledWith('servers', { connectionTimeout: 45 })
      expect(mockUpdateSettings).toHaveBeenCalledWith('servers', { retryCount: 5 })
    })

    it('should update server tab', () => {
      const { result } = renderHook(() => useSettingsState())
      
      act(() => {
        result.current.setActiveServerTab('docker')
      })

      expect(result.current.activeServerTab).toBe('docker')
    })
  })
})