/**
 * Tests for agent module.
 *
 * Tests agent lifecycle operations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

import { getMCPClient } from '../../src/lib/mcp-client.js';
import { listAgents, installAgent } from '../../src/lib/agent.js';

describe('Agent Module', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockClient = {
      callTool: vi.fn(),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('listAgents', () => {
    it('should return empty array when no agents', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [], count: 0 },
      });

      const result = await listAgents();

      expect(result).toEqual([]);
      expect(mockClient.callTool).toHaveBeenCalledWith('list_agents', {});
    });

    it('should return agents list', async () => {
      const mockAgents = [
        {
          id: 'agent-1',
          server_id: 'server-1',
          status: 'connected',
          version: '1.0.0',
          last_seen: '2024-01-01T00:00:00Z',
          registered_at: '2024-01-01T00:00:00Z',
        },
      ];

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: mockAgents, count: 1 },
      });

      const result = await listAgents();

      expect(result).toHaveLength(1);
      expect(result[0]!.id).toBe('agent-1');
    });

    it('should return empty array on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection failed',
      });

      const result = await listAgents();

      expect(result).toEqual([]);
    });
  });

  describe('installAgent', () => {
    it('should return success with agent data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', version: '1.0.0' },
        message: 'Agent installed',
      });

      const result = await installAgent('server-1');

      expect(result.success).toBe(true);
      expect(result.data?.agent_id).toBe('agent-1');
      expect(mockClient.callTool).toHaveBeenCalledWith('install_agent', {
        server_id: 'server-1',
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Server not found',
      });

      const result = await installAgent('invalid');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Server not found');
    });

    it('should handle missing error message', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
      });

      const result = await installAgent('invalid');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to install agent');
    });
  });
});
