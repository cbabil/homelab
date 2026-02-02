/**
 * Integration tests for MCP Communication
 * 
 * Tests end-to-end MCP protocol communication between frontend and backend.
 * Covers tool calling, event streaming, and error handling scenarios.
 */

import React from 'react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { MCPProvider, useMCP } from '@/providers/MCPProvider'
import { ToastProvider } from '@/components/ui/Toast'
import { server } from '@/test/mocks/server'
import { rest } from 'msw'

// Test component that uses MCP functionality
function TestMCPIntegration() {
  const [result, setResult] = React.useState<string>('')
  const { client, isConnected, error } = useMCP()

  const handleHealthCheck = async () => {
    try {
      const response = await client.callTool('get_health_status', {})
      setResult(response.success ? 'Health check passed' : 'Health check failed')
    } catch (_err) {
      setResult('Error calling tool')
    }
  }

  return (
    <div>
      <div data-testid="connection-status">
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
      <div data-testid="error-status">{error || 'No error'}</div>
      <button onClick={handleHealthCheck} data-testid="health-check-btn">
        Check Health
      </button>
      <div data-testid="result">{result}</div>
    </div>
  )
}

describe('MCP Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    server.resetHandlers()
  })

  const renderWithProviders = (component: React.ReactNode) => {
    return render(
      <BrowserRouter>
        <ToastProvider>
          <MCPProvider serverUrl="http://localhost:8000">
            {component}
          </MCPProvider>
        </ToastProvider>
      </BrowserRouter>
    )
  }

  it('should establish MCP connection and show connected status', async () => {
    renderWithProviders(<TestMCPIntegration />)

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
      expect(screen.getByTestId('error-status')).toHaveTextContent('No error')
    }, { timeout: 3000 })
  })

  it('should successfully call MCP tool and get response', async () => {
    server.use(
      rest.post('http://localhost:8000/mcp', (_req, res, ctx) => {
        return res(
          ctx.json({
            success: true,
            data: {
              status: 'healthy',
              components: { mcp_server: 'healthy' }
            },
            message: 'Health check completed successfully'
          })
        )
      })
    )

    renderWithProviders(<TestMCPIntegration />)

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })

    const healthButton = screen.getByTestId('health-check-btn')
    await userEvent.click(healthButton)

    await waitFor(() => {
      expect(screen.getByTestId('result')).toHaveTextContent('Health check passed')
    })
  })

  it('should handle MCP tool call failures', async () => {
    server.use(
      rest.post('http://localhost:8000/mcp', (_req, res, ctx) => {
        return res(ctx.status(500), ctx.text('Internal server error'))
      })
    )

    renderWithProviders(<TestMCPIntegration />)

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })

    const healthButton = screen.getByTestId('health-check-btn')
    await userEvent.click(healthButton)

    await waitFor(() => {
      expect(screen.getByTestId('result')).toHaveTextContent('Health check failed')
    })
  })

  it('should handle connection failures and show error state', async () => {
    server.use(
      rest.get('http://localhost:8000/health', (_req, res, _ctx) => {
        return res.networkError('Network connection failed')
      })
    )

    renderWithProviders(<TestMCPIntegration />)

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Disconnected')
      expect(screen.getByTestId('error-status')).toHaveTextContent('Failed to connect to MCP server')
    }, { timeout: 3000 })
  })
})