/**
 * Unit tests for MCP Client Service
 * 
 * Tests MCP client functionality with FastMCP protocol implementation.
 * Covers connection management, tool calling, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { HomelabMCPClient } from './mcpClient'

describe('HomelabMCPClient', () => {
  let client: HomelabMCPClient
  let fetchMock: ReturnType<typeof vi.fn>
  const baseUrl = 'http://localhost:8000'

  beforeEach(() => {
    fetchMock = vi.fn()
    global.fetch = fetchMock
    client = new HomelabMCPClient(baseUrl)
  })

  describe('constructor', () => {
    it('should initialize with base URL', () => {
      expect(client.isConnected()).toBe(false)
    })

    it('should remove trailing slash from base URL', () => {
      const clientWithSlash = new HomelabMCPClient('http://localhost:8000/')
      expect(clientWithSlash.isConnected()).toBe(false)
    })
  })

  describe('connect', () => {
    it('should connect successfully with valid MCP initialization', async () => {
      // Mock session response
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: vi.fn().mockReturnValue('test-session-id')
        }
      } as any)

      // Mock initialization response with SSE format
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}\n\n')
      } as any)

      // Mock initialized notification response
      fetchMock.mockResolvedValueOnce({
        ok: true
      } as any)

      await expect(client.connect()).resolves.not.toThrow()
      expect(client.isConnected()).toBe(true)
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })

    it('should handle missing session ID', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: {
          get: vi.fn().mockReturnValue(null)
        }
      } as any)

      await expect(client.connect()).rejects.toThrow('Failed to get session ID from MCP server')
      expect(client.isConnected()).toBe(false)
    })

    it('should handle network error', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'))

      await expect(client.connect()).rejects.toThrow('Failed to connect to MCP server')
      expect(client.isConnected()).toBe(false)
    })
  })

  describe('disconnect', () => {
    it('should disconnect and reset state', async () => {
      // Mock successful connection
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: { get: vi.fn().mockReturnValue('test-session-id') }
      } as any)
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}\n\n')
      } as any)
      fetchMock.mockResolvedValueOnce({ ok: true } as any)

      await client.connect()
      expect(client.isConnected()).toBe(true)
      
      await client.disconnect()
      expect(client.isConnected()).toBe(false)
    })
  })

  describe('callTool', () => {
    it('should call tool successfully', async () => {
      // Mock successful connection
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: { get: vi.fn().mockReturnValue('test-session-id') }
      } as any)
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}\n\n')
      } as any)
      fetchMock.mockResolvedValueOnce({ ok: true } as any)

      await client.connect()
      
      // Mock tool call response
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"status":"success","data":"test"}}\n\n')
      } as any)

      const result = await client.callTool('get_health_status', {})

      expect(result.success).toBe(true)
      expect(result.data).toEqual({ status: 'success', data: 'test' })
      expect(result.message).toBe('Tool call successful')
    })

    it('should handle tool call error response', async () => {
      // Mock successful connection
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: { get: vi.fn().mockReturnValue('test-session-id') }
      } as any)
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}\n\n')
      } as any)
      fetchMock.mockResolvedValueOnce({ ok: true } as any)

      await client.connect()
      
      // Mock error response
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","error":{"message":"Tool not found"}}\n\n')
      } as any)

      const result = await client.callTool('invalid_tool', {})

      expect(result.success).toBe(false)
      expect(result.error).toBe('Tool not found')
      expect(result.message).toBe('Tool not found')
    })

    it('should auto-connect when disconnected', async () => {
      expect(client.isConnected()).toBe(false)

      // Mock reconnection
      fetchMock.mockResolvedValueOnce({
        ok: true,
        headers: { get: vi.fn().mockReturnValue('test-session-id-2') }
      } as any)
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}\n\n')
      } as any)
      fetchMock.mockResolvedValueOnce({ ok: true } as any)
      
      // Mock tool call
      fetchMock.mockResolvedValueOnce({
        ok: true,
        text: vi.fn().mockResolvedValue('data: {"jsonrpc":"2.0","result":{"message":"pong"}}\n\n')
      } as any)

      const result = await client.callTool('ping', {})

      expect(client.isConnected()).toBe(true)
      expect(result.success).toBe(true)
    })
  })

  describe('subscribeTo', () => {
    beforeEach(() => {
      // Mock EventSource
      global.EventSource = vi.fn().mockImplementation((url) => ({
        url,
        close: vi.fn()
      }))
    })

    it('should create EventSource with correct URL', () => {
      const events = ['server-status', 'app-updates']
      
      const eventSource = client.subscribeTo(events)

      expect(EventSource).toHaveBeenCalledWith(
        'http://localhost:8000/events?events=server-status,app-updates'
      )
      expect(eventSource).toBeDefined()
    })

    it('should close existing event source before creating new one', () => {
      const mockClose = vi.fn()
      global.EventSource = vi.fn().mockImplementation(() => ({
        close: mockClose
      }))

      client.subscribeTo(['event1'])
      client.subscribeTo(['event2'])

      expect(mockClose).toHaveBeenCalledTimes(1)
    })
  })
})