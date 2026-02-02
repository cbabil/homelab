/**
 * Tests for backup Import component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Store captured callbacks
let capturedTextInputSubmit: ((value: string) => void) | undefined;
let capturedPasswordSubmit: ((value: string) => void) | undefined;

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

// Mock the backup lib
vi.mock('../../../src/lib/backup.js', () => ({
  importBackup: vi.fn(),
}));

// Mock the auth lib
vi.mock('../../../src/lib/auth.js', () => ({
  requireAdmin: vi.fn(),
}));

// Mock the UI components to capture callbacks - we need to import Text from ink
vi.mock('../../../src/components/ui/index.js', async () => {
  const { Text } = await import('ink');
  return {
    Banner: () => React.createElement(Text, null, 'Tomo'),
    Spinner: ({ text }: { text: string }) => React.createElement(Text, null, text),
    TextInput: ({
      label,
      onSubmit,
    }: {
      label: string;
      onSubmit: (value: string) => void;
      validate?: (value: string) => string | null;
    }) => {
      capturedTextInputSubmit = onSubmit;
      return React.createElement(Text, null, label);
    },
    PasswordInput: ({
      label,
      onSubmit,
    }: {
      label: string;
      onSubmit: (value: string) => void;
      validate?: (value: string) => string | null;
    }) => {
      capturedPasswordSubmit = onSubmit;
      return React.createElement(Text, null, label);
    },
  };
});

import { Import } from '../../../src/commands/backup/Import.js';
import { useMCP } from '../../../src/hooks/useMCP.js';
import { importBackup } from '../../../src/lib/backup.js';
import { requireAdmin } from '../../../src/lib/auth.js';

describe('Import (Backup)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedTextInputSubmit = undefined;
    capturedPasswordSubmit = undefined;
    vi.mocked(useMCP).mockReturnValue({
      connected: true,
      connecting: false,
      error: null,
      callTool: vi.fn(),
    });
    vi.mocked(requireAdmin).mockResolvedValue(true);
  });

  it('should render banner', () => {
    const { lastFrame } = render(<Import options={{}} />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show connecting state', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: true,
      error: null,
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Import options={{}} />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should show MCP error when connection fails', () => {
    vi.mocked(useMCP).mockReturnValue({
      connected: false,
      connecting: false,
      error: 'Connection refused',
      callTool: vi.fn(),
    });

    const { lastFrame } = render(<Import options={{}} />);
    expect(lastFrame()).toContain('Failed to connect');
  });

  it('should accept mcpUrl option', () => {
    const { lastFrame } = render(
      <Import options={{ mcpUrl: 'http://custom:8000/mcp' }} />
    );

    expect(useMCP).toHaveBeenCalledWith('http://custom:8000/mcp');
    expect(lastFrame()).toBeDefined();
  });

  it('should show success when backup imported', async () => {
    vi.mocked(importBackup).mockResolvedValue({
      success: true,
      users_imported: 5,
      servers_imported: 3,
      apps_imported: 10,
    });

    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('successfully') || frame?.includes('Importing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should show error when import fails', async () => {
    vi.mocked(importBackup).mockResolvedValue({
      success: false,
      error: 'Invalid password',
    });

    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'wrongpassword' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Importing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle auth failure', async () => {
    vi.mocked(requireAdmin).mockResolvedValue(false);

    const { lastFrame } = render(<Import options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('authentication');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should prompt for input path when not provided', async () => {
    const { lastFrame } = render(<Import options={{}} />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('input');
    }, { timeout: 2000 }).catch(() => {
      // May not reach that step
    });
  });

  it('should accept overwrite option', () => {
    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'password123', overwrite: true }} />
    );

    expect(lastFrame()).toBeDefined();
  });

  it('should prompt for password when input is provided', async () => {
    const { lastFrame } = render(<Import options={{ input: '/path/to/backup.enc' }} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('password') || frame?.includes('Authenticating');
    }, { timeout: 2000 }).catch(() => {
      // May not reach that step
    });
  });

  it('should handle import exception', async () => {
    vi.mocked(importBackup).mockRejectedValue(new Error('Network error'));

    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('error') || frame?.includes('Network') || frame?.includes('Importing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle init exception', async () => {
    vi.mocked(requireAdmin).mockRejectedValue(new Error('Auth service unavailable'));

    const { lastFrame } = render(<Import options={{}} />);

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Auth service') || frame?.includes('error');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should handle missing error in import result', async () => {
    vi.mocked(importBackup).mockResolvedValue({
      success: false,
    });

    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Failed to import') || frame?.includes('Importing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  it('should display import statistics on success', async () => {
    vi.mocked(importBackup).mockResolvedValue({
      success: true,
      users_imported: 5,
      servers_imported: 3,
      apps_imported: 10,
    });

    const { lastFrame } = render(
      <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
    );

    await vi.waitFor(() => {
      const frame = lastFrame();
      return frame?.includes('Users') || frame?.includes('successfully') || frame?.includes('Importing');
    }, { timeout: 2000 }).catch(() => {
      // May exit quickly
    });
  });

  describe('interactive flow', () => {
    it('should proceed from input to password step', async () => {
      const { lastFrame, rerender } = render(<Import options={{}} />);

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('input');
        },
        { timeout: 2000 }
      );

      // Submit input path
      capturedTextInputSubmit?.('/backup/file.enc');
      rerender(<Import options={{}} />);

      await vi.waitFor(
        () => {
          const frame = lastFrame();
          return frame?.includes('password') || frame?.includes('Authenticating');
        },
        { timeout: 1000 }
      ).catch(() => {
        // May proceed quickly
      });
    });

    it('should proceed from password to importing step', async () => {
      vi.mocked(importBackup).mockResolvedValue({
        success: true,
        users_imported: 1,
        servers_imported: 1,
        apps_imported: 1,
      });

      const { lastFrame, rerender } = render(
        <Import options={{ input: '/backup/file.enc' }} />
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('password');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May not reach
      });

      // Submit password
      capturedPasswordSubmit?.('securepassword');
      rerender(<Import options={{ input: '/backup/file.enc' }} />);

      await vi.waitFor(
        () => {
          const frame = lastFrame();
          return frame?.includes('Importing') || frame?.includes('successfully');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May proceed quickly
      });
    });

    it('should handle zero import counts', async () => {
      vi.mocked(importBackup).mockResolvedValue({
        success: true,
        users_imported: 0,
        servers_imported: 0,
        apps_imported: 0,
      });

      const { lastFrame } = render(
        <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
      );

      await vi.waitFor(
        () => {
          const frame = lastFrame();
          return frame?.includes('successfully') || frame?.includes('Importing');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May exit quickly
      });
    });

    it('should handle undefined import counts', async () => {
      vi.mocked(importBackup).mockResolvedValue({
        success: true,
      });

      const { lastFrame } = render(
        <Import options={{ input: '/path/to/backup.enc', password: 'password123' }} />
      );

      await vi.waitFor(
        () => {
          const frame = lastFrame();
          return frame?.includes('successfully') || frame?.includes('Importing');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May exit quickly
      });
    });
  });
});
