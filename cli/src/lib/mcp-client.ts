/**
 * MCP Client for CLI
 *
 * Connects to the Tomo MCP server and calls tools.
 */

import { DEFAULT_MCP_URL } from './constants.js';

export interface MCPResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  httpStatus?: number;
}

export interface MCPClientOptions {
  baseUrl: string;
  timeout?: number;
}

export class MCPClient {
  private baseUrl: string;
  private sessionId: string | null = null;
  private connected: boolean = false;
  private timeout: number;
  private authTokenGetter: (() => string | null) | null = null;
  private tokenRefresher: (() => Promise<boolean>) | null = null;
  private forceLogoutHandler: (() => void) | null = null;

  constructor(options: MCPClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.timeout = options.timeout || 30000;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setAuthTokenGetter(getter: () => string | null): void {
    this.authTokenGetter = getter;
  }

  setTokenRefresher(refresher: () => Promise<boolean>): void {
    this.tokenRefresher = refresher;
  }

  setForceLogoutHandler(handler: () => void): void {
    this.forceLogoutHandler = handler;
  }

  async connect(): Promise<void> {
    try {
      // Block plaintext HTTP for remote servers — credentials would be sent in cleartext
      const parsed = new URL(this.baseUrl);
      const isLocal = ['localhost', '127.0.0.1', '::1'].includes(parsed.hostname);
      if (parsed.protocol === 'http:' && !isLocal) {
        throw new Error(
          'Refusing to connect to remote MCP server over plaintext HTTP. Use HTTPS for non-local servers.'
        );
      }

      // Establish session to get session ID
      const sessionResponse = await fetch(this.baseUrl, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream'
        },
        signal: AbortSignal.timeout(this.timeout)
      });

      const sessionId = sessionResponse.headers.get('mcp-session-id');
      if (!sessionId) {
        throw new Error('Failed to get session ID from MCP server');
      }

      this.sessionId = sessionId;

      // Initialize MCP protocol
      const initResponse = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          'mcp-session-id': this.sessionId
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
              name: 'tomo-cli',
              version: '0.1.0'
            }
          },
          id: 'init'
        }),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!initResponse.ok) {
        throw new Error(`MCP initialization failed: ${initResponse.status}`);
      }

      // Parse initialization response
      const initResponseText = await initResponse.text();
      const initDataLine = parseSSEDataLine(initResponseText);

      if (!initDataLine) {
        throw new Error('Invalid MCP initialization response format');
      }

      const initResult = JSON.parse(initDataLine);

      if (initResult.error) {
        throw new Error(`MCP initialization error: ${initResult.error.message}`);
      }

      // Send initialized notification
      await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          'mcp-session-id': this.sessionId
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'notifications/initialized',
          params: {}
        }),
        signal: AbortSignal.timeout(this.timeout)
      });

      this.connected = true;
    } catch (error) {
      this.connected = false;
      this.sessionId = null;
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    this.sessionId = null;
  }

  async callToolRaw<T>(
    name: string,
    params: Record<string, unknown> = {},
    retryCount: number = 0
  ): Promise<MCPResponse<T>> {
    if (!this.connected || !this.sessionId) {
      await this.connect();
    }

    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name,
        arguments: params
      },
      id: `tool-call-${crypto.randomUUID()}`
    };

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'mcp-session-id': this.sessionId!,
      };

      const token = this.authTokenGetter?.();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        // Try reconnecting once on 400 error (max 1 retry)
        if (response.status === 400 && retryCount < 1) {
          await this.disconnect();
          await this.connect();
          return this.callToolRaw<T>(name, params, retryCount + 1);
        }
        // Return structured error with httpStatus instead of throwing,
        // so callTool can inspect the status code for 401 handling.
        return {
          success: false,
          error: `MCP call failed: ${response.status}`,
          message: 'MCP tool call failed',
          httpStatus: response.status,
        };
      }

      // Parse SSE response
      const responseText = await response.text();
      const dataLine = parseSSEDataLine(responseText);

      if (!dataLine) {
        throw new Error('Invalid MCP response format');
      }

      const result = JSON.parse(dataLine);

      if (result.error) {
        return {
          success: false,
          error: result.error.message || 'MCP call failed',
          message: result.error.message
        };
      }

      // Extract tool result
      const toolResult = result.result;
      const actualData = toolResult?.structuredContent ?? toolResult?.content?.[0]?.text ?? toolResult;

      return {
        success: true,
        data: actualData,
        message: 'Tool call successful'
      };

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      return {
        success: false,
        error: message,
        message: 'MCP tool call failed'
      };
    }
  }

  async callTool<T>(
    name: string,
    params: Record<string, unknown> = {}
  ): Promise<MCPResponse<T>> {
    const result = await this.callToolRaw<T>(name, params);

    if (!result.success && result.httpStatus === 401) {
      if (this.tokenRefresher) {
        const refreshed = await this.tokenRefresher();
        if (refreshed) {
          // retryCount=1 prevents the 400-reconnect path from firing on the
          // retried request, avoiding infinite retry loops after a refresh.
          return this.callToolRaw<T>(name, params, 1);
        }
        this.forceLogoutHandler?.();
      }
    }

    return result;
  }

  isConnected(): boolean {
    return this.connected;
  }
}

/**
 * Parse SSE data line from response text.
 * Handles `data:` with or without trailing space.
 */
function parseSSEDataLine(responseText: string): string | null {
  const lines = responseText.split('\n');
  const dataLine = lines.find(line => line.startsWith('data:'));

  if (!dataLine) {
    return null;
  }

  // Strip 'data:' prefix and trim leading whitespace
  return dataLine.substring(5).trimStart();
}

// Singleton instance
let mcpClient: MCPClient | null = null;

export function getMCPClient(baseUrl?: string): MCPClient {
  const url = baseUrl || DEFAULT_MCP_URL;

  // If client exists but URL differs, close old and create new
  if (mcpClient && mcpClient.getBaseUrl() !== url.replace(/\/$/, '')) {
    void mcpClient.disconnect();
    mcpClient = null;
  }

  if (!mcpClient) {
    mcpClient = new MCPClient({ baseUrl: url });
  }

  return mcpClient;
}

export async function initMCPClient(baseUrl?: string): Promise<MCPClient> {
  const client = getMCPClient(baseUrl);
  await client.connect();
  return client;
}

export function closeMCPClient(): void {
  if (mcpClient) {
    mcpClient.disconnect();
    mcpClient = null;
  }
}
