/**
 * Tests for CommandRouter module.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

import { routeCommand } from '../../src/app/CommandRouter.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';
import type { AppState } from '../../src/app/types.js';

describe('CommandRouter', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };
  let mockState: AppState;

  beforeEach(() => {
    mockClient = {
      callTool: vi.fn(),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);

    mockState = {
      mcpConnected: true,
      mcpUrl: 'http://localhost:8000/mcp',
      mcpConnecting: false,
      mcpError: null,
      authenticated: true,
      username: 'admin',
      history: [],
      inputValue: '',
      commandHistory: [],
      historyIndex: -1,
      isRunningCommand: false,
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('slash commands', () => {
    it('should handle /help command', async () => {
      const results = await routeCommand('/help', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].content).toContain('Available Commands');
    });

    it('should handle /h alias for help', async () => {
      const results = await routeCommand('/h', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].content).toContain('Available Commands');
    });

    it('should handle /? alias for help', async () => {
      const results = await routeCommand('/?', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].content).toContain('Available Commands');
    });

    it('should handle /clear command', async () => {
      const results = await routeCommand('/clear', mockState);

      expect(results).toHaveLength(1);
      expect(results[0].content).toBe('__CLEAR__');
    });

    it('should handle /cls alias for clear', async () => {
      const results = await routeCommand('/cls', mockState);

      expect(results).toHaveLength(1);
      expect(results[0].content).toBe('__CLEAR__');
    });

    it('should handle /quit command', async () => {
      const results = await routeCommand('/quit', mockState);

      expect(results).toHaveLength(1);
      expect(results[0].content).toBe('Goodbye!');
      expect(results[0].exit).toBe(true);
    });

    it('should handle /exit alias for quit', async () => {
      const results = await routeCommand('/exit', mockState);

      expect(results).toHaveLength(1);
      expect(results[0].exit).toBe(true);
    });

    it('should handle /q alias for quit', async () => {
      const results = await routeCommand('/q', mockState);

      expect(results).toHaveLength(1);
      expect(results[0].exit).toBe(true);
    });

    it('should handle /status command', async () => {
      const results = await routeCommand('/status', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].content).toContain('Connection Status');
    });

    it('should show connected status when connected', async () => {
      const results = await routeCommand('/status', mockState);

      const mcpStatus = results.find((r) => r.content.includes('MCP:'));
      expect(mcpStatus?.type).toBe('success');
    });

    it('should show disconnected status when not connected', async () => {
      mockState.mcpConnected = false;
      const results = await routeCommand('/status', mockState);

      const mcpStatus = results.find((r) => r.content.includes('MCP:'));
      expect(mcpStatus?.type).toBe('error');
    });

    it('should handle /logout command', async () => {
      const results = await routeCommand('/logout', mockState);

      expect(results.some((r) => r.content === '__LOGOUT__')).toBe(true);
      expect(results.some((r) => r.content.includes('Logged out'))).toBe(true);
    });

    it('should return error for unknown slash command', async () => {
      const results = await routeCommand('/unknown', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Unknown command');
    });
  });

  describe('/servers command', () => {
    it('should list servers when connected', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          servers: [
            { id: 'srv-1', name: 'Server 1', hostname: '192.168.1.10', status: 'online' },
          ],
        },
      });

      const results = await routeCommand('/servers', mockState);

      expect(results[0].content).toContain('1 server(s)');
    });

    it('should show no servers message when empty', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { servers: [] },
      });

      const results = await routeCommand('/servers', mockState);

      expect(results[0].content).toContain('No servers found');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/servers', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Not connected');
    });
  });

  describe('/agents command', () => {
    it('should list agents when connected', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agents: [
            { id: 'agent-1', server_id: 'srv-1', status: 'connected', version: '1.0.0' },
          ],
        },
      });

      const results = await routeCommand('/agents', mockState);

      expect(results[0].content).toContain('1 agent(s)');
    });

    it('should show no agents message when empty', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [] },
      });

      const results = await routeCommand('/agents', mockState);

      expect(results[0].content).toContain('No agents found');
    });
  });

  describe('regular commands', () => {
    it('should handle agent list command', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [] },
      });

      const results = await routeCommand('agent list', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('list_agents', {});
    });

    it('should handle agent status command', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'srv-1',
          status: 'connected',
          version: '1.0.0',
        },
      });

      const results = await routeCommand('agent status srv-1', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('get_agent_status', {
        server_id: 'srv-1',
      });
    });

    it('should show error when agent status missing server-id', async () => {
      const results = await routeCommand('agent status', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Usage:');
    });

    it('should handle agent ping command', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { success: true, latency_ms: 50 },
      });

      const results = await routeCommand('agent ping srv-1', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('ping_agent', {
        server_id: 'srv-1',
      });
      expect(results[0].type).toBe('success');
      expect(results[0].content).toContain('Pong');
    });

    it('should show error when agent ping missing server-id', async () => {
      const results = await routeCommand('agent ping', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Usage:');
    });

    it('should handle update command', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '1.0.0',
          update_available: false,
        },
      });

      const results = await routeCommand('update', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('check_updates', {});
    });

    it('should handle server list command', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { servers: [] },
      });

      const results = await routeCommand('server list', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('list_servers', {});
    });

    it('should return error for unknown command', async () => {
      const results = await routeCommand('unknown command', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Unknown command');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('agent list', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Not connected');
    });
  });

  describe('empty input', () => {
    it('should return empty array for empty input', async () => {
      const results = await routeCommand('', mockState);
      expect(results).toEqual([]);
    });

    it('should return empty array for whitespace-only input', async () => {
      const results = await routeCommand('   ', mockState);
      expect(results).toEqual([]);
    });
  });

  describe('case insensitivity', () => {
    it('should handle uppercase slash commands', async () => {
      const results = await routeCommand('/HELP', mockState);
      expect(results[0].content).toContain('Available Commands');
    });

    it('should handle mixed case regular commands', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [] },
      });

      await routeCommand('AGENT LIST', mockState);
      expect(mockClient.callTool).toHaveBeenCalledWith('list_agents', {});
    });
  });

  describe('/login command', () => {
    it('should return info about login requirements', async () => {
      const results = await routeCommand('/login', mockState);

      expect(results[0].type).toBe('info');
      expect(results[0].content).toContain('Login requires');
    });
  });

  describe('error handling', () => {
    it('should handle /servers error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection timeout',
      });

      const results = await routeCommand('/servers', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Connection timeout');
    });

    it('should handle /agents error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Permission denied',
      });

      const results = await routeCommand('/agents', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Permission denied');
    });

    it('should handle agent list error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Service unavailable',
      });

      const results = await routeCommand('agent list', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Service unavailable');
    });

    it('should handle agent status error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Agent not found',
      });

      const results = await routeCommand('agent status srv-1', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Agent not found');
    });

    it('should handle agent status with null data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null,
      });

      const results = await routeCommand('agent status srv-1', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('not found');
    });

    it('should handle agent ping error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Timeout',
      });

      const results = await routeCommand('agent ping srv-1', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Timeout');
    });

    it('should handle update error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Update check failed',
      });

      const results = await routeCommand('update', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Update check failed');
    });

    it('should handle server list error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Database error',
      });

      const results = await routeCommand('server list', mockState);

      expect(results[0].type).toBe('error');
    });
  });

  describe('agent subcommand edge cases', () => {
    it('should handle unknown agent subcommand', async () => {
      const results = await routeCommand('agent unknown', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Unknown agent subcommand');
    });

    it('should handle agent without subcommand', async () => {
      const results = await routeCommand('agent', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Usage:');
    });

    it('should display connected agent status with version', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'srv-1',
          status: 'connected',
          version: '2.0.0',
          last_seen: '2024-01-15',
        },
      });

      const results = await routeCommand('agent status srv-1', mockState);

      expect(results.find((r) => r.content.includes('connected'))?.type).toBe('success');
      expect(results.find((r) => r.content.includes('Version'))).toBeDefined();
    });

    it('should display disconnected agent status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'srv-1',
          status: 'disconnected',
          version: null,
          last_seen: null,
        },
      });

      const results = await routeCommand('agent status srv-1', mockState);

      expect(results.find((r) => r.content.includes('Status'))?.type).toBe('info');
      expect(results.find((r) => r.content.includes('unknown'))).toBeDefined();
    });
  });

  describe('server commands', () => {
    it('should handle unknown server subcommand', async () => {
      const results = await routeCommand('server unknown', mockState);

      expect(results[0].type).toBe('error');
    });

    it('should display servers with online status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          servers: [
            { id: 'srv-1', name: 'Server 1', hostname: '192.168.1.1', status: 'online' },
          ],
        },
      });

      const results = await routeCommand('server list', mockState);

      expect(results.find((r) => r.type === 'success')).toBeDefined();
    });

    it('should display servers with offline status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          servers: [
            { id: 'srv-1', name: 'Server 1', hostname: '192.168.1.1', status: 'offline' },
          ],
        },
      });

      const results = await routeCommand('server list', mockState);

      // Offline servers show as 'info' type
      expect(results.find((r) => r.type === 'info' && r.content.includes('srv-1'))).toBeDefined();
    });
  });

  describe('update command', () => {
    it('should display update available', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '2.0.0',
          update_available: true,
        },
      });

      const results = await routeCommand('update', mockState);

      expect(results.find((r) => r.content.includes('Update available'))).toBeDefined();
    });

    it('should display up to date', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '1.0.0',
          update_available: false,
        },
      });

      const results = await routeCommand('update', mockState);

      expect(results.find((r) => r.content.includes('latest version'))).toBeDefined();
    });
  });

  describe('exception handling', () => {
    it('should handle /servers exception', async () => {
      mockClient.callTool.mockRejectedValue(new Error('Network error'));

      const results = await routeCommand('/servers', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Network error');
    });

    it('should handle /agents exception', async () => {
      mockClient.callTool.mockRejectedValue(new Error('Connection refused'));

      const results = await routeCommand('/agents', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Connection refused');
    });
  });

  describe('edge cases', () => {
    it('should handle update with null data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null,
      });

      const results = await routeCommand('update', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('No update information');
    });

    it('should handle server without subcommand', async () => {
      const results = await routeCommand('server', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Usage:');
    });

    it('should handle update error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Update service unavailable',
      });

      const results = await routeCommand('update', mockState);

      expect(results[0].type).toBe('error');
      expect(results[0].content).toContain('Update service');
    });

    it('should display multiple agents in list', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agents: [
            { id: 'agent-1', server_id: 'srv-1', status: 'connected' },
            { id: 'agent-2', server_id: 'srv-2', status: 'disconnected' },
            { id: 'agent-3', server_id: 'srv-3', status: 'pending' },
          ],
        },
      });

      const results = await routeCommand('agent list', mockState);

      expect(results.length).toBeGreaterThan(1);
      expect(results.find((r) => r.content.includes('agent-1'))).toBeDefined();
      expect(results.find((r) => r.content.includes('agent-2'))).toBeDefined();
      expect(results.find((r) => r.content.includes('agent-3'))).toBeDefined();
    });
  });
});
