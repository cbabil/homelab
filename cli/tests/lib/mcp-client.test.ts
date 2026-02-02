/**
 * Tests for MCP Client module.
 *
 * Tests the MCPClient class and singleton helper functions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Import after mocks
import { MCPClient, getMCPClient, initMCPClient, closeMCPClient } from '../../src/lib/mcp-client.js';

describe('mcp-client module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    closeMCPClient(); // Reset singleton between tests
  });

  afterEach(() => {
    closeMCPClient();
  });

  describe('MCPClient constructor', () => {
    it('should set baseUrl correctly', () => {
      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      expect(client).toBeDefined();
    });

    it('should strip trailing slash from baseUrl', () => {
      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp/' });
      expect(client).toBeDefined();
    });

    it('should use default timeout of 30000ms', () => {
      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      expect(client).toBeDefined();
    });

    it('should accept custom timeout', () => {
      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp', timeout: 60000 });
      expect(client).toBeDefined();
    });
  });

  describe('MCPClient connect', () => {
    it('should connect successfully when server responds with session ID', async () => {
      // First call: GET to establish session
      mockFetch.mockResolvedValueOnce({
        headers: new Map([['mcp-session-id', 'test-session-123']]),
        ok: true
      });

      // Second call: POST to initialize
      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"capabilities":{}},"id":"init"}')
      });

      // Third call: POST to send initialized notification
      mockFetch.mockResolvedValueOnce({
        ok: true
      });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      expect(client.isConnected()).toBe(true);
    });

    it('should throw error when session ID is not returned', async () => {
      mockFetch.mockResolvedValueOnce({
        headers: new Map(),
        ok: true
      });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });

      await expect(client.connect()).rejects.toThrow('Failed to get session ID');
    });

    it('should throw error when init response is not ok', async () => {
      mockFetch.mockResolvedValueOnce({
        headers: new Map([['mcp-session-id', 'test-session']]),
        ok: true
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });

      await expect(client.connect()).rejects.toThrow('MCP initialization failed: 500');
    });

    it('should set connected to false on connection error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });

      await expect(client.connect()).rejects.toThrow('Network error');
      expect(client.isConnected()).toBe(false);
    });

    it('should throw error when init response has no data line', async () => {
      mockFetch.mockResolvedValueOnce({
        headers: new Map([['mcp-session-id', 'test-session']]),
        ok: true
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('event: message\nno data line here')
      });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });

      await expect(client.connect()).rejects.toThrow('Invalid MCP initialization response format');
    });

    it('should throw error when init result contains error', async () => {
      mockFetch.mockResolvedValueOnce({
        headers: new Map([['mcp-session-id', 'test-session']]),
        ok: true
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","error":{"message":"Server error"},"id":"init"}')
      });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });

      await expect(client.connect()).rejects.toThrow('MCP initialization error: Server error');
    });
  });

  describe('MCPClient disconnect', () => {
    it('should set connected to false', async () => {
      // Set up successful connection first
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();
      expect(client.isConnected()).toBe(true);

      await client.disconnect();
      expect(client.isConnected()).toBe(false);
    });
  });

  describe('MCPClient callTool', () => {
    it('should auto-connect if not connected', async () => {
      // Connection calls
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        })
        // Tool call
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"content":[{"text":"success"}]},"id":"tool-1"}')
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      const result = await client.callTool('test_tool');

      expect(result.success).toBe(true);
    });

    it('should return success response for successful tool call', async () => {
      // Set up connection
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      // Tool call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"structuredContent":{"key":"value"}},"id":"tool-1"}')
      });

      const result = await client.callTool('test_tool', { param: 'value' });

      expect(result.success).toBe(true);
      expect(result.data).toEqual({ key: 'value' });
    });

    it('should return error response when tool returns error', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","error":{"message":"Tool failed"},"id":"tool-1"}')
      });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Tool failed');
    });

    it('should return error response on fetch failure', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });

    it('should reconnect on 400 error and retry', async () => {
      // Initial connection
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session-1']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      // First tool call returns 400 - should trigger reconnect
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 400
        })
        // Reconnection sequence
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session-2']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        })
        // Retry tool call
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"structuredContent":{"success":true}},"id":"tool-1"}')
        });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(true);
    });

    it('should throw error on non-400 HTTP error', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(false);
      expect(result.error).toBe('MCP call failed: 500');
    });

    it('should handle response without data line', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('event: message\nno-data-here')
      });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid MCP response format');
    });

    it('should handle text content in response', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"content":[{"text":"Hello World"}]},"id":"tool-1"}')
      });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(true);
      expect(result.data).toBe('Hello World');
    });

    it('should fallback to full result when no structured or text content', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      await client.connect();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{"custom":"data"},"id":"tool-1"}')
      });

      const result = await client.callTool('test_tool');

      expect(result.success).toBe(true);
      expect(result.data).toEqual({ custom: 'data' });
    });
  });

  describe('MCPClient isConnected', () => {
    it('should return false initially', () => {
      const client = new MCPClient({ baseUrl: 'http://localhost:8000/mcp' });
      expect(client.isConnected()).toBe(false);
    });
  });

  describe('getMCPClient', () => {
    it('should return an MCPClient instance', () => {
      const client = getMCPClient('http://localhost:8000/mcp');
      expect(client).toBeInstanceOf(MCPClient);
    });

    it('should return same instance on subsequent calls', () => {
      const client1 = getMCPClient('http://localhost:8000/mcp');
      const client2 = getMCPClient('http://localhost:8000/mcp');
      expect(client1).toBe(client2);
    });

    it('should use MCP_SERVER_URL environment variable when no baseUrl provided', () => {
      process.env.MCP_SERVER_URL = 'http://env-server:8000/mcp';
      closeMCPClient(); // Reset singleton

      const client = getMCPClient();
      expect(client).toBeInstanceOf(MCPClient);

      delete process.env.MCP_SERVER_URL;
    });

    it('should use default URL when no baseUrl or env var', () => {
      delete process.env.MCP_SERVER_URL;
      closeMCPClient();

      const client = getMCPClient();
      expect(client).toBeInstanceOf(MCPClient);
    });
  });

  describe('initMCPClient', () => {
    it('should return connected client', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const client = await initMCPClient('http://localhost:8000/mcp');
      expect(client.isConnected()).toBe(true);
    });
  });

  describe('closeMCPClient', () => {
    it('should disconnect and reset singleton', async () => {
      mockFetch
        .mockResolvedValueOnce({
          headers: new Map([['mcp-session-id', 'test-session']]),
          ok: true
        })
        .mockResolvedValueOnce({
          ok: true,
          text: () => Promise.resolve('data: {"jsonrpc":"2.0","result":{},"id":"init"}')
        })
        .mockResolvedValueOnce({
          ok: true
        });

      await initMCPClient('http://localhost:8000/mcp');

      closeMCPClient();

      // Next call should create new instance
      const newClient = getMCPClient('http://localhost:8000/mcp');
      expect(newClient.isConnected()).toBe(false);
    });

    it('should be safe to call when not initialized', () => {
      expect(() => closeMCPClient()).not.toThrow();
    });
  });
});
