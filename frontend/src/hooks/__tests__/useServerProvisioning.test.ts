/**
 * useServerProvisioning Hook Tests - Connection
 *
 * Tests for startProvisioning and connection handling.
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockCallTool } = vi.hoisted(() => ({ mockCallTool: vi.fn() }))

vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: { callTool: mockCallTool, isConnected: () => true },
    isConnected: true,
    error: null
  })
}))

import { useServerProvisioning } from '../useServerProvisioning'

describe('useServerProvisioning - Connection', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('should initialize state and call test_connection', async () => {
    mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: false } })
    const { result } = renderHook(() => useServerProvisioning())

    await act(async () => { await result.current.startProvisioning('server-123') })

    expect(mockCallTool).toHaveBeenCalledWith('test_connection', { server_id: 'server-123' })
    expect(result.current.state.serverId).toBe('server-123')
  })

  it('should transition to docker check on connection success', async () => {
    mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: false } })
    const { result } = renderHook(() => useServerProvisioning())

    await act(async () => { await result.current.startProvisioning('server-123') })

    expect(result.current.state.currentStep).toBe('docker')
    expect(result.current.state.requiresDecision).toBe('docker')
    expect(result.current.state.steps.find((s) => s.id === 'connection')?.status).toBe('success')
  })

  it('should skip to agent if docker already installed', async () => {
    mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: true } })
    const { result } = renderHook(() => useServerProvisioning())

    await act(async () => { await result.current.startProvisioning('server-123') })

    expect(result.current.state.currentStep).toBe('agent')
    expect(result.current.state.dockerInstalled).toBe(true)
    expect(result.current.state.steps.find((s) => s.id === 'docker')?.status).toBe('success')
  })

  it('should set error state and canRetry on connection failure', async () => {
    mockCallTool.mockResolvedValue({ data: { success: false, error: 'SSH timeout' } })
    const { result } = renderHook(() => useServerProvisioning())

    await act(async () => { await result.current.startProvisioning('server-123') })

    expect(result.current.state.canRetry).toBe(true)
    const connStep = result.current.state.steps.find((s) => s.id === 'connection')
    expect(connStep?.status).toBe('error')
    expect(connStep?.error).toBe('SSH timeout')
  })

  it('should handle exceptions during connection', async () => {
    mockCallTool.mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => useServerProvisioning())

    await act(async () => { await result.current.startProvisioning('server-123') })

    expect(result.current.state.canRetry).toBe(true)
    expect(result.current.state.steps.find((s) => s.id === 'connection')?.status).toBe('error')
  })
})
