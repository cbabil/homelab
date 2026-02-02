/**
 * Unit tests for useDashboardData hook
 *
 * Tests dashboard data fetching, auto-refresh, and state management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useDashboardData } from '../useDashboardData'
import { useMCP } from '@/providers/MCPProvider'

// Mock the MCP provider
vi.mock('@/providers/MCPProvider')

const mockUseMCP = vi.mocked(useMCP)

describe('useDashboardData', () => {
  const mockClient = {
    callTool: vi.fn() as ReturnType<typeof vi.fn>,
    isConnected: () => true
  }

  const mockServersResponse = {
    success: true,
    data: {
      servers: [
        { id: '1', name: 'Server 1', host: 'host1', port: 22, username: 'user', auth_type: 'password', status: 'connected' },
        { id: '2', name: 'Server 2', host: 'host2', port: 22, username: 'user', auth_type: 'password', status: 'connected' },
        { id: '3', name: 'Server 3', host: 'host3', port: 22, username: 'user', auth_type: 'password', status: 'connected' },
        { id: '4', name: 'Server 4', host: 'host4', port: 22, username: 'user', auth_type: 'password', status: 'connected' },
        { id: '5', name: 'Server 5', host: 'host5', port: 22, username: 'user', auth_type: 'password', status: 'disconnected' }
      ]
    }
  }

  const mockDashboardSummary = {
    total_servers: 5,
    online_servers: 4,
    offline_servers: 1,
    total_apps: 10,
    running_apps: 8,
    stopped_apps: 1,
    error_apps: 1,
    avg_cpu_percent: 45.5,
    avg_memory_percent: 60.2,
    avg_disk_percent: 35.0,
    recent_activities: [
      {
        id: '1',
        activity_type: 'server_connect',
        description: 'Server connected',
        created_at: new Date().toISOString()
      }
    ]
  }

  const mockHealthStatus = {
    status: 'healthy'
  }

  beforeEach(() => {
    mockClient.callTool.mockReset()
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should return loading state initially', () => {
    mockClient.callTool.mockImplementation(() => new Promise(() => {}))

    const { result } = renderHook(() => useDashboardData())

    expect(result.current.loading).toBe(true)
    expect(result.current.dashboardData).toBeNull()
  })

  it('should fetch dashboard data on mount', async () => {
    mockClient.callTool
      .mockResolvedValueOnce({ data: mockServersResponse })
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    const { result } = renderHook(() => useDashboardData())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(mockClient.callTool).toHaveBeenCalledWith('list_servers', {})
    expect(mockClient.callTool).toHaveBeenCalledWith('get_dashboard_summary', {})
    expect(mockClient.callTool).toHaveBeenCalledWith('get_health_status', {})
    // Server counts should be overridden from backend data
    expect(result.current.dashboardData?.total_servers).toBe(5)
    expect(result.current.dashboardData?.online_servers).toBe(4)
    expect(result.current.healthStatus).toEqual(mockHealthStatus)
  })

  it('should not fetch data when not connected', () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: false,
      error: null
    })

    const { result } = renderHook(() => useDashboardData())

    expect(mockClient.callTool).not.toHaveBeenCalled()
    expect(result.current.isConnected).toBe(false)
  })

  it('should set lastUpdated after successful fetch', async () => {
    mockClient.callTool
      .mockResolvedValueOnce({ data: mockServersResponse })
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    const { result } = renderHook(() => useDashboardData())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.lastUpdated).toBeInstanceOf(Date)
  })

  it('should handle fetch errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockClient.callTool.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useDashboardData())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to fetch dashboard data:',
      expect.any(Error)
    )
    expect(result.current.dashboardData).toBeNull()

    consoleSpy.mockRestore()
  })

  it('should expose isConnected from MCP provider', () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    const { result } = renderHook(() => useDashboardData())

    expect(result.current.isConnected).toBe(true)
  })

  it('should provide refresh function', async () => {
    mockClient.callTool
      .mockResolvedValueOnce({ data: mockServersResponse })
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    const { result } = renderHook(() => useDashboardData())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(typeof result.current.refresh).toBe('function')
  })

  it('should call refresh when refresh function is invoked', async () => {
    mockClient.callTool
      .mockResolvedValueOnce({ data: mockServersResponse })
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })
      .mockResolvedValueOnce({ data: mockServersResponse })
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    const { result } = renderHook(() => useDashboardData())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const callCountBeforeRefresh = mockClient.callTool.mock.calls.length

    act(() => {
      result.current.refresh()
    })

    await waitFor(() => {
      expect(mockClient.callTool.mock.calls.length).toBeGreaterThan(callCountBeforeRefresh)
    })
  })
})
