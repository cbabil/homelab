/**
 * Unit tests for MCP Provider
 *
 * Tests MCP context provider with connection management.
 * Covers connection states, error handling, and context value.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MCPProvider, useMCP } from './MCPProvider'

// Create mutable mock state
const mockState = {
  isConnected: false,
  isConnecting: false,
  error: null as string | null,
  callTool: vi.fn()
}

// Mock the useMcpClient hook that MCPProvider uses internally
vi.mock('@/hooks/useMcpClient', () => ({
  useMcpClient: () => ({
    isConnected: mockState.isConnected,
    isConnecting: mockState.isConnecting,
    error: mockState.error,
    callTool: mockState.callTool,
    tools: [],
    resources: [],
    prompts: [],
    readResource: vi.fn(),
    getPrompt: vi.fn(),
    authenticate: vi.fn()
  })
}))

// Mock useToast which is used by useMcpClient
vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({ addToast: vi.fn() }),
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}))

// Test component to access MCP context
function TestComponent() {
  const { client, isConnected, error } = useMCP()

  return (
    <div>
      <div data-testid="connected">{isConnected.toString()}</div>
      <div data-testid="error">{error || 'no error'}</div>
      <div data-testid="client-exists">{client ? 'true' : 'false'}</div>
    </div>
  )
}

describe('MCPProvider', () => {
  beforeEach(() => {
    // Reset mock state
    mockState.isConnected = false
    mockState.isConnecting = false
    mockState.error = null
    mockState.callTool = vi.fn().mockResolvedValue({ success: true })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should provide MCP client context', () => {
    mockState.isConnected = true

    render(
      <MCPProvider serverUrl="http://localhost:8000">
        <TestComponent />
      </MCPProvider>
    )

    expect(screen.getByTestId('client-exists')).toHaveTextContent('true')
  })

  it('should show connected status when hook reports connected', () => {
    mockState.isConnected = true

    render(
      <MCPProvider serverUrl="http://localhost:8000">
        <TestComponent />
      </MCPProvider>
    )

    expect(screen.getByTestId('connected')).toHaveTextContent('true')
    expect(screen.getByTestId('error')).toHaveTextContent('no error')
  })

  it('should show error when connection fails', () => {
    mockState.isConnected = false
    mockState.error = 'Connection failed'

    render(
      <MCPProvider serverUrl="http://localhost:8000">
        <TestComponent />
      </MCPProvider>
    )

    expect(screen.getByTestId('connected')).toHaveTextContent('false')
    expect(screen.getByTestId('error')).toHaveTextContent('Connection failed')
  })

  it('should show disconnected status initially', () => {
    mockState.isConnected = false
    mockState.isConnecting = true

    render(
      <MCPProvider serverUrl="http://localhost:8000">
        <TestComponent />
      </MCPProvider>
    )

    expect(screen.getByTestId('connected')).toHaveTextContent('false')
  })

  it('should provide client with callTool function', async () => {
    mockState.isConnected = true
    mockState.callTool.mockResolvedValue({ success: true, data: 'test' })

    render(
      <MCPProvider serverUrl="http://localhost:8000">
        <TestComponent />
      </MCPProvider>
    )

    expect(screen.getByTestId('client-exists')).toHaveTextContent('true')
  })

  it('should throw error when useMCP is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => render(<TestComponent />)).toThrow(
      'useMCP must be used within an MCPProvider'
    )

    consoleSpy.mockRestore()
  })
})