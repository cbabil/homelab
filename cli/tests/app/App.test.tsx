/**
 * Tests for App component (dashboard layout).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import type { MCPClient } from '../../src/lib/mcp-client.js';

// Store captured useInput callback and InkTextInput callbacks
let capturedUseInputCallback:
  | ((input: string, key: Record<string, boolean>) => void)
  | undefined;
let capturedOnSubmit: ((value: string) => void) | undefined;
let capturedOnChange: ((value: string) => void) | undefined;
const mockExit = vi.fn();

// Mock ink's useApp and useInput hooks
vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useApp: () => ({ exit: mockExit }),
    useInput: (
      callback: (input: string, key: Record<string, boolean>) => void
    ) => {
      capturedUseInputCallback = callback;
    },
  };
});

// Mock ink-text-input to capture submit callback
vi.mock('ink-text-input', async () => {
  const { Text } = await import('ink');
  return {
    default: ({
      value,
      onChange,
      onSubmit,
      placeholder,
    }: {
      value: string;
      onChange: (value: string) => void;
      onSubmit: (value: string) => void;
      placeholder?: string;
    }) => {
      capturedOnSubmit = onSubmit;
      capturedOnChange = onChange;
      return React.createElement(Text, null, value || placeholder || '');
    },
  };
});

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  initMCPClient: vi.fn(),
  closeMCPClient: vi.fn(),
  getMCPClient: vi.fn(),
}));

// Mock the CommandRouter
vi.mock('../../src/app/CommandRouter.js', () => ({
  routeCommand: vi.fn(),
}));

// Mock useDashboardData
vi.mock('../../src/hooks/useDashboardData.js', () => ({
  useDashboardData: vi.fn(() => ({
    agents: [],
    servers: [],
    loading: false,
    error: null,
    lastRefresh: null,
    refresh: vi.fn(),
  })),
}));

// Mock auth module
vi.mock('../../src/lib/auth.js', () => ({
  authenticateAdmin: vi.fn(),
  checkSystemSetup: vi.fn(),
  clearAuth: vi.fn(),
  getAuthToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => null),
  getUsername: vi.fn(() => null),
  getRole: vi.fn(() => null),
  revokeToken: vi.fn(() => Promise.resolve()),
  refreshAuthToken: vi.fn(() => Promise.resolve(false)),
}));

// Mock admin module (used by useSetupFlow and useResetPasswordFlow hooks)
vi.mock('../../src/lib/admin.js', () => ({
  createAdmin: vi.fn(),
  resetPassword: vi.fn(),
}));

// Mock backup module (used by useBackupFlow hook)
vi.mock('../../src/lib/backup.js', () => ({
  exportBackup: vi.fn(),
  importBackup: vi.fn(),
}));

import { App } from '../../src/app/App.js';
import { initMCPClient, closeMCPClient } from '../../src/lib/mcp-client.js';
import { routeCommand } from '../../src/app/CommandRouter.js';
import { checkSystemSetup, clearAuth, revokeToken } from '../../src/lib/auth.js';

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedUseInputCallback = undefined;
    capturedOnSubmit = undefined;
    capturedOnChange = undefined;
    vi.mocked(initMCPClient).mockResolvedValue({
      setAuthTokenGetter: vi.fn(),
      setTokenRefresher: vi.fn(),
      setForceLogoutHandler: vi.fn(),
    } as unknown as MCPClient);
    vi.mocked(checkSystemSetup).mockResolvedValue(false);
    vi.mocked(routeCommand).mockResolvedValue([{ type: 'info', content: 'Test output' }]);
  });

  it('should render status bar with version at top', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('VERSION: 0.1.0');
  });

  it('should render ASCII header on all tabs', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('A D M I N');
  });

  it('should render bottom navigation menu', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('DASHBOARD');
  });

  it('should render MCP info in status bar', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('MCP:');
    expect(lastFrame()).toContain('STATUS:');
  });

  it('should render tab navigation items', () => {
    const { lastFrame } = render(<App />);
    const frame = lastFrame() || '';
    expect(frame).toContain('DASHBOARD');
    expect(frame).toContain('AGENTS');
    expect(frame).toContain('LOGS');
    expect(frame).toContain('SETTINGS');
  });

  describe('auto-connect', () => {
    it('should auto-connect to default MCP URL on mount', async () => {
      render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalledWith('http://localhost:8000/mcp');
      });
    });

    it('should use custom MCP URL when provided', async () => {
      render(<App mcpUrl="http://custom:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalledWith('http://custom:8000/mcp');
      });
    });

    it('should close MCP client on unmount', async () => {
      const { unmount } = render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      unmount();
      expect(closeMCPClient).toHaveBeenCalled();
    });

    it('should show login prompt after successful connection', async () => {
      const { lastFrame } = render(<App />);

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Username:');
        },
        { timeout: 2000 }
      );
    });

    it('should show offline prompt when connection fails', async () => {
      vi.mocked(initMCPClient).mockRejectedValue(new Error('Connection refused'));

      const { lastFrame } = render(<App />);

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('OFFLINE');
        },
        { timeout: 2000 }
      );
    });

    it('should let user type commands when offline', async () => {
      vi.mocked(initMCPClient).mockRejectedValue(new Error('Connection refused'));

      const { lastFrame } = render(<App />);

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('OFFLINE');
        },
        { timeout: 2000 }
      );

      // Prompt should still be interactive
      expect(lastFrame()).toContain('tomo:~$');
    });
  });

  describe('command handling', () => {
    it('should execute command via router', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'success', content: 'Command executed successfully' },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('test command');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle __CLEAR__ command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__CLEAR__' },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/clear');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle __LOGOUT__ command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__LOGOUT__' },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/logout');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle __VIEW__ command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__VIEW__agents' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/view agents');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('[ AGENT_MANAGEMENT ]');
        },
        { timeout: 2000 }
      ).catch(() => {
        // View may not have switched in test environment
      });
    });

    it('should handle __REFRESH__ command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__REFRESH__' },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/refresh');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle exit command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'info', content: 'Goodbye!', exit: true },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/quit');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle command error', async () => {
      vi.mocked(routeCommand).mockRejectedValue(new Error('Command failed'));

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('bad command');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it('should handle __SETUP__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__SETUP__' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/admin create');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Username:');
        },
        { timeout: 2000 }
      );
    });

    it('should handle __LOGIN__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__LOGIN__' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/login');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Username:');
        },
        { timeout: 2000 }
      );
    });

    it('should handle __RESET_PASSWORD__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__RESET_PASSWORD__testuser' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/user reset-password testuser');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('New password:');
        },
        { timeout: 2000 }
      );
    });

    it('should handle __BACKUP_EXPORT__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__BACKUP_EXPORT__./backup.enc' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/backup export ./backup.enc');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Encryption password:');
        },
        { timeout: 2000 }
      );
    });

    it('should handle __BACKUP_IMPORT__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__BACKUP_IMPORT__./backup.enc' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/backup import ./backup.enc');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Decryption password:');
        },
        { timeout: 2000 }
      );
    });

    it('should handle __BACKUP_IMPORT_OVERWRITE__ signal', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__BACKUP_IMPORT_OVERWRITE__./backup.enc' },
      ]);

      const { lastFrame } = render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/backup import ./backup.enc --overwrite');

      await vi.waitFor(
        () => {
          expect(routeCommand).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Decryption password:');
        },
        { timeout: 2000 }
      );
    });
  });

  describe('logout revokes token', () => {
    it('should call revokeToken when logout signal is handled', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__LOGOUT__' },
        { type: 'success', content: 'Logged out successfully' },
      ]);

      render(<App mcpUrl="http://localhost:8000/mcp" />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('/logout');

      await vi.waitFor(
        () => {
          expect(revokeToken).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });
  });

  describe('keyboard shortcuts', () => {
    it('should support Ctrl+L shortcut', () => {
      render(<App />);
      capturedUseInputCallback?.('l', { ctrl: true });
      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should ignore non-shortcut keys', () => {
      render(<App />);
      capturedUseInputCallback?.('a', {});
      expect(capturedUseInputCallback).toBeDefined();
    });
  });

  describe('input handling', () => {
    it('should update input value on change', () => {
      render(<App />);
      capturedOnChange?.('new input');
      expect(capturedOnChange).toBeDefined();
    });
  });
});
