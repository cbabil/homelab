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
import {
  listAgents,
  installAgent,
  uninstallAgent,
  getAgentStatus,
  revokeAgent,
  pingAgent,
  checkAgentHealth,
  checkAgentVersion,
  triggerAgentUpdate,
  listStaleAgents,
  resetAgentStatus,
} from '../../src/lib/agent.js';

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
      expect(result[0].id).toBe('agent-1');
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

  describe('uninstallAgent', () => {
    it('should return success when uninstalled', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1' },
        message: 'Agent uninstalled',
      });

      const result = await uninstallAgent('server-1');

      expect(result.success).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledWith('uninstall_agent', {
        server_id: 'server-1',
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not found',
      });

      const result = await uninstallAgent('invalid');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Agent not found');
    });

    it('should handle missing error message', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
      });

      const result = await uninstallAgent('invalid');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to uninstall agent');
    });
  });

  describe('getAgentStatus', () => {
    it('should return agent status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'server-1',
          status: 'connected',
          is_connected: true,
          version: '1.0.0',
        },
      });

      const result = await getAgentStatus('server-1');

      expect(result).not.toBeNull();
      expect(result?.id).toBe('agent-1');
      expect(result?.is_connected).toBe(true);
    });

    it('should return null when no agent found', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not found',
      });

      const result = await getAgentStatus('invalid');

      expect(result).toBeNull();
    });
  });

  describe('revokeAgent', () => {
    it('should return success when revoked', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1' },
        message: 'Agent revoked',
      });

      const result = await revokeAgent('server-1');

      expect(result.success).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledWith('revoke_agent_token', {
        server_id: 'server-1',
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not found',
      });

      const result = await revokeAgent('invalid');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Agent not found');
    });
  });

  describe('pingAgent', () => {
    it('should return ping result', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agent_id: 'agent-1',
          responsive: true,
          latency_ms: 50.5,
        },
      });

      const result = await pingAgent('server-1', 5);

      expect(result).not.toBeNull();
      expect(result?.responsive).toBe(true);
      expect(result?.latency_ms).toBe(50.5);
    });

    it('should use default timeout', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', responsive: true, latency_ms: 10 },
      });

      await pingAgent('server-1');

      expect(mockClient.callTool).toHaveBeenCalledWith('ping_agent', {
        server_id: 'server-1',
        timeout: 5,
      });
    });

    it('should return null on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not connected',
      });

      const result = await pingAgent('server-1');

      expect(result).toBeNull();
    });
  });

  describe('checkAgentHealth', () => {
    it('should return health data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agent_id: 'agent-1',
          server_id: 'server-1',
          status: 'connected',
          health: 'healthy',
          is_connected: true,
          is_stale: false,
          version: '1.0.0',
        },
      });

      const result = await checkAgentHealth('server-1');

      expect(result).not.toBeNull();
      expect(result?.health).toBe('healthy');
    });

    it('should return null on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not found',
      });

      const result = await checkAgentHealth('invalid');

      expect(result).toBeNull();
    });
  });

  describe('checkAgentVersion', () => {
    it('should return version info', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '1.1.0',
          update_available: true,
        },
      });

      const result = await checkAgentVersion('server-1');

      expect(result).not.toBeNull();
      expect(result?.update_available).toBe(true);
    });

    it('should return null on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Version unknown',
      });

      const result = await checkAgentVersion('invalid');

      expect(result).toBeNull();
    });
  });

  describe('triggerAgentUpdate', () => {
    it('should return success when update triggered', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', status: 'updating' },
        message: 'Update triggered',
      });

      const result = await triggerAgentUpdate('server-1');

      expect(result.success).toBe(true);
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Already at latest version',
      });

      const result = await triggerAgentUpdate('server-1');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Already at latest version');
    });
  });

  describe('listStaleAgents', () => {
    it('should return stale agents', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          stale_count: 1,
          agents: [
            {
              agent_id: 'agent-1',
              server_id: 'server-1',
              last_heartbeat: '2024-01-01T00:00:00Z',
            },
          ],
        },
      });

      const result = await listStaleAgents();

      expect(result).not.toBeNull();
      expect(result?.stale_count).toBe(1);
    });

    it('should return null on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Lifecycle manager unavailable',
      });

      const result = await listStaleAgents();

      expect(result).toBeNull();
    });
  });

  describe('resetAgentStatus', () => {
    it('should reset specific agent', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', reset_count: 1 },
        message: 'Agent status reset',
      });

      const result = await resetAgentStatus('server-1');

      expect(result.success).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledWith('reset_agent_status', {
        server_id: 'server-1',
      });
    });

    it('should reset all agents when no server ID', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { reset_count: 5 },
        message: 'Reset 5 agents',
      });

      const result = await resetAgentStatus();

      expect(result.success).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledWith('reset_agent_status', {});
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent is connected',
      });

      const result = await resetAgentStatus('server-1');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Agent is connected');
    });
  });
});
