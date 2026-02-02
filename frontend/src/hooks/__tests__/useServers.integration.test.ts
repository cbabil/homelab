/**
 * useServers Hook Integration Tests
 *
 * Tests for server management hook with MCP backend integration.
 * Backend is single source of truth - no localStorage.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useServers } from '../useServers'

// Mock MCP Provider
const mockCallTool = vi.fn()
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: vi.fn(() => ({
    client: { callTool: mockCallTool },
    isConnected: true
  }))
}))

// Mock server info service
vi.mock('@/services/serverInfoService', () => ({
  serverInfoService: {
    fetchServerInfo: vi.fn(),
    setMCPClient: vi.fn()
  }
}))

import { serverInfoService } from '@/services/serverInfoService'
import { useMCP } from '@/providers/MCPProvider'
import { SystemInfo } from '@/types/server'

const mockUseMCP = vi.mocked(useMCP)

const mockBackendServer = {
  id: 'srv-123',
  name: 'Test Server',
  host: '192.168.1.100',
  port: 22,
  username: 'testuser',
  auth_type: 'password',
  status: 'disconnected'
}

const mockSystemInfo: SystemInfo = {
  os: 'Ubuntu 22.04',
  kernel: '5.15.0-91-generic',
  architecture: 'x86_64',
  docker_version: '24.0.7'
}

describe('useServers Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseMCP.mockReturnValue({
      client: { callTool: mockCallTool },
      isConnected: true
    } as any)

    // Default: list_servers returns one server
    mockCallTool.mockResolvedValue({
      data: {
        success: true,
        data: { servers: [mockBackendServer] }
      }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('server fetching', () => {
    it('should fetch servers from backend on mount', async () => {
      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      expect(mockCallTool).toHaveBeenCalledWith('list_servers', {})
      expect(result.current.servers[0].id).toBe('srv-123')
      expect(result.current.servers[0].name).toBe('Test Server')
    })

    it('should return empty array when not connected', async () => {
      mockUseMCP.mockReturnValue({
        client: { callTool: mockCallTool },
        isConnected: false
      } as any)

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.servers).toEqual([])
      expect(mockCallTool).not.toHaveBeenCalled()
    })

    it('should handle backend errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockCallTool.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.servers).toEqual([])
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('handleConnectServer', () => {
    it('should successfully connect and fetch server info', async () => {
      vi.mocked(serverInfoService.fetchServerInfo).mockResolvedValue({
        success: true,
        system_info: mockSystemInfo,
        message: 'Success'
      })

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      await act(async () => {
        await result.current.handleConnectServer('srv-123')
      })

      expect(serverInfoService.fetchServerInfo).toHaveBeenCalled()
    })

    it('should handle server info fetch failure gracefully', async () => {
      vi.mocked(serverInfoService.fetchServerInfo).mockResolvedValue({
        success: false,
        error: 'SSH connection failed',
        message: 'Failed to fetch'
      })

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      const connectionResult = await act(async () => {
        return await result.current.handleConnectServer('srv-123')
      })

      expect(connectionResult.success).toBe(false)
    })

    it('should handle complete connection failure', async () => {
      vi.mocked(serverInfoService.fetchServerInfo).mockRejectedValue(
        new Error('Network timeout')
      )

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      const connectionResult = await act(async () => {
        return await result.current.handleConnectServer('srv-123')
      })

      expect(connectionResult.success).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle nonexistent server gracefully', async () => {
      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      const connectionResult = await act(async () => {
        return await result.current.handleConnectServer('nonexistent-id')
      })

      expect(connectionResult.success).toBe(false)
    })
  })

  describe('server filtering', () => {
    it('should filter servers by name, host, and username', async () => {
      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(1)
      })

      act(() => {
        result.current.setSearchTerm('Test')
      })

      expect(result.current.filteredServers).toHaveLength(1)

      act(() => {
        result.current.setSearchTerm('NonexistentServer')
      })

      expect(result.current.filteredServers).toHaveLength(0)
    })
  })

  describe('server statistics', () => {
    it('should calculate health percentage correctly', async () => {
      mockCallTool.mockResolvedValue({
        data: {
          success: true,
          data: {
            servers: [
              { ...mockBackendServer, id: '1', status: 'connected' },
              { ...mockBackendServer, id: '2', status: 'disconnected' }
            ]
          }
        }
      })

      const { result } = renderHook(() => useServers())

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(2)
      })

      expect(result.current.connectedCount).toBe(1)
      expect(result.current.totalServers).toBe(2)
      expect(result.current.healthPercentage).toBe(50)
    })
  })
})
