/**
 * Unit tests for Settings Handlers Hook
 * 
 * Tests MCP configuration save/load functionality with localStorage persistence.
 * Covers edit mode, validation, and connection handlers.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSettingsHandlers } from './useSettingsHandlers'
import { TomoMCPClient } from '@/services/mcpClient'

// Mock MCP client
vi.mock('@/services/mcpClient')

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

describe('useSettingsHandlers', () => {
  const mockProps = {
    mcpConfigText: '{"mcpServers":{"tomo":{"type":"http","url":"http://localhost:8000"}}}',
    setMcpConfig: vi.fn(),
    setMcpConfigError: vi.fn(),
    setIsEditingMcpConfig: vi.fn(),
    setOriginalMcpConfig: vi.fn(),
    setMcpConfigText: vi.fn(),
    setSortBy: vi.fn(),
    setSortOrder: vi.fn(),
    setSessions: vi.fn(),
    sortBy: 'lastActivity' as const,
    sortOrder: 'desc' as const,
    mcpConfig: { mcpServers: { 'tomo': { type: 'http' as const, url: 'http://localhost:8000' } } },
    originalMcpConfig: '',
    setMcpConnectionStatus: vi.fn(),
    setMcpConnectionError: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('handleSort', () => {
    it('should toggle sort order for same column', () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))
      
      act(() => {
        result.current.handleSort('lastActivity')
      })

      expect(mockProps.setSortOrder).toHaveBeenCalledWith('asc')
    })

    it('should set new column with ascending order', () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))

      act(() => {
        result.current.handleSort('userId')
      })

      expect(mockProps.setSortBy).toHaveBeenCalledWith('userId')
      expect(mockProps.setSortOrder).toHaveBeenCalledWith('asc')
    })
  })

  describe('handleTerminateSession', () => {
    it('should remove session from list', () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))
      
      act(() => {
        result.current.handleTerminateSession('session-1')
      })

      expect(mockProps.setSessions).toHaveBeenCalledWith(expect.any(Function))
    })
  })

  describe('handleRestoreSession', () => {
    it('should update session status to active', () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))
      
      act(() => {
        result.current.handleRestoreSession('session-1')
      })

      expect(mockProps.setSessions).toHaveBeenCalledWith(expect.any(Function))
    })
  })

  describe('MCP Config Edit Mode', () => {
    it('should enter edit mode with formatted config', () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))
      
      act(() => {
        result.current.handleMcpConfigEdit()
      })

      expect(mockProps.setMcpConfigText).toHaveBeenCalledWith(
        JSON.stringify(mockProps.mcpConfig, null, 2)
      )
      expect(mockProps.setOriginalMcpConfig).toHaveBeenCalledWith(
        JSON.stringify(mockProps.mcpConfig, null, 2)
      )
      expect(mockProps.setMcpConfigError).toHaveBeenCalledWith('')
      expect(mockProps.setIsEditingMcpConfig).toHaveBeenCalledWith(true)
    })

    it('should cancel edit mode and restore original config', () => {
      const originalConfig = '{"original":"config"}'
      const propsWithOriginal = { ...mockProps, originalMcpConfig: originalConfig }
      const { result } = renderHook(() => useSettingsHandlers(propsWithOriginal))
      
      act(() => {
        result.current.handleMcpConfigCancel()
      })

      expect(mockProps.setMcpConfigText).toHaveBeenCalledWith(originalConfig)
      expect(mockProps.setMcpConfigError).toHaveBeenCalledWith('')
      expect(mockProps.setIsEditingMcpConfig).toHaveBeenCalledWith(false)
      expect(mockProps.setOriginalMcpConfig).toHaveBeenCalledWith('')
    })
  })

  describe('MCP Config Save', () => {
    it('should save valid config successfully', () => {
      const validConfig = '{"mcpServers":{"test":{"type":"http","url":"http://test"}}}'
      const propsWithValidConfig = { ...mockProps, mcpConfigText: validConfig }
      const { result } = renderHook(() => useSettingsHandlers(propsWithValidConfig))

      act(() => {
        result.current.handleMcpConfigSave()
      })

      expect(mockProps.setMcpConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          mcpServers: expect.objectContaining({
            test: expect.objectContaining({
              type: 'http',
              url: 'http://test'
            })
          })
        })
      )
      expect(mockProps.setMcpConfigError).toHaveBeenCalledWith('')
      expect(mockProps.setIsEditingMcpConfig).toHaveBeenCalledWith(false)
      expect(mockProps.setOriginalMcpConfig).toHaveBeenCalledWith('')
    })

    it('should handle invalid JSON', () => {
      const invalidConfig = '{"invalid": json}'
      const propsWithInvalidConfig = { ...mockProps, mcpConfigText: invalidConfig }
      const { result } = renderHook(() => useSettingsHandlers(propsWithInvalidConfig))
      
      act(() => {
        result.current.handleMcpConfigSave()
      })

      expect(mockProps.setMcpConfigError).toHaveBeenCalledWith('Unexpected error parsing JSON')
      expect(mockProps.setMcpConfig).not.toHaveBeenCalled()
      expect(mockProps.setIsEditingMcpConfig).not.toHaveBeenCalledWith(false)
    })

    it('should handle validation errors', () => {
      const invalidConfig = '{}'
      const propsWithInvalidConfig = { ...mockProps, mcpConfigText: invalidConfig }
      const { result } = renderHook(() => useSettingsHandlers(propsWithInvalidConfig))
      
      act(() => {
        result.current.handleMcpConfigSave()
      })

      expect(mockProps.setMcpConfigError).toHaveBeenCalledWith(expect.stringContaining('mcpServers'))
      expect(mockProps.setMcpConfig).not.toHaveBeenCalled()
      expect(mockProps.setIsEditingMcpConfig).not.toHaveBeenCalledWith(false)
    })
  })

  describe('MCP Connection', () => {
    it('should connect successfully', async () => {
      const mockConnect = vi.fn().mockResolvedValue(undefined)
      vi.mocked(TomoMCPClient).mockImplementation(() => ({
        connect: mockConnect
      } as any))

      const { result } = renderHook(() => useSettingsHandlers(mockProps))

      await act(async () => {
        await result.current.handleMcpConnect()
      })

      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('connecting')
      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('connected')
      expect(mockProps.setMcpConnectionError).toHaveBeenCalledWith('')
    })

    it('should handle connection error', async () => {
      const mockConnect = vi.fn().mockRejectedValue(new Error('Connection failed'))
      vi.mocked(TomoMCPClient).mockImplementation(() => ({
        connect: mockConnect
      } as any))

      const { result } = renderHook(() => useSettingsHandlers(mockProps))

      await act(async () => {
        await result.current.handleMcpConnect()
      })

      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('connecting')
      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('error')
      expect(mockProps.setMcpConnectionError).toHaveBeenCalledWith('Connection failed')
    })

    it('should handle missing server URL', async () => {
      const propsWithoutUrl = {
        ...mockProps,
        mcpConfig: { mcpServers: { 'tomo': { type: 'http' as const } } } as const
      }
      const { result } = renderHook(() => useSettingsHandlers(propsWithoutUrl as any))

      await act(async () => {
        await result.current.handleMcpConnect()
      })

      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('connecting')
      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('error')
      expect(mockProps.setMcpConnectionError).toHaveBeenCalledWith('No MCP server URL configured')
    })

    it('should disconnect successfully', async () => {
      const { result } = renderHook(() => useSettingsHandlers(mockProps))
      
      await act(async () => {
        await result.current.handleMcpDisconnect()
      })

      expect(mockProps.setMcpConnectionStatus).toHaveBeenCalledWith('disconnected')
      expect(mockProps.setMcpConnectionError).toHaveBeenCalledWith('')
    })
  })
})