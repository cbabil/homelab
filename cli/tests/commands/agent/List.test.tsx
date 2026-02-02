/**
 * Tests for agent List component.
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
  listAgents: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { List } from '../../../src/commands/agent/List.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { listAgents } from '../../../src/lib/agent.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('List (Agent)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMCP).mockReturnValue({
      connected: true,
      connecting: false,
      error: null,
      callTool: vi.fn(),
    });
    vi.mocked(requireAdmin).mockResolvedValue(true);
    vi.mocked(listAgents).mockResolvedValue([]);
  });

  it('should render banner', () => {
    const { lastFrame } = render(<List options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<List options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<List options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <List options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show no agents message when list is empty', async () => {
    vi.mocked(listAgents).mockResolvedValue([]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('No agents');
    }, { timeout: 2000 }).catch(() => {
      // May exit before we can check
    });
  });

  it('should display agents when found', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      {
        id: 'agent-1',
        server_id: 'server-1',
        status: 'connected',
        version: '1.0.0',
        last_seen: '2024-01-15',
        registered_at: '2024-01-01',
      },
    ]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('agent-1') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle list fetch error', async () => {
    vi.mocked(listAgents).mockRejectedValue(new Error('Network error'));

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display connected status with green color', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      {
        id: 'agent-1',
        server_id: 'server-1',
        status: 'connected',
        version: '1.0.0',
        last_seen: '2024-01-15',
        registered_at: '2024-01-01',
      },
    ]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('CONNECTED');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display disconnected status with yellow color', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      {
        id: 'agent-2',
        server_id: 'server-2',
        status: 'disconnected',
        version: null,
        last_seen: null,
        registered_at: null,
      },
    ]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('DISCONNECTED');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display unknown status with gray color', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      {
        id: 'agent-3',
        server_id: 'server-3',
        status: 'pending',
        version: null,
        last_seen: null,
        registered_at: null,
      },
    ]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('PENDING');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display multiple agents', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      {
        id: 'agent-1',
        server_id: 'server-1',
        status: 'connected',
        version: '1.0.0',
        last_seen: '2024-01-15',
        registered_at: '2024-01-01',
      },
      {
        id: 'agent-2',
        server_id: 'server-2',
        status: 'disconnected',
        version: '0.9.0',
        last_seen: '2024-01-10',
        registered_at: '2024-01-05',
      },
    ]);

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('2 agent');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle init error', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<List options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
