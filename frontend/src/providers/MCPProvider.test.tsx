/**
 * Unit tests for MCP Provider
 * 
 * Tests MCP context provider with connection management.
 * Covers connection states, error handling, and context value.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MCPProvider, useMCP } from './MCPProvider'
import { HomelabMCPClient } from '@/services/mcpClient'
import { NotificationProvider } from './NotificationProvider'

// Mock the MCP client
vi.mock('@/services/mcpClient')

const MockedHomelabMCPClient = vi.mocked(HomelabMCPClient)

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
  let mockClient: any

  beforeEach(() => {
    mockClient = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn().mockReturnValue(false)
    }

    MockedHomelabMCPClient.mockImplementation(() => mockClient)
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.clearAllTimers()
  })

  it('should provide MCP client context', async () => {
    mockClient.connect.mockResolvedValue(undefined)

    render(
      <NotificationProvider>
        <MCPProvider serverUrl="http://localhost:8000">
          <TestComponent />
        </MCPProvider>
      </NotificationProvider>
    )

    expect(screen.getByTestId('client-exists')).toHaveTextContent('true')
  })

  it('should establish connection on mount', async () => {
    mockClient.connect.mockResolvedValue(undefined)

    render(
      <NotificationProvider>
        <MCPProvider serverUrl="http://localhost:8000">
          <TestComponent />
        </MCPProvider>
      </NotificationProvider>
    )

    await waitFor(() => {
      expect(mockClient.connect).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true')
      expect(screen.getByTestId('error')).toHaveTextContent('no error')
    })
  })

  it('should handle connection failure', async () => {
    const errorMessage = 'Connection failed'
    mockClient.connect.mockRejectedValue(new Error(errorMessage))

    vi.useFakeTimers()

    render(
      <NotificationProvider>
        <MCPProvider serverUrl="http://localhost:8000">
          <TestComponent />
        </MCPProvider>
      </NotificationProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('false')
      expect(screen.getByTestId('error')).toHaveTextContent(errorMessage)
    })

    vi.useRealTimers()
  })

  it('should retry connection after failure', async () => {
    const errorMessage = 'Connection failed'
    mockClient.connect
      .mockRejectedValueOnce(new Error(errorMessage))
      .mockResolvedValueOnce(undefined)

    vi.useFakeTimers()

    render(
      <NotificationProvider>
        <MCPProvider serverUrl="http://localhost:8000">
          <TestComponent />
        </MCPProvider>
      </NotificationProvider>
    )

    // Wait for first connection attempt to fail
    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('false')
    })

    // Fast-forward time to trigger retry
    vi.advanceTimersByTime(5000)

    await waitFor(() => {
      expect(mockClient.connect).toHaveBeenCalledTimes(2)
    })

    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true')
      expect(screen.getByTestId('error')).toHaveTextContent('no error')
    })

    vi.useRealTimers()
  })

  it('should disconnect client on unmount', () => {
    const { unmount } = render(
      <NotificationProvider>
        <MCPProvider serverUrl="http://localhost:8000">
          <TestComponent />
        </MCPProvider>
      </NotificationProvider>
    )

    unmount()

    expect(mockClient.disconnect).toHaveBeenCalledTimes(1)
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