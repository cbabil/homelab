/**
 * useDeploymentModal Hook Tests
 *
 * Unit tests for the deployment modal state management hook.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDeploymentModal } from '../useDeploymentModal'
import { useMCP } from '@/providers/MCPProvider'
import { useToast } from '@/components/ui/Toast'
import { App, AppCategory } from '@/types/app'
import { Package } from 'lucide-react'

// Mock dependencies
vi.mock('@/providers/MCPProvider')
vi.mock('@/components/ui/Toast')
vi.mock('../useInstallationStatus', () => ({
  useInstallationStatus: () => ({
    statusData: null,
    isPolling: false,
    startPolling: vi.fn(),
    stopPolling: vi.fn(),
    reset: vi.fn()
  })
}))

const mockUseMCP = vi.mocked(useMCP)
const mockUseToast = vi.mocked(useToast)

const mockCategory: AppCategory = {
  id: 'media',
  name: 'Media',
  description: 'Media applications',
  icon: Package,
  color: 'red'
}

const mockApp: App = {
  id: 'plex',
  name: 'Plex',
  description: 'Media server',
  version: '1.0.0',
  category: mockCategory,
  tags: ['media', 'streaming'],
  icon: 'plex.png',
  author: 'Plex Inc',
  license: 'Proprietary',
  requirements: {
    minRam: '2GB',
    requiredPorts: [32400]
  },
  status: 'available',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z'
}

const mockServers = [
  {
    id: 'srv-1',
    name: 'Docker Server',
    host: '192.168.1.100',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'connected' as const,
    docker_installed: true,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'srv-2',
    name: 'No Docker Server',
    host: '192.168.1.101',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'connected' as const,
    docker_installed: false,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'srv-3',
    name: 'Offline Server',
    host: '192.168.1.102',
    port: 22,
    username: 'admin',
    auth_type: 'password' as const,
    status: 'disconnected' as const,
    docker_installed: true,
    created_at: '2024-01-01T00:00:00Z'
  }
]

describe('useDeploymentModal', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> }
  let mockAddToast: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockClient = { callTool: vi.fn() }
    mockAddToast = vi.fn()

    mockUseMCP.mockReturnValue({
      client: mockClient as unknown as ReturnType<typeof useMCP>['client'],
      isConnected: true,
      error: null
    })

    mockUseToast.mockReturnValue({ addToast: mockAddToast } as unknown as ReturnType<typeof useToast>)
  })

  describe('initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useDeploymentModal())

      expect(result.current.isOpen).toBe(false)
      expect(result.current.step).toBe('select')
      expect(result.current.selectedApp).toBeNull()
      expect(result.current.selectedServerIds).toEqual([])
      expect(result.current.config).toEqual({
        ports: {},
        volumes: {},
        env: {}
      })
      expect(result.current.isDeploying).toBe(false)
      expect(result.current.error).toBeNull()
      expect(result.current.deploymentResult).toBeNull()
    })
  })

  describe('openModal', () => {
    it('should open modal with selected app', () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.selectedApp).toEqual(mockApp)
      expect(result.current.step).toBe('select')
    })

    it('should reset state when opening with new app', () => {
      const { result } = renderHook(() => useDeploymentModal())

      // Set some state
      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
        result.current.setStep('deploying')
      })

      // Open with new app
      const newApp = { ...mockApp, id: 'jellyfin', name: 'Jellyfin' }
      act(() => {
        result.current.openModal(newApp)
      })

      expect(result.current.selectedApp).toEqual(newApp)
      expect(result.current.selectedServerIds).toEqual([])
      expect(result.current.step).toBe('select')
    })
  })

  describe('closeModal', () => {
    it('should close modal', () => {
      vi.useFakeTimers()
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
      })

      expect(result.current.isOpen).toBe(true)

      act(() => {
        result.current.closeModal()
      })

      expect(result.current.isOpen).toBe(false)

      // After animation delay, state should be reset
      act(() => {
        vi.advanceTimersByTime(300)
      })

      expect(result.current.selectedApp).toBeNull()
      vi.useRealTimers()
    })
  })

  describe('setSelectedServerIds', () => {
    it('should update selected servers', () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.setSelectedServerIds(['srv-1'])
      })

      expect(result.current.selectedServerIds).toEqual(['srv-1'])
    })

    it('should support multiple servers', () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.setSelectedServerIds(['srv-1', 'srv-2'])
      })

      expect(result.current.selectedServerIds).toEqual(['srv-1', 'srv-2'])
    })
  })

  describe('setStep', () => {
    it('should update step', () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.setStep('deploying')
      })

      expect(result.current.step).toBe('deploying')
    })
  })

  describe('updateConfig', () => {
    it('should update config with partial values', () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.updateConfig({ ports: { '8080': 9090 } })
      })

      expect(result.current.config.ports).toEqual({ '8080': 9090 })
      expect(result.current.config.volumes).toEqual({})
      expect(result.current.config.env).toEqual({})

      act(() => {
        result.current.updateConfig({ env: { NODE_ENV: 'production' } })
      })

      expect(result.current.config.ports).toEqual({ '8080': 9090 })
      expect(result.current.config.env).toEqual({ NODE_ENV: 'production' })
    })
  })

  describe('reset', () => {
    it('should reset all state to defaults', () => {
      const { result } = renderHook(() => useDeploymentModal())

      // Set various state
      act(() => {
        result.current.setSelectedServerIds(['srv-1'])
        result.current.setStep('deploying')
        result.current.updateConfig({ ports: { '8080': 9090 } })
      })

      act(() => {
        result.current.reset()
      })

      expect(result.current.step).toBe('select')
      expect(result.current.selectedServerIds).toEqual([])
      expect(result.current.config).toEqual({ ports: {}, volumes: {}, env: {} })
      expect(result.current.error).toBeNull()
      expect(result.current.deploymentResult).toBeNull()
    })
  })

  describe('deploy', () => {
    it('should fail if no app selected', async () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.setSelectedServerIds(['srv-1'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toBe('Please select at least one server')
    })

    it('should fail if no server selected', async () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toBe('Please select at least one server')
    })

    it('should fail if not connected to MCP', async () => {
      mockUseMCP.mockReturnValue({
        client: mockClient as unknown as ReturnType<typeof useMCP>['client'],
        isConnected: false,
        error: null
      })

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toBe('Not connected to MCP server')
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Connection Error',
        message: 'Not connected to the backend server',
        duration: 4000
      })
    })

    it('should fail if selected server not found', async () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['non-existent'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toBe('Selected servers not found')
    })

    it('should fail if server is offline or missing Docker', async () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-3']) // Offline server
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toContain('Some servers are not ready')
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Servers Not Ready',
        message: '1 server(s) are offline or missing Docker',
        duration: 5000
      })
    })

    it('should fail if server has no Docker', async () => {
      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-2']) // No Docker
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.error).toContain('Some servers are not ready')
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Servers Not Ready',
        message: '1 server(s) are offline or missing Docker',
        duration: 5000
      })
    })

    it('should deploy successfully', async () => {
      // Backend returns: { success, data: { installation_id, ... }, message }
      // MCP client wraps: { success, data: <tool_result>, message }
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          success: true,
          data: {
            installation_id: 'inst-123',
            server_id: 'srv-1',
            app_id: 'plex'
          },
          message: 'Installation started'
        }
      })

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(true)
      expect(result.current.deploymentResult).toEqual({
        success: true,
        installationId: 'inst-123',
        serverId: 'srv-1',
        appId: 'plex'
      })
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'success',
        title: 'Deployment Started',
        message: 'Plex is being installed on 1 server(s)',
        duration: 5000
      })
    })

    it('should handle deployment failure from API', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Container creation failed'
      })

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.step).toBe('error')
      expect(result.current.error).toBe('Container creation failed')
    })

    it('should handle deployment exception', async () => {
      mockClient.callTool.mockRejectedValue(new Error('Network timeout'))

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(mockServers)
      })

      expect(success!).toBe(false)
      expect(result.current.step).toBe('error')
      expect(result.current.error).toBe('Network timeout')
    })

    it('should set isDeploying during deployment', async () => {
      let resolveDeployment: (value: unknown) => void
      mockClient.callTool.mockReturnValue(
        new Promise((resolve) => {
          resolveDeployment = resolve
        })
      )

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
      })

      let deployPromise: Promise<boolean>
      act(() => {
        deployPromise = result.current.deploy(mockServers)
      })

      expect(result.current.isDeploying).toBe(true)
      expect(result.current.step).toBe('success') // Multi-server goes straight to success for progress tracking

      await act(async () => {
        resolveDeployment!({ success: true, data: { success: true } })
        await deployPromise!
      })

      expect(result.current.isDeploying).toBe(false)
    })

    it('should pass config to API call', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          success: true,
          data: { installation_id: 'inst-123' },
          message: 'Installation started'
        }
      })

      const { result } = renderHook(() => useDeploymentModal())

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1'])
        result.current.updateConfig({
          ports: { '8080': 9090 },
          env: { API_KEY: 'secret' },
          volumes: { '/data': '/var/lib/app' }
        })
      })

      await act(async () => {
        await result.current.deploy(mockServers)
      })

      expect(mockClient.callTool).toHaveBeenCalledWith('add_app', {
        server_id: 'srv-1',
        app_id: 'plex',
        config: {
          ports: { '8080': 9090 },
          env: { API_KEY: 'secret' },
          volumes: { '/data': '/var/lib/app' }
        }
      })
    })

    it('should deploy to multiple servers', async () => {
      // Backend returns nested structure with snake_case
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          success: true,
          data: {
            installation_id: 'inst-123',
            server_id: 'srv-1',
            app_id: 'plex'
          },
          message: 'Installation started'
        }
      })

      const { result } = renderHook(() => useDeploymentModal())

      // Add another connected server with Docker for multi-server test
      const multiServers = [
        ...mockServers,
        {
          id: 'srv-4',
          name: 'Another Docker Server',
          host: '192.168.1.104',
          port: 22,
          username: 'admin',
          auth_type: 'password' as const,
          status: 'connected' as const,
          docker_installed: true,
          created_at: '2024-01-01T00:00:00Z'
        }
      ]

      act(() => {
        result.current.openModal(mockApp)
        result.current.setSelectedServerIds(['srv-1', 'srv-4'])
      })

      let success: boolean
      await act(async () => {
        success = await result.current.deploy(multiServers)
      })

      expect(success!).toBe(true)
      // Should be called twice, once for each server
      expect(mockClient.callTool).toHaveBeenCalledTimes(2)
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'success',
        title: 'Deployment Started',
        message: 'Plex is being installed on 2 server(s)',
        duration: 5000
      })
    })
  })
})
