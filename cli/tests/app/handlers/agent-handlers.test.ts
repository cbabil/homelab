/**
 * Tests for agent command handlers.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

vi.mock('../../../src/lib/agent.js', () => ({
  installAgent: vi.fn(),
}));

import { handleAgentCommand } from '../../../src/app/handlers/agent-handlers.js';
import { installAgent } from '../../../src/lib/agent.js';

describe('agent-handlers', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient = {
      callTool: vi.fn(),
    };
  });

  describe('list', () => {
    it('should list agents', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agents: [
            { id: 'agent-1', server_id: 'srv-1', status: 'connected' },
          ],
        },
      });

      const results = await handleAgentCommand(mockClient as any, 'list', []);

      expect(mockClient.callTool).toHaveBeenCalledWith('list_agents', {});
      expect(results[0]!.content).toContain('1 agent(s)');
    });
  });

  describe('status', () => {
    it('should show agent status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'srv-1',
          status: 'connected',
          version: '1.0.0',
          last_seen: '2024-01-15',
        },
      });

      const results = await handleAgentCommand(mockClient as any, 'status', ['srv-1']);

      expect(mockClient.callTool).toHaveBeenCalledWith('get_agent_status', {
        server_id: 'srv-1',
      });
      expect(results.find((r) => r.content.includes('connected'))?.type).toBe('success');
    });

    it('should return error when missing server-id', async () => {
      const results = await handleAgentCommand(mockClient as any, 'status', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });

  describe('ping', () => {
    it('should ping an agent', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { success: true, latency_ms: 50 },
      });

      const results = await handleAgentCommand(mockClient as any, 'ping', ['srv-1']);

      expect(results[0]!.type).toBe('success');
      expect(results[0]!.content).toContain('Pong');
    });

    it('should return error when missing server-id', async () => {
      const results = await handleAgentCommand(mockClient as any, 'ping', []);

      expect(results[0]!.type).toBe('error');
    });
  });

  describe('rotate', () => {
    it('should rotate agent token', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agent_id: 'agent-1',
          server_id: 'srv-1',
          grace_period_seconds: 300,
          token_expires_at: '2024-01-15T12:00:00Z',
        },
      });

      const results = await handleAgentCommand(mockClient as any, 'rotate', ['srv-1']);

      expect(results[0]!.type).toBe('success');
      expect(results[0]!.content).toContain('Token rotation');
    });

    it('should return error when missing server-id', async () => {
      const results = await handleAgentCommand(mockClient as any, 'rotate', []);

      expect(results[0]!.type).toBe('error');
    });
  });

  describe('install', () => {
    it('should install an agent', async () => {
      vi.mocked(installAgent).mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', version: '1.0.0' },
        message: 'Installed',
      });

      const results = await handleAgentCommand(mockClient as any, 'install', ['srv-1']);

      expect(installAgent).toHaveBeenCalledWith('srv-1');
      expect(results[0]!.type).toBe('success');
      expect(results[0]!.content).toContain('Agent installed');
    });

    it('should handle install failure', async () => {
      vi.mocked(installAgent).mockResolvedValue({
        success: false,
        error: 'Server not found',
      });

      const results = await handleAgentCommand(mockClient as any, 'install', ['srv-1']);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Server not found');
    });

    it('should return error when missing server-id', async () => {
      const results = await handleAgentCommand(mockClient as any, 'install', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });

  describe('unknown subcommand', () => {
    it('should return error for unknown subcommand', async () => {
      const results = await handleAgentCommand(mockClient as any, 'unknown', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown agent subcommand');
    });

    it('should return usage when no subcommand', async () => {
      const results = await handleAgentCommand(mockClient as any, '', []);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });
});
