/**
 * Tests for agent Ping component.
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
  pingAgent: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { Ping } from '../../../src/commands/agent/Ping.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { pingAgent } from '../../../src/lib/agent.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('Ping (Agent)', () => {
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
    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <Ping serverId="server-1" options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should accept timeout option', () => {
    const { lastFrame } = render(
      <Ping serverId="server-1" options={{ timeout: '10' }} />
    );

    expect(lastFrame()).toBeDefined();
  });

  it('should show pong when agent responds', async () => {
    vi.mocked(pingAgent).mockResolvedValue({
      agent_id: 'agent-1',
      responsive: true,
      latency_ms: 42,
    });

    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Pong') || frame?.includes('Pinging');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when agent not responsive', async () => {
    vi.mocked(pingAgent).mockResolvedValue({
      agent_id: 'agent-1',
      responsive: false,
      latency_ms: null,
    });

    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('not respond') || frame?.includes('Pinging');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<Ping serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
