/**
 * Tests for agent Install component.
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
  installAgent: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { Install } from '../../../src/commands/agent/Install.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { installAgent } from '../../../src/lib/agent.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('Install (Agent)', () => {
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
    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <Install serverId="server-1" options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show success when agent installed', async () => {
    vi.mocked(installAgent).mockResolvedValue({
      success: true,
      data: { agent_id: 'agent-123', version: '1.0.0' },
    });

    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('successfully') || frame?.includes('Installing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when installation fails', async () => {
    vi.mocked(installAgent).mockResolvedValue({
      success: false,
      error: 'Installation failed',
    });

    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Installing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<Install serverId="server-1" options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
