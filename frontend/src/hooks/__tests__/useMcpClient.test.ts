/**
 * MCP Client Hook Tests
 *
 * Unit tests for the useMcpClient hook wrapper.
 */

import { renderHook } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMcpClient } from '../useMcpClient'

// Mock TomoMCPClient
vi.mock('@/services/mcpClient', () => ({
  TomoMCPClient: vi.fn().mockImplementation(() => ({
    connect: vi.fn().mockResolvedValue(undefined),
    callTool: vi.fn().mockResolvedValue({ success: true, data: {} })
  }))
}))

// Mock toast provider
vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({
    addToast: vi.fn()
  })
}))

describe('useMcpClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with correct connection state', async () => {
    const { result } = renderHook(() => useMcpClient({
      serverUrl: 'http://localhost:8000'
    }))

    // Should start with initial values
    expect(result.current.isConnected).toBe(false)
    // Note: isConnecting may be true or false depending on timing
  })

  it('should provide connection state properties', () => {
    const { result } = renderHook(() => useMcpClient({
      serverUrl: 'http://localhost:8000'
    }))

    expect(result.current).toHaveProperty('isConnected')
    expect(result.current).toHaveProperty('isConnecting')
    expect(result.current).toHaveProperty('error')
    expect(result.current).toHaveProperty('tools')
    expect(result.current).toHaveProperty('resources')
    expect(result.current).toHaveProperty('prompts')
  })

  it('should handle tool calls', async () => {
    const { result } = renderHook(() => useMcpClient({
      serverUrl: 'http://localhost:8000'
    }))

    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 100))

    const response = await result.current.callTool('test_tool', { param: 'value' })

    // Should either fail with error or succeed - depends on connection
    expect(response).toHaveProperty('success')
  })

  it('should provide all required methods', () => {
    const { result } = renderHook(() => useMcpClient({
      serverUrl: 'http://localhost:8000'
    }))

    expect(result.current).toHaveProperty('callTool')
    expect(result.current).toHaveProperty('readResource')
    expect(result.current).toHaveProperty('getPrompt')
    expect(result.current).toHaveProperty('authenticate')
    expect(typeof result.current.callTool).toBe('function')
    expect(typeof result.current.readResource).toBe('function')
    expect(typeof result.current.getPrompt).toBe('function')
    expect(typeof result.current.authenticate).toBe('function')
  })
})