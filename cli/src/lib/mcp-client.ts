/**
 * MCP Client for CLI
 *
 * Connects to the Tomo MCP server and calls tools.
 */

export interface MCPResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
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

  constructor(options: MCPClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.timeout = options.timeout || 30000;
  }

  async connect(): Promise<void> {
    try {
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
              version: '1.0.0'
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
      const lines = initResponseText.split('\n');
      const dataLine = lines.find(line => line.startsWith('data: '));

      if (!dataLine) {
        throw new Error('Invalid MCP initialization response format');
      }

      const jsonData = dataLine.substring(6);
      const initResult = JSON.parse(jsonData);

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

  async callTool<T>(name: string, params: Record<string, unknown> = {}): Promise<MCPResponse<T>> {
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
      id: `tool-call-${Date.now()}`
    };

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream',
          'mcp-session-id': this.sessionId!
        },
        body: JSON.stringify(request),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        // Try reconnecting once on 400 error
        if (response.status === 400) {
          await this.disconnect();
          await this.connect();
          return this.callTool<T>(name, params);
        }
        throw new Error(`MCP call failed: ${response.status}`);
      }

      // Parse SSE response
      const responseText = await response.text();
      const lines = responseText.split('\n');
      const dataLine = lines.find(line => line.startsWith('data: '));

      if (!dataLine) {
        throw new Error('Invalid MCP response format');
      }

      const jsonData = dataLine.substring(6);
      const result = JSON.parse(jsonData);

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

  isConnected(): boolean {
    return this.connected;
  }
}

// Singleton instance
let mcpClient: MCPClient | null = null;

export function getMCPClient(baseUrl?: string): MCPClient {
  if (!mcpClient) {
    const url = baseUrl || process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp';
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
