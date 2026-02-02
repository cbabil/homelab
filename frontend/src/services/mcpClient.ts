/**
 * MCP Client Implementation
 * 
 * Implements the Model Context Protocol client for frontend-backend communication.
 * Provides type-safe tool calling and real-time event subscription.
 */

import { MCPClient, MCPResponse } from '@/types/mcp'
import { mcpLogger } from '@/services/systemLogger'

export class TomoMCPClient implements MCPClient {
  private baseUrl: string
  private eventSource: EventSource | null = null
  private connected: boolean = false
  private sessionId: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '') // Remove trailing slash
    mcpLogger.info('MCP Client initialized', { baseUrl: this.baseUrl })
  }

  async connect(): Promise<void> {
    mcpLogger.info('Attempting to connect to MCP server', { url: this.baseUrl })

    try {
      // Initialize MCP protocol (stateless HTTP - no session required)
      const initResponse = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream'
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'initialize',
          params: {
            protocolVersion: '2024-11-05',
            capabilities: {
              roots: { listChanged: true },
              sampling: {}
            },
            clientInfo: {
              name: 'tomo-frontend',
              version: '1.0.0'
            }
          },
          id: 'init'
        })
      })

      if (!initResponse.ok) {
        throw new Error(`MCP initialization failed: ${initResponse.status} ${initResponse.statusText}`)
      }

      // Check for session ID in response (optional in stateless mode)
      const sessionId = initResponse.headers.get('mcp-session-id')
      if (sessionId) {
        this.sessionId = sessionId
        mcpLogger.info('MCP session ID received', { sessionId })
      }

      // Parse initialization response (JSON format in stateless mode)
      const initResult = await initResponse.json()

      if (initResult.error) {
        throw new Error(`MCP initialization error: ${initResult.error.message}`)
      }

      // Send initialized notification
      await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          ...(this.sessionId && { 'mcp-session-id': this.sessionId })
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'notifications/initialized',
          params: {}
        })
      })

      this.connected = true
      mcpLogger.info('MCP connection established successfully', {
        sessionId: this.sessionId,
        url: this.baseUrl
      })
    } catch (error) {
      this.connected = false
      this.sessionId = null
      mcpLogger.error('MCP connection failed', error)
      throw new Error(`Failed to connect to MCP server: ${error}`)
    }
  }

  private async resetConnection(): Promise<void> {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
      mcpLogger.info('Event source closed')
    }

    this.connected = false
    this.sessionId = null
    mcpLogger.info('MCP connection state reset')
  }

  async disconnect(): Promise<void> {
    mcpLogger.info('Disconnecting from MCP server', { 
      sessionId: this.sessionId,
      url: this.baseUrl 
    })

    await this.resetConnection()
    mcpLogger.info('MCP client disconnected')
  }

  async callTool<T>(name: string, params: Record<string, unknown>, attempt = 0): Promise<MCPResponse<T>> {
    if (!this.connected) {
      mcpLogger.info('Auto-connecting for tool call', { tool: name })
      await this.connect()
    }

    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name,
        arguments: params
      },
      id: `tool-call-${Date.now()}`
    }

    mcpLogger.info('Calling MCP tool', { tool: name, params })

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          ...(this.sessionId && { 'mcp-session-id': this.sessionId })
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        if (response.status === 400 && attempt === 0) {
          mcpLogger.warn('MCP request failed, attempting reconnect', {
            tool: name,
            status: response.status
          })

          await this.resetConnection()

          try {
            await this.connect()
          } catch (error) {
            mcpLogger.error('Reconnect attempt failed', {
              tool: name,
              error: error instanceof Error ? error.message : 'Unknown error'
            })
            throw new Error(`MCP reconnection failed: ${error instanceof Error ? error.message : error}`)
          }

          return await this.callTool<T>(name, params, attempt + 1)
        }

        throw new Error(`MCP call failed: ${response.status} ${response.statusText}`)
      }

      // Parse JSON response (stateless HTTP mode returns JSON directly)
      const result = await response.json()
      
      // Convert MCP JSON-RPC response to our internal format
      if (result.error) {
        mcpLogger.error('MCP tool call failed', { 
          tool: name, 
          error: result.error.message,
          code: result.error.code 
        })
        return {
          success: false,
          error: result.error.message || 'MCP call failed',
          message: result.error.message || 'MCP tool call failed'
        }
      }

      // MCP tool calls return: { content: [...], structuredContent: {...}, isError: boolean }
      // The actual tool response is in structuredContent
      const toolResult = result.result
      const actualData = toolResult?.structuredContent ?? toolResult?.content?.[0]?.text ?? toolResult

      mcpLogger.info('MCP tool call successful', {
        tool: name,
        resultType: typeof actualData,
        hasStructuredContent: !!toolResult?.structuredContent
      })
      return {
        success: true,
        data: actualData,
        message: 'Tool call successful'
      }

    } catch (error) {
      mcpLogger.error('MCP tool call exception', { 
        tool: name, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'MCP tool call failed'
      }
    }
  }

  subscribeTo(events: string[]): EventSource {
    const eventSourceUrl = `${this.baseUrl}/events?events=${events.join(',')}`
    
    mcpLogger.info('Subscribing to MCP events', { events, url: eventSourceUrl })
    
    if (this.eventSource) {
      mcpLogger.info('Closing existing event source')
      this.eventSource.close()
    }

    this.eventSource = new EventSource(eventSourceUrl)
    
    // Add event source logging
    this.eventSource.onopen = () => {
      mcpLogger.info('Event source connection opened')
    }
    
    this.eventSource.onerror = (error) => {
      mcpLogger.error('Event source error', error)
    }
    
    return this.eventSource
  }

  isConnected(): boolean {
    return this.connected
  }
}
