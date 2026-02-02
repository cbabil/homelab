import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useInstallationStatus, InstallationStatusData } from '../useInstallationStatus'

// Mock the MCP provider with vi.hoisted
const { mockCallTool } = vi.hoisted(() => {
  const mockCallTool = vi.fn()
  return { mockCallTool }
})

vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: { callTool: mockCallTool },
    isConnected: true
  })
}))

describe('useInstallationStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockCallTool.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useInstallationStatus())

    expect(result.current.statusData).toBeNull()
    expect(result.current.isPolling).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should start polling when startPolling is called', async () => {
    const mockStatus: InstallationStatusData = {
      id: 'install-123',
      status: 'pulling',
      app_id: 'nginx',
      server_id: 'server-1'
    }

    mockCallTool.mockResolvedValue({
      success: true,
      data: mockStatus
    })

    const { result } = renderHook(() => useInstallationStatus())

    act(() => {
      result.current.startPolling('install-123')
    })

    expect(result.current.isPolling).toBe(true)

    await waitFor(() => {
      expect(mockCallTool).toHaveBeenCalledWith('get_installation_status', {
        installation_id: 'install-123'
      })
    })

    await waitFor(() => {
      expect(result.current.statusData).toEqual(mockStatus)
    })
  })

  it('should stop polling on terminal state "running"', async () => {
    const mockStatus: InstallationStatusData = {
      id: 'install-123',
      status: 'running',
      app_id: 'nginx',
      server_id: 'server-1',
      container_name: 'nginx-container'
    }

    mockCallTool.mockResolvedValue({
      success: true,
      data: mockStatus
    })

    const onComplete = vi.fn()
    const { result } = renderHook(() => useInstallationStatus({ onComplete }))

    act(() => {
      result.current.startPolling('install-123')
    })

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false)
    })

    expect(onComplete).toHaveBeenCalledWith(mockStatus)
  })

  it('should stop polling and call onError on terminal state "error"', async () => {
    const mockStatus: InstallationStatusData = {
      id: 'install-123',
      status: 'error',
      app_id: 'nginx',
      server_id: 'server-1',
      error_message: 'Failed to pull image'
    }

    mockCallTool.mockResolvedValue({
      success: true,
      data: mockStatus
    })

    const onError = vi.fn()
    const { result } = renderHook(() => useInstallationStatus({ onError }))

    act(() => {
      result.current.startPolling('install-123')
    })

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false)
    })

    expect(onError).toHaveBeenCalledWith('Failed to pull image', mockStatus)
    expect(result.current.error).toBe('Failed to pull image')
  })

  it('should call onStatusChange when status changes', async () => {
    let callCount = 0
    mockCallTool.mockImplementation(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({
          success: true,
          data: { id: 'install-123', status: 'pulling', app_id: 'nginx', server_id: 'server-1' }
        })
      }
      return Promise.resolve({
        success: true,
        data: { id: 'install-123', status: 'creating', app_id: 'nginx', server_id: 'server-1' }
      })
    })

    const onStatusChange = vi.fn()
    const { result } = renderHook(() => useInstallationStatus({ onStatusChange }))

    act(() => {
      result.current.startPolling('install-123')
    })

    // First call
    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalledWith('pulling', expect.objectContaining({ status: 'pulling' }))
    })

    // Advance time for next poll
    await act(async () => {
      vi.advanceTimersByTime(2000)
    })

    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalledWith('creating', expect.objectContaining({ status: 'creating' }))
    })
  })

  it('should stop polling when stopPolling is called', async () => {
    mockCallTool.mockResolvedValue({
      success: true,
      data: { id: 'install-123', status: 'pulling', app_id: 'nginx', server_id: 'server-1' }
    })

    const { result } = renderHook(() => useInstallationStatus())

    act(() => {
      result.current.startPolling('install-123')
    })

    expect(result.current.isPolling).toBe(true)

    act(() => {
      result.current.stopPolling()
    })

    expect(result.current.isPolling).toBe(false)
  })

  it('should reset state when reset is called', async () => {
    mockCallTool.mockResolvedValue({
      success: true,
      data: { id: 'install-123', status: 'pulling', app_id: 'nginx', server_id: 'server-1' }
    })

    const { result } = renderHook(() => useInstallationStatus())

    act(() => {
      result.current.startPolling('install-123')
    })

    await waitFor(() => {
      expect(result.current.statusData).not.toBeNull()
    })

    act(() => {
      result.current.reset()
    })

    expect(result.current.statusData).toBeNull()
    expect(result.current.isPolling).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should handle API errors gracefully', async () => {
    mockCallTool.mockResolvedValue({
      success: false,
      error: 'Installation not found'
    })

    const { result } = renderHook(() => useInstallationStatus())

    act(() => {
      result.current.startPolling('install-123')
    })

    await waitFor(() => {
      expect(result.current.error).toBe('Installation not found')
    })

    // Should continue polling on transient errors
    expect(result.current.isPolling).toBe(true)
  })

  it('should use custom poll interval', async () => {
    mockCallTool.mockResolvedValue({
      success: true,
      data: { id: 'install-123', status: 'pulling', app_id: 'nginx', server_id: 'server-1' }
    })

    const { result } = renderHook(() => useInstallationStatus({ pollInterval: 5000 }))

    act(() => {
      result.current.startPolling('install-123')
    })

    // Initial call
    await waitFor(() => {
      expect(mockCallTool).toHaveBeenCalledTimes(1)
    })

    // Advance by default interval (2s) - should not trigger another call
    await act(async () => {
      vi.advanceTimersByTime(2000)
    })

    expect(mockCallTool).toHaveBeenCalledTimes(1)

    // Advance to custom interval (5s total)
    await act(async () => {
      vi.advanceTimersByTime(3000)
    })

    await waitFor(() => {
      expect(mockCallTool).toHaveBeenCalledTimes(2)
    })
  })
})
