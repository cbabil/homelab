/**
 * useServerProvisioning Hook Tests - Docker
 *
 * Tests for installDocker and skipDocker operations.
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

describe('useServerProvisioning - Docker', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('installDocker', () => {
    it('should call MCP tool and update state on success', async () => {
      mockCallTool
        .mockResolvedValueOnce({ data: { success: true, docker_installed: false } })
        .mockResolvedValueOnce({ data: { success: true } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installDocker() })

      expect(mockCallTool).toHaveBeenCalledWith('install_docker', { server_id: 'server-123' })
      expect(result.current.state.dockerInstalled).toBe(true)
      expect(result.current.state.currentStep).toBe('agent')
    })

    it('should set error state on docker install failure', async () => {
      mockCallTool
        .mockResolvedValueOnce({ data: { success: true, docker_installed: false } })
        .mockResolvedValueOnce({ data: { success: false, error: 'Permission denied' } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installDocker() })

      expect(result.current.state.canRetry).toBe(true)
      expect(result.current.state.steps.find((s) => s.id === 'docker')?.status).toBe('error')
    })

    it('should handle exceptions during docker install', async () => {
      mockCallTool
        .mockResolvedValueOnce({ data: { success: true, docker_installed: false } })
        .mockRejectedValueOnce(new Error('Docker timeout'))
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      await act(async () => { await result.current.installDocker() })

      expect(result.current.state.canRetry).toBe(true)
      expect(result.current.state.steps.find((s) => s.id === 'docker')?.status).toBe('error')
    })
  })

  describe('skipDocker', () => {
    it('should mark docker as skipped and transition to agent step', async () => {
      mockCallTool.mockResolvedValue({ data: { success: true, docker_installed: false } })
      const { result } = renderHook(() => useServerProvisioning())

      await act(async () => { await result.current.startProvisioning('server-123') })
      act(() => { result.current.skipDocker() })

      expect(result.current.state.steps.find((s) => s.id === 'docker')?.status).toBe('skipped')
      expect(result.current.state.currentStep).toBe('agent')
      expect(result.current.state.requiresDecision).toBe('agent')
    })
  })
})
