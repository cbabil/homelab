/**
 * Tests for CommandRouter module.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

// Mock security lib for /security commands
vi.mock('../../src/lib/security.js', () => ({
  getLockedAccounts: vi.fn(),
  unlockAccount: vi.fn(),
}));

// Mock agent lib for /agent install
vi.mock('../../src/lib/agent.js', () => ({
  installAgent: vi.fn(),
}));

import { routeCommand } from '../../src/app/CommandRouter.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';
import { getLockedAccounts, unlockAccount } from '../../src/lib/security.js';
import { installAgent } from '../../src/lib/agent.js';
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
      expect(results[0]!.content).toContain('Available Commands');
    });

    it('should handle /h alias for help', async () => {
      const results = await routeCommand('/h', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0]!.content).toContain('Available Commands');
    });

    it('should handle /? alias for help', async () => {
      const results = await routeCommand('/?', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0]!.content).toContain('Available Commands');
    });

    it('should handle /clear command', async () => {
      const results = await routeCommand('/clear', mockState);

      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('__CLEAR__');
    });

    it('should handle /cls alias for clear', async () => {
      const results = await routeCommand('/cls', mockState);

      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('__CLEAR__');
    });

    it('should handle /quit command', async () => {
      const results = await routeCommand('/quit', mockState);

      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('Goodbye!');
      expect(results[0]!.exit).toBe(true);
    });

    it('should handle /exit alias for quit', async () => {
      const results = await routeCommand('/exit', mockState);

      expect(results).toHaveLength(1);
      expect(results[0]!.exit).toBe(true);
    });

    it('should handle /q alias for quit', async () => {
      const results = await routeCommand('/q', mockState);

      expect(results).toHaveLength(1);
      expect(results[0]!.exit).toBe(true);
    });

    it('should handle /status command', async () => {
      const results = await routeCommand('/status', mockState);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0]!.content).toContain('Connection Status');
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

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown command');
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

      expect(results[0]!.content).toContain('1 server(s)');
    });

    it('should show no servers message when empty', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { servers: [] },
      });

      const results = await routeCommand('/servers', mockState);

      expect(results[0]!.content).toContain('No servers found');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/servers', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
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

      expect(results[0]!.content).toContain('1 agent(s)');
    });

    it('should show no agents message when empty', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [] },
      });

      const results = await routeCommand('/agents', mockState);

      expect(results[0]!.content).toContain('No agents found');
    });
  });

  describe('/agent slash command', () => {
    it('should handle /agent list', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { agents: [] },
      });

      const results = await routeCommand('/agent list', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('list_agents', {});
    });

    it('should handle /agent status', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: 'agent-1',
          server_id: 'srv-1',
          status: 'connected',
          version: '1.0.0',
        },
      });

      const results = await routeCommand('/agent status srv-1', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('get_agent_status', {
        server_id: 'srv-1',
      });
    });

    it('should show error when agent status missing server-id', async () => {
      const results = await routeCommand('/agent status', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should handle /agent ping', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { success: true, latency_ms: 50 },
      });

      const results = await routeCommand('/agent ping srv-1', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('ping_agent', {
        server_id: 'srv-1',
      });
      expect(results[0]!.type).toBe('success');
      expect(results[0]!.content).toContain('Pong');
    });

    it('should handle /agent rotate', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          agent_id: 'agent-1',
          server_id: 'srv-1',
          grace_period_seconds: 300,
          token_expires_at: '2024-01-15T12:00:00Z',
        },
      });

      const results = await routeCommand('/agent rotate srv-1', mockState);

      expect(results[0]!.type).toBe('success');
    });

    it('should handle /agent install', async () => {
      vi.mocked(installAgent).mockResolvedValue({
        success: true,
        data: { agent_id: 'agent-1', version: '1.0.0' },
        message: 'Installed',
      });

      const results = await routeCommand('/agent install srv-1', mockState);

      expect(installAgent).toHaveBeenCalledWith('srv-1');
      expect(results[0]!.type).toBe('success');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/agent list', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });

    it('should handle unknown agent subcommand', async () => {
      const results = await routeCommand('/agent unknown', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown agent subcommand');
    });

    it('should handle /agent without subcommand', async () => {
      const results = await routeCommand('/agent', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });

  describe('/server slash command', () => {
    it('should handle /server list', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { servers: [] },
      });

      const results = await routeCommand('/server list', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('list_servers', {});
    });

    it('should handle unknown server subcommand', async () => {
      const results = await routeCommand('/server unknown', mockState);

      expect(results[0]!.type).toBe('error');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/server list', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });
  });

  describe('/update slash command', () => {
    it('should handle /update', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '1.0.0',
          update_available: false,
        },
      });

      const results = await routeCommand('/update', mockState);

      expect(mockClient.callTool).toHaveBeenCalledWith('check_updates', {});
    });

    it('should display update available', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          current_version: '1.0.0',
          latest_version: '2.0.0',
          update_available: true,
        },
      });

      const results = await routeCommand('/update', mockState);

      expect(results.find((r) => r.content.includes('Update available'))).toBeDefined();
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/update', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });
  });

  describe('/security slash command', () => {
    it('should handle /security list-locked', async () => {
      vi.mocked(getLockedAccounts).mockResolvedValue([]);

      const results = await routeCommand('/security list-locked', mockState);

      expect(getLockedAccounts).toHaveBeenCalled();
      expect(results[0]!.content).toContain('No locked accounts');
    });

    it('should handle /security unlock', async () => {
      vi.mocked(unlockAccount).mockResolvedValue({ success: true, lock_id: 'lock-1' });

      const results = await routeCommand('/security unlock lock-1', mockState);

      expect(unlockAccount).toHaveBeenCalledWith('lock-1', 'admin', undefined);
      expect(results[0]!.type).toBe('success');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/security list-locked', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });
  });

  describe('/backup slash command', () => {
    it('should handle /backup export', async () => {
      const results = await routeCommand('/backup export', mockState);

      expect(results[0]!.content).toBe('__BACKUP_EXPORT__./backup.enc');
    });

    it('should handle /backup export with path', async () => {
      const results = await routeCommand('/backup export /tmp/bk.enc', mockState);

      expect(results[0]!.content).toBe('__BACKUP_EXPORT__/tmp/bk.enc');
    });

    it('should handle /backup import', async () => {
      const results = await routeCommand('/backup import /tmp/bk.enc', mockState);

      expect(results[0]!.content).toBe('__BACKUP_IMPORT__/tmp/bk.enc');
    });

    it('should handle /backup import --overwrite', async () => {
      const results = await routeCommand('/backup import /tmp/bk.enc --overwrite', mockState);

      expect(results[0]!.content).toBe('__BACKUP_IMPORT_OVERWRITE__/tmp/bk.enc');
    });

    it('should return error when import path missing', async () => {
      const results = await routeCommand('/backup import', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/backup export', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });
  });

  describe('/user slash command', () => {
    it('should handle /user reset-password', async () => {
      const results = await routeCommand('/user reset-password john', mockState);

      expect(results[0]!.content).toBe('__RESET_PASSWORD__john');
    });

    it('should return error when username missing', async () => {
      const results = await routeCommand('/user reset-password', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should return error when not connected', async () => {
      mockState.mcpConnected = false;

      const results = await routeCommand('/user reset-password john', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Not connected');
    });
  });

  describe('/admin slash command', () => {
    it('should handle /admin create', async () => {
      const results = await routeCommand('/admin create', mockState);

      expect(results[0]!.content).toBe('__SETUP__');
    });

    it('should return error for unknown admin subcommand', async () => {
      const results = await routeCommand('/admin unknown', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown admin subcommand');
    });

    it('should return usage when no subcommand', async () => {
      const results = await routeCommand('/admin', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should sanitize admin subcommand in error message', async () => {
      const results = await routeCommand('/admin \x1b[31mmalicious\x1b[0m', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('malicious');
      expect(results[0]!.content).not.toContain('\x1b[');
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

  describe('non-slash input', () => {
    it('should return error for input without slash prefix', async () => {
      const results = await routeCommand('agent list', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown input');
      expect(results[1]!.content).toContain('/help');
    });

    it('should return error for unknown regular command', async () => {
      const results = await routeCommand('unknown command', mockState);

      expect(results[0]!.type).toBe('error');
    });
  });

  describe('case insensitivity', () => {
    it('should handle uppercase slash commands', async () => {
      const results = await routeCommand('/HELP', mockState);
      expect(results[0]!.content).toContain('Available Commands');
    });
  });

  describe('/login command', () => {
    it('should return __LOGIN__ signal', async () => {
      const results = await routeCommand('/login', mockState);

      expect(results[0]!.type).toBe('system');
      expect(results[0]!.content).toBe('__LOGIN__');
    });
  });

  describe('/view command', () => {
    it('should handle /view with valid view name', async () => {
      const results = await routeCommand('/view agents', mockState);
      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('__VIEW__agents');
    });

    it('should handle /view with all valid views', async () => {
      for (const view of ['dashboard', 'agents', 'logs', 'settings']) {
        const results = await routeCommand(`/view ${view}`, mockState);
        expect(results[0]!.content).toBe(`__VIEW__${view}`);
      }
    });

    it('should reject /view with invalid view name', async () => {
      const results = await routeCommand('/view invalid', mockState);
      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should reject /view without argument', async () => {
      const results = await routeCommand('/view', mockState);
      expect(results[0]!.type).toBe('error');
    });
  });

  describe('/refresh command', () => {
    it('should handle /refresh command', async () => {
      const results = await routeCommand('/refresh', mockState);
      expect(results).toHaveLength(1);
      expect(results[0]!.content).toBe('__REFRESH__');
    });
  });

  describe('error handling', () => {
    it('should handle /servers error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection timeout',
      });

      const results = await routeCommand('/servers', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Connection timeout');
    });

    it('should handle /agents error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Permission denied',
      });

      const results = await routeCommand('/agents', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Permission denied');
    });

    it('should handle /agent list error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Service unavailable',
      });

      const results = await routeCommand('/agent list', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Service unavailable');
    });

    it('should handle /update error response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Update check failed',
      });

      const results = await routeCommand('/update', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Update check failed');
    });
  });

  describe('exception handling', () => {
    it('should handle /servers exception', async () => {
      mockClient.callTool.mockRejectedValue(new Error('Network error'));

      const results = await routeCommand('/servers', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Network error');
    });

    it('should handle /agents exception', async () => {
      mockClient.callTool.mockRejectedValue(new Error('Connection refused'));

      const results = await routeCommand('/agents', mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Connection refused');
    });
  });

  describe('auth enforcement', () => {
    const privilegedCommands = [
      '/servers',
      '/agents',
      '/agent list',
      '/server list',
      '/update',
      '/security list-locked',
      '/backup export',
      '/user reset-password john',
    ];

    it.each(privilegedCommands)(
      'should require auth for %s when not authenticated',
      async (cmd) => {
        const unauthState = { ...mockState, authenticated: false };
        const results = await routeCommand(cmd, unauthState);

        expect(results[0]!.type).toBe('error');
        expect(results[0]!.content).toContain('Authentication required');
      }
    );

    it.each(privilegedCommands)(
      'should require connection for %s when not connected',
      async (cmd) => {
        const disconnectedState = { ...mockState, mcpConnected: false, authenticated: false };
        const results = await routeCommand(cmd, disconnectedState);

        expect(results[0]!.type).toBe('error');
        expect(results[0]!.content).toContain('Not connected');
      }
    );

    it('should NOT require auth for /help', async () => {
      const unauthState = { ...mockState, authenticated: false };
      const results = await routeCommand('/help', unauthState);
      expect(results[0]!.content).toContain('Available Commands');
    });

    it('should NOT require auth for /status', async () => {
      const unauthState = { ...mockState, authenticated: false };
      const results = await routeCommand('/status', unauthState);
      expect(results[0]!.content).toContain('Connection Status');
    });

    it('should NOT require auth for /login', async () => {
      const unauthState = { ...mockState, authenticated: false };
      const results = await routeCommand('/login', unauthState);
      expect(results[0]!.content).toBe('__LOGIN__');
    });

    it('should NOT require auth for /admin create', async () => {
      const unauthState = { ...mockState, authenticated: false };
      const results = await routeCommand('/admin create', unauthState);
      expect(results[0]!.content).toBe('__SETUP__');
    });
  });

  describe('help lists all commands', () => {
    it('should list management commands in help', async () => {
      const results = await routeCommand('/help', mockState);
      const allContent = results.map((r) => r.content).join('\n');

      expect(allContent).toContain('/agent');
      expect(allContent).toContain('/server');
      expect(allContent).toContain('/update');
      expect(allContent).toContain('/security');
      expect(allContent).toContain('/backup');
      expect(allContent).toContain('/user');
      expect(allContent).toContain('/admin');
    });
  });
});
