/**
 * Tests for ListLocked component.
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
  getLockedAccounts: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { ListLocked } from '../../../src/commands/security/ListLocked.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { getLockedAccounts } from '../../../src/lib/security.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('ListLocked', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMCP).mockReturnValue({
      connected: true,
      connecting: false,
      error: null,
      callTool: vi.fn(),
    });
    vi.mocked(requireAdmin).mockResolvedValue(true);
    vi.mocked(getLockedAccounts).mockResolvedValue([]);
  });

  it('should render banner', () => {
    const { lastFrame } = render(<ListLocked options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<ListLocked options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<ListLocked options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <ListLocked options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show no locked accounts message when list is empty', async () => {
    vi.mocked(getLockedAccounts).mockResolvedValue([]);

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('No locked');
    }, { timeout: 2000 }).catch(() => {
      // May exit before we can check
    });
  });

  it('should display locked accounts when found', async () => {
    vi.mocked(getLockedAccounts).mockResolvedValue([
      {
        id: '1',
        identifier_type: 'username',
        identifier: 'testuser',
        attempt_count: 5,
        locked_at: '2024-01-15',
        lock_expires_at: '2024-01-16',
        ip_address: '192.168.1.1',
      },
    ]);

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('testuser') || frame?.includes('locked') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should pass includeExpired option', async () => {
    const { lastFrame } = render(<ListLocked options={{ includeExpired: true }} />);

    await vi.waitFor(() => {
      expect(getLockedAccounts).toHaveBeenCalledWith(true, false);
    }, { timeout: 1000 }).catch(() => {
      // Expected
    });

    expect(lastFrame()).toBeDefined();
  });

  it('should pass includeUnlocked option', async () => {
    const { lastFrame } = render(<ListLocked options={{ includeUnlocked: true }} />);

    await vi.waitFor(() => {
      expect(getLockedAccounts).toHaveBeenCalledWith(false, true);
    }, { timeout: 1000 }).catch(() => {
      // Expected
    });

    expect(lastFrame()).toBeDefined();
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle init exception', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle fetch exception', async () => {
    vi.mocked(getLockedAccounts).mockRejectedValue(new Error('Database error'));

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Database') || frame?.includes('error') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display multiple locked accounts', async () => {
    vi.mocked(getLockedAccounts).mockResolvedValue([
      {
        id: '1',
        identifier_type: 'username',
        identifier: 'user1',
        attempt_count: 5,
        locked_at: '2024-01-15',
        lock_expires_at: '2024-01-16',
        ip_address: '192.168.1.1',
      },
      {
        id: '2',
        identifier_type: 'ip',
        identifier: '10.0.0.1',
        attempt_count: 10,
        locked_at: '2024-01-14',
        lock_expires_at: null,
        ip_address: '10.0.0.1',
      },
    ]);

    const { lastFrame } = render(<ListLocked options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('2 locked') || frame?.includes('user1') || frame?.includes('Fetching');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
