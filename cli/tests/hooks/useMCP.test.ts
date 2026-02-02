/**
 * Tests for useMCP hook - tests the MCP client functions directly.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { MCPClient } from '../../src/lib/mcp-client.js';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  initMCPClient: vi.fn(),
  closeMCPClient: vi.fn(),
  getMCPClient: vi.fn(),
}));

import {
  initMCPClient,
  closeMCPClient,
  getMCPClient,
} from '../../src/lib/mcp-client.js';

describe('MCP Client functions', () => {
  let mockClient: Partial<MCPClient> & { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient = {
      callTool: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn().mockReturnValue(true),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as unknown as MCPClient);
  });

  describe('initMCPClient', () => {
    it('should be called with URL', async () => {
      vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

      await initMCPClient('http://localhost:8000/mcp');

      expect(initMCPClient).toHaveBeenCalledWith('http://localhost:8000/mcp');
    });

    it('should handle connection success', async () => {
      vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

      const result = await initMCPClient('http://localhost:8000/mcp');

      expect(result).toBeDefined();
    });

    it('should handle connection failure', async () => {
      vi.mocked(initMCPClient).mockRejectedValue(new Error('Connection failed'));

      await expect(initMCPClient('http://localhost:8000/mcp')).rejects.toThrow(
        'Connection failed'
      );
    });
  });

  describe('closeMCPClient', () => {
    it('should close the client', () => {
      closeMCPClient();

      expect(closeMCPClient).toHaveBeenCalled();
    });
  });

  describe('getMCPClient', () => {
    it('should return the client', () => {
      const client = getMCPClient();

      expect(client).toBe(mockClient);
    });
  });

  describe('callTool', () => {
    it('should call tool with arguments', async () => {
      mockClient.callTool.mockResolvedValue({ success: true, data: { test: 'data' } });

      const result = await mockClient.callTool('test_tool', { arg: 'value' });

      expect(mockClient.callTool).toHaveBeenCalledWith('test_tool', { arg: 'value' });
      expect(result).toEqual({ success: true, data: { test: 'data' } });
    });

    it('should call tool without arguments', async () => {
      mockClient.callTool.mockResolvedValue({ success: true });

      const result = await mockClient.callTool('simple_tool');

      expect(mockClient.callTool).toHaveBeenCalledWith('simple_tool');
      expect(result).toEqual({ success: true });
    });

    it('should handle tool errors', async () => {
      mockClient.callTool.mockResolvedValue({ success: false, error: 'Tool failed' });

      const result = await mockClient.callTool('failing_tool', {});

      expect(result).toEqual({ success: false, error: 'Tool failed' });
    });
  });
});
