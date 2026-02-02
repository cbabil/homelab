/**
 * System Setup Hook Tests
 *
 * Unit tests for the useSystemSetup hook.
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock callTool function with vi.hoisted
const { mockCallTool } = vi.hoisted(() => {
  const mockCallTool = vi.fn()
  return { mockCallTool }
})

// Mock MCP Provider - must be before imports
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: {
      callTool: mockCallTool,
      isConnected: () => true
    },
    isConnected: true,
    error: null
  })
}))

import { useSystemSetup } from '../useSystemSetup'

describe('useSystemSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return loading state initially', () => {
    mockCallTool.mockImplementation(() => new Promise(() => {})) // Never resolves

    const { result } = renderHook(() => useSystemSetup())

    // Initially loading
    expect(result.current.isLoading).toBe(true)
  })

  it('should return needsSetup: true when system not set up', async () => {
    // Mock matches real MCP client response structure:
    // mcpClient wraps backend response, so data is nested
    mockCallTool.mockResolvedValue({
      success: true,
      data: {
        success: true,
        data: {
          needs_setup: true,
          is_setup: false,
          app_name: 'Tomo'
        }
      }
    })

    const { result } = renderHook(() => useSystemSetup())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.needsSetup).toBe(true)
    expect(result.current.error).toBeNull()
    expect(mockCallTool).toHaveBeenCalledWith('get_system_setup', {})
  })

  it('should return needsSetup: false when system is set up', async () => {
    mockCallTool.mockResolvedValue({
      success: true,
      data: {
        success: true,
        data: {
          needs_setup: false,
          is_setup: true,
          app_name: 'Tomo'
        }
      }
    })

    const { result } = renderHook(() => useSystemSetup())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.needsSetup).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should handle API errors gracefully', async () => {
    mockCallTool.mockResolvedValue({
      success: false,
      message: 'Database connection failed'
    })

    const { result } = renderHook(() => useSystemSetup())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBe('Database connection failed')
  })

  it('should handle network errors gracefully', async () => {
    mockCallTool.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useSystemSetup())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBe('Network error')
  })

  it('should provide refetch function', async () => {
    mockCallTool.mockResolvedValue({
      success: true,
      data: {
        success: true,
        data: {
          needs_setup: true,
          is_setup: false,
          app_name: 'Tomo'
        }
      }
    })

    const { result } = renderHook(() => useSystemSetup())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Get initial call count (may be 1 or 2 depending on StrictMode)
    const initialCallCount = mockCallTool.mock.calls.length

    // Refetch
    await act(async () => {
      await result.current.refetch()
    })

    // Should have one more call than initial
    expect(mockCallTool).toHaveBeenCalledTimes(initialCallCount + 1)
  })
})
