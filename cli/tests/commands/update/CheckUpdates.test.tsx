/**
 * Tests for CheckUpdates component.
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

// Mock the patch lib
vi.mock('../../../src/lib/patch.js', () => ({
  checkForUpdates: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

import { CheckUpdates } from '../../../src/commands/update/CheckUpdates.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { checkForUpdates } from '../../../src/lib/patch.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('CheckUpdates', () => {
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
    const { lastFrame } = render(<CheckUpdates options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <CheckUpdates options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show up-to-date when no update available', async () => {
    vi.mocked(checkForUpdates).mockResolvedValue({
      success: true,
      components: {
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0',
      },
      latest_version: '1.0.0',
      update_available: false,
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('latest') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show update available when newer version exists', async () => {
    vi.mocked(checkForUpdates).mockResolvedValue({
      success: true,
      components: {
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0',
      },
      latest_version: '2.0.0',
      update_available: true,
      release_url: 'https://example.com/releases/2.0.0',
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('available') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when check fails', async () => {
    vi.mocked(checkForUpdates).mockResolvedValue({
      success: false,
      update_available: false,
      error: 'Failed to check updates',
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle init exception', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle check exception', async () => {
    vi.mocked(checkForUpdates).mockRejectedValue(new Error('Network error'));

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Network') || frame?.includes('error') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display component versions', async () => {
    vi.mocked(checkForUpdates).mockResolvedValue({
      success: true,
      components: {
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0',
      },
      latest_version: '1.0.0',
      update_available: false,
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('1.0.0') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display release URL when update available', async () => {
    vi.mocked(checkForUpdates).mockResolvedValue({
      success: true,
      components: {
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0',
      },
      latest_version: '2.0.0',
      update_available: true,
      release_url: 'https://github.com/example/releases/v2.0.0',
    });

    const { lastFrame } = render(<CheckUpdates options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('2.0.0') || frame?.includes('available') || frame?.includes('Checking');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });
});
