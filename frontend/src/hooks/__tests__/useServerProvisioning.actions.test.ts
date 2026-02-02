/** useServerProvisioning Hook Tests - Actions: agent install, skip, cancel, retry, reset */

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

describe('useServerProvisioning - Actions', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('installAgent', () => {
    it('should call MCP tool and complete flow on success', async () => {
      mockCallTool
        .mockResolvedValueOnce({ data: { success: true, docker_installed: true } })
        .mockResolvedValueOnce({ data: { success: true, agent_id: 'agent-abc' } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installAgent() })

      expect(mockCallTool).toHaveBeenCalledWith('install_agent', { server_id: 'server-123' })
      expect(result.current.state.currentStep).toBe('complete')
      expect(result.current.state.isProvisioning).toBe(false)
    })

    it('should set error state on agent install failure', async () => {
      mockCallTool
        .mockResolvedValueOnce({ data: { success: true, docker_installed: true } })
        .mockResolvedValueOnce({ data: { success: false, error: 'Agent failed' } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installAgent() })

      expect(result.current.state.canRetry).toBe(true)
      expect(result.current.state.steps.find((s) => s.id === 'agent')?.status).toBe('error')
    })
  })

  describe('skipAgent', () => {
    it('should mark agent as skipped and complete flow', async () => {
      mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: true } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      act(() => { result.current.skipAgent() })

      expect(result.current.state.steps.find((s) => s.id === 'agent')?.status).toBe('skipped')
      expect(result.current.state.currentStep).toBe('complete')
      expect(result.current.state.isProvisioning).toBe(false)
    })
  })

  describe('cancel', () => {
    it('should call delete_server and reset state', async () => {
      mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: false } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.cancel() })

      expect(mockCallTool).toHaveBeenCalledWith('delete_server', { server_id: 'server-123' })
      expect(result.current.state.isProvisioning).toBe(false)
      expect(result.current.state.serverId).toBeUndefined()
    })
  })

  describe('retry', () => {
    it('should re-attempt failed connection step', async () => {
      mockCallTool.mockResolvedValueOnce({ data: { success: false, error: 'Timeout' } })
        .mockResolvedValueOnce({ data: { success: true, docker_installed: true } })
      const { result } = renderHook(() => useServerProvisioning())
      await act(async () => { await result.current.startProvisioning('server-123') })
      expect(result.current.state.canRetry).toBe(true)
      await act(async () => { result.current.retry() })
      expect(mockCallTool).toHaveBeenCalledTimes(2)
    })

    it('should re-attempt failed docker step', async () => {
      mockCallTool.mockResolvedValueOnce({ data: { success: true, docker_installed: false } })
        .mockResolvedValueOnce({ data: { success: false, error: 'Docker fail' } })
        .mockResolvedValueOnce({ data: { success: true } })
      const { result } = renderHook(() => useServerProvisioning())
      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installDocker() })
      await act(async () => { result.current.retry() })
      expect(mockCallTool).toHaveBeenLastCalledWith('install_docker', { server_id: 'server-123' })
    })
  })

  describe('reset', () => {
    it('should reset to initial state', async () => {
      mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: false } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      act(() => { result.current.reset() })

      expect(result.current.state.isProvisioning).toBe(false)
      expect(result.current.state.serverId).toBeUndefined()
      expect(result.current.state.currentStep).toBe('connection')
    })
  })
})
