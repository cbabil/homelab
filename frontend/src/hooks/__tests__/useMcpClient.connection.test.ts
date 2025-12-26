/**
 * useMcpClient Connection Tests
 *
 * Ensures connection failure toasts are not duplicated during retry attempts.
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useMcpClient } from '../useMcpClient'

const addToast = vi.fn()
const connectMock = vi.fn()

vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({ addToast })
}))

vi.mock('@/services/mcpClient', () => ({
  HomelabMCPClient: vi.fn().mockImplementation(() => ({
    connect: connectMock,
    callTool: vi.fn(),
    isConnected: vi.fn().mockReturnValue(false)
  }))
}))

describe('useMcpClient connection handling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    connectMock.mockRejectedValue(new Error('Failed to fetch'))
    addToast.mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('emits connection failure toast only once across retries', async () => {
    renderHook(() => useMcpClient({ serverUrl: 'http://localhost:8000/mcp', autoReconnect: false }))

    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(addToast).toHaveBeenCalledTimes(1)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000)
      await Promise.resolve()
    })

    expect(addToast).toHaveBeenCalledTimes(1)
  })
})
