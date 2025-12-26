/**
 * MCP Client Hook Tests
 * 
 * Unit tests for the useMcpClient hook wrapper.
 */

import { renderHook } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMcpClient } from '../useMcpClient'

// Mock use-mcp package
vi.mock('use-mcp/react', () => ({
  useMcp: vi.fn()
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

  it('should initialize with correct default options', async () => {
    const { useMcp } = await import('use-mcp/react')
    vi.mocked(useMcp).mockReturnValue({
      state: 'connecting',
      tools: [],
      resources: [],
      prompts: [],
      resourceTemplates: [],
      callTool: vi.fn(),
      readResource: vi.fn(),
      getPrompt: vi.fn(),
      authenticate: vi.fn(),
      log: vi.fn(),
      listResources: vi.fn(),
      listPrompts: vi.fn(),
      listTools: vi.fn()
    } as any)

    renderHook(() => useMcpClient({ 
      serverUrl: 'http://localhost:8000' 
    }))

    expect(useMcp).toHaveBeenCalledWith({
      url: 'http://localhost:8000',
      clientName: 'Homelab Assistant',
      autoReconnect: true
    })
  })

  it('should return correct connection state when ready', async () => {
    const { useMcp } = await import('use-mcp/react')
    vi.mocked(useMcp).mockReturnValue({
      state: 'ready',
      tools: [],
      resources: [],
      prompts: [],
      resourceTemplates: [],
      callTool: vi.fn(),
      readResource: vi.fn(),
      getPrompt: vi.fn(),
      authenticate: vi.fn(),
      log: vi.fn(),
      listResources: vi.fn(),
      listPrompts: vi.fn(),
      listTools: vi.fn()
    } as any)

    const { result } = renderHook(() => useMcpClient({ 
      serverUrl: 'http://localhost:8000' 
    }))

    expect(result.current.isConnected).toBe(true)
    expect(result.current.isConnecting).toBe(false)
    expect(result.current.error).toBe(null)
  })

  it('should handle tool calls with success response', async () => {
    const mockCallTool = vi.fn().mockResolvedValue({ result: 'success' })
    const { useMcp } = await import('use-mcp/react')
    
    vi.mocked(useMcp).mockReturnValue({
      state: 'ready',
      tools: [],
      resources: [],
      prompts: [],
      resourceTemplates: [],
      callTool: mockCallTool,
      readResource: vi.fn(),
      getPrompt: vi.fn(),
      authenticate: vi.fn(),
      log: vi.fn(),
      listResources: vi.fn(),
      listPrompts: vi.fn(),
      listTools: vi.fn()
    } as any)

    const { result } = renderHook(() => useMcpClient({ 
      serverUrl: 'http://localhost:8000' 
    }))

    const response = await result.current.callTool('test_tool', { param: 'value' })

    expect(mockCallTool).toHaveBeenCalledWith('test_tool', { param: 'value' })
    expect(response.success).toBe(true)
    expect(response.data).toEqual({ result: 'success' })
  })

  it('should handle tool call errors', async () => {
    const mockCallTool = vi.fn().mockRejectedValue(new Error('Tool failed'))
    const { useMcp } = await import('use-mcp/react')
    
    vi.mocked(useMcp).mockReturnValue({
      state: 'ready',
      tools: [],
      resources: [],
      prompts: [],
      resourceTemplates: [],
      callTool: mockCallTool,
      readResource: vi.fn(),
      getPrompt: vi.fn(),
      authenticate: vi.fn(),
      log: vi.fn(),
      listResources: vi.fn(),
      listPrompts: vi.fn(),
      listTools: vi.fn()
    } as any)

    const { result } = renderHook(() => useMcpClient({ 
      serverUrl: 'http://localhost:8000' 
    }))

    const response = await result.current.callTool('test_tool', { param: 'value' })

    expect(response.success).toBe(false)
    expect(response.error).toBe('Tool failed')
  })
})