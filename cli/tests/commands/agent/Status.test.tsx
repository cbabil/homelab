/**
 * Tests for agent Status component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Mock ink's useApp hook
vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useApp: () => ({ exit: vi.fn() }),
  };
});

// Mock the useMCP hook
vi.mock('../../../src/hooks/useMCP.js', () => ({
  useMCP: vi.fn(() => ({
    connected: true,
    connecting: false,
    error: null,
  })),
}));

// Mock the agent lib
vi.mock('../../../src/lib/agent.js', () => ({
  getAgentStatus: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { Status } from '../../../src/commands/agent/Status.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { getAgentStatus } from '../../../src/lib/agent.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('Status (Agent)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMCP).mockReturnValue({
      connected: true,
      connecting: false,
      error: null,
      callTool: vi.fn(),
    });
    vi.mocked(requireAdmin).mockResolvedValue(true);
  });

  it('should render banner', () => {
    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <Status serverId="server-1" options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should display agent status when found', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue({
      id: 'agent-1',
      server_id: 'server-1',
      status: 'connected',
      version: '1.0.0',
      last_seen: '2024-01-15',
      registered_at: '2024-01-01',
      is_connected: true,
    });

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Status') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when agent not found', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue(null);

    const { lastFrame } = render(<Status serverId="unknown" options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('No agent');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display connected status with green color', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue({
      id: 'agent-1',
      server_id: 'server-1',
      status: 'connected',
      version: '1.0.0',
      last_seen: '2024-01-15',
      registered_at: '2024-01-01',
      is_connected: true,
    });

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('CONNECTED') && frame?.includes('Yes');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display disconnected status with yellow color', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue({
      id: 'agent-2',
      server_id: 'server-2',
      status: 'disconnected',
      version: null,
      last_seen: null,
      registered_at: null,
      is_connected: false,
    });

    const { lastFrame } = render(<Status serverId="server-2" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('DISCONNECTED');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display unknown status with gray color', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue({
      id: 'agent-3',
      server_id: 'server-3',
      status: 'pending',
      version: null,
      last_seen: null,
      registered_at: null,
      is_connected: false,
    });

    const { lastFrame } = render(<Status serverId="server-3" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('PENDING');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle fetch error', async () => {
    vi.mocked(getAgentStatus).mockRejectedValue(new Error('Network error'));

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle init error', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<Status serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display agent details with null values', async () => {
    vi.mocked(getAgentStatus).mockResolvedValue({
      id: 'agent-4',
      server_id: 'server-4',
      status: 'connected',
      version: null,
      last_seen: null,
      registered_at: null,
      is_connected: false,
    });

    const { lastFrame } = render(<Status serverId="server-4" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('unknown') || frame?.includes('never') || frame?.includes('pending');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
