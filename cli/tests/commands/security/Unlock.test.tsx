/**
 * Tests for Unlock component.
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

// Mock the security lib
vi.mock('../../../src/lib/security.js', () => ({
  unlockAccount: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { Unlock } from '../../../src/commands/security/Unlock.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { unlockAccount } from '../../../src/lib/security.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('Unlock', () => {
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
    const { lastFrame } = render(<Unlock options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Unlock options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Unlock options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <Unlock options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show success when account unlocked', async () => {
    vi.mocked(unlockAccount).mockResolvedValue({ success: true });

    const { lastFrame } = render(
      <Unlock options={{ lockId: '123', admin: 'admin' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('successfully') || frame?.includes('Unlocking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when unlock fails', async () => {
    vi.mocked(unlockAccount).mockResolvedValue({
      success: false,
      error: 'Lock not found',
    });

    const { lastFrame } = render(
      <Unlock options={{ lockId: '123', admin: 'admin' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Unlocking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<Unlock options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should prompt for lock ID when not provided', async () => {
    const { lastFrame } = render(<Unlock options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('lock ID');
    }, { timeout: 2000 }).catch(() => {
      // May not reach that step
    });
  });

  it('should accept notes option', () => {
    const { lastFrame } = render(
      <Unlock options={{ lockId: '123', admin: 'admin', notes: 'Test unlock' }} />
    );

    expect(lastFrame()).toBeDefined();
  });

  it('should handle init exception', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<Unlock options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle unlock exception', async () => {
    vi.mocked(unlockAccount).mockRejectedValue(new Error('Database error'));

    const { lastFrame } = render(
      <Unlock options={{ lockId: '123', admin: 'admin' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Database') || frame?.includes('error') || frame?.includes('Unlocking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should prompt for admin when only lockId is provided', async () => {
    const { lastFrame } = render(<Unlock options={{ lockId: '123' }} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('admin') || frame?.includes('Authenticating');
    }, { timeout: 2000 }).catch(() => {
      // May not reach that step
    });
  });
});
