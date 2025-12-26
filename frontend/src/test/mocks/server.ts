/**
 * Mock Service Worker Server Configuration
 * 
 * Sets up MSW for mocking API requests in tests.
 * Provides realistic backend responses for MCP client testing.
 */

import { setupServer } from 'msw/node'
import { rest } from 'msw'

// Mock handlers for MCP backend API
const handlers = [
  // Health check endpoint
  rest.get('http://localhost:8000/health', (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        service: 'homelab-assistant-backend',
        version: '0.1.0'
      })
    )
  }),

  // MCP tool call endpoint
  rest.post('http://localhost:8000/mcp', (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: { message: 'Tool call successful' },
        message: 'MCP tool executed successfully'
      })
    )
  }),

  // MCP events endpoint
  rest.get('http://localhost:8000/events', (_req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.text('data: {"event": "test", "data": {}}\n\n')
    )
  })
]

// Create MSW server instance
export const server = setupServer(...handlers)