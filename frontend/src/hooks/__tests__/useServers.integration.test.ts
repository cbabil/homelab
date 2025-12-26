/**
 * useServers Hook Integration Tests
 * 
 * Tests for server management hook including info fetching integration.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useServers } from '../useServers'

// Mock services
vi.mock('@/services/serverStorageService', () => ({
  serverStorageService: {
    getAllServers: vi.fn(() => []),
    getServerById: vi.fn(),
    addServer: vi.fn(),
    updateServer: vi.fn(),
    deleteServer: vi.fn(),
    updateServerStatus: vi.fn(),
    updateServerSystemInfo: vi.fn()
  }
}))

vi.mock('@/services/serverInfoService', () => ({
  serverInfoService: {
    fetchServerInfo: vi.fn()
  }
}))

import { serverStorageService } from '@/services/serverStorageService'
import { serverInfoService } from '@/services/serverInfoService'
import { ServerConnection, SystemInfo } from '@/types/server'

const mockServer: ServerConnection = {
  id: 'srv-123',
  name: 'Test Server',
  host: '192.168.1.100',
  port: 22,
  username: 'testuser',
  auth_type: 'password',
  status: 'disconnected',
  created_at: '2024-01-01T00:00:00Z'
}

const mockSystemInfo: SystemInfo = {
  os: 'Ubuntu 22.04',
  kernel: '5.15.0-91-generic',
  architecture: 'x86_64',
  uptime: '15 days, 8:32',
  docker_version: '24.0.7'
}

describe('useServers Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(serverStorageService.getAllServers).mockReturnValue([mockServer])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('handleConnectServer', () => {
    it('should successfully connect and fetch server info', async () => {
      vi.mocked(serverStorageService.getServerById).mockReturnValue(mockServer)
      vi.mocked(serverInfoService.fetchServerInfo).mockResolvedValue({
        success: true,
        system_info: mockSystemInfo,
        message: 'Success'
      })

      const { result } = renderHook(() => useServers())

      await act(async () => {
        await result.current.handleConnectServer('srv-123')
      })

      // Should call services in correct order
      expect(serverStorageService.updateServerStatus).toHaveBeenNthCalledWith(
        1,
        'srv-123',
        'preparing'
      )
      
      expect(serverInfoService.fetchServerInfo).toHaveBeenCalledWith(mockServer)
      
      expect(serverStorageService.updateServerSystemInfo).toHaveBeenCalledWith(
        'srv-123',
        mockSystemInfo
      )
      
      expect(serverStorageService.updateServerStatus).toHaveBeenNthCalledWith(
        2,
        'srv-123',
        'connected'
      )
    })

    it('should handle server info fetch failure gracefully', async () => {
      vi.mocked(serverStorageService.getServerById).mockReturnValue(mockServer)
      vi.mocked(serverInfoService.fetchServerInfo).mockResolvedValue({
        success: false,
        error: 'SSH connection failed',
        message: 'Failed to fetch'
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { result } = renderHook(() => useServers())

      await act(async () => {
        await result.current.handleConnectServer('srv-123')
      })

      // Should still mark as connected even if info fetch fails
      expect(serverStorageService.updateServerStatus).toHaveBeenLastCalledWith(
        'srv-123',
        'connected'
      )
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to fetch system info: SSH connection failed'
      )
      
      // Should not update system info
      expect(serverStorageService.updateServerSystemInfo).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('should handle complete connection failure', async () => {
      vi.mocked(serverStorageService.getServerById).mockReturnValue(mockServer)
      vi.mocked(serverInfoService.fetchServerInfo).mockRejectedValue(
        new Error('Network timeout')
      )

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const { result } = renderHook(() => useServers())

      await act(async () => {
        await result.current.handleConnectServer('srv-123')
      })

      // Should mark as error when connection fails completely
      expect(serverStorageService.updateServerStatus).toHaveBeenLastCalledWith(
        'srv-123',
        'error'
      )
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Server connection failed: Error: Network timeout'
      )

      consoleSpy.mockRestore()
    })

    it('should handle nonexistent server gracefully', async () => {
      vi.mocked(serverStorageService.getServerById).mockReturnValue(undefined)

      const { result } = renderHook(() => useServers())

      await act(async () => {
        await result.current.handleConnectServer('nonexistent-id')
      })

      // Should not call any other services
      expect(serverStorageService.updateServerStatus).not.toHaveBeenCalled()
      expect(serverInfoService.fetchServerInfo).not.toHaveBeenCalled()
    })

    it('should refresh server list after connection attempt', async () => {
      vi.mocked(serverStorageService.getServerById).mockReturnValue(mockServer)
      vi.mocked(serverInfoService.fetchServerInfo).mockResolvedValue({
        success: true,
        system_info: mockSystemInfo,
        message: 'Success'
      })

      const { result } = renderHook(() => useServers())

      await act(async () => {
        await result.current.handleConnectServer('srv-123')
      })

      // getAllServers should be called multiple times to refresh state
      expect(serverStorageService.getAllServers).toHaveBeenCalledTimes(3)
    })
  })

  describe('server filtering', () => {
    it('should filter servers by name, host, and username', () => {
      const serverWithInfo: ServerConnection = {
        ...mockServer,
        system_info: mockSystemInfo
      }

      vi.mocked(serverStorageService.getAllServers).mockReturnValue([serverWithInfo])

      const { result } = renderHook(() => useServers())

      act(() => {
        result.current.setSearchTerm('Test')
      })

      // Should find server by name
      expect(result.current.filteredServers).toHaveLength(1)
    })
  })

  describe('server statistics', () => {
    it('should calculate health percentage correctly with connected servers', () => {
      const connectedServer: ServerConnection = {
        ...mockServer,
        status: 'connected'
      }
      const disconnectedServer: ServerConnection = {
        ...mockServer,
        id: 'srv-456',
        status: 'disconnected'
      }

      vi.mocked(serverStorageService.getAllServers).mockReturnValue([
        connectedServer,
        disconnectedServer
      ])

      const { result } = renderHook(() => useServers())

      expect(result.current.connectedCount).toBe(1)
      expect(result.current.totalServers).toBe(2)
      expect(result.current.healthPercentage).toBe(50)
    })
  })
})