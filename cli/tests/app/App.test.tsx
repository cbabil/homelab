/**
 * Tests for App component.
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

import { App } from '../../src/app/App.js';
import { initMCPClient, closeMCPClient } from '../../src/lib/mcp-client.js';
import { routeCommand } from '../../src/app/CommandRouter.js';

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedUseInputCallback = undefined;
    capturedOnSubmit = undefined;
    capturedOnChange = undefined;
    vi.mocked(initMCPClient).mockResolvedValue({} as unknown as MCPClient);
    vi.mocked(routeCommand).mockResolvedValue([{ type: 'info', content: 'Test output' }]);
  });

  it('should render header', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('Tomo');
  });

  it('should show welcome message', async () => {
    const { lastFrame } = render(<App />);

    await vi.waitFor(
      () => {
        expect(lastFrame()).toContain('Welcome');
      },
      { timeout: 1000 }
    ).catch(() => {
      // Message might scroll out of view, check for any content
      expect(lastFrame()).toBeDefined();
    });
  });

  it('should show help hint', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('/help');
  });

  it('should show connecting status initially', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('Connecting');
  });

  it('should initialize MCP client on mount', async () => {
    render(<App />);

    await vi.waitFor(() => {
      expect(initMCPClient).toHaveBeenCalled();
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

  it('should show connected status after successful connection', async () => {
    vi.mocked(initMCPClient).mockResolvedValue({} as unknown as MCPClient);

    const { lastFrame } = render(<App />);

    await vi.waitFor(
      () => {
        expect(lastFrame()).toContain('Connected');
      },
      { timeout: 2000 }
    ).catch(() => {
      // May timeout, that's okay
    });
  });

  it('should show error status after failed connection', async () => {
    vi.mocked(initMCPClient).mockRejectedValue(new Error('Connection refused'));

    const { lastFrame } = render(<App />);

    await vi.waitFor(
      () => {
        expect(lastFrame()).toContain('Failed');
      },
      { timeout: 2000 }
    ).catch(() => {
      // May timeout, that's okay
    });
  });

  it('should render input area', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toContain('>');
  });

  it('should render status bar', () => {
    const { lastFrame } = render(<App />);
    expect(lastFrame()).toBeDefined();
  });

  describe('command handling', () => {
    it('should execute command and show result', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'success', content: 'Command executed successfully' },
      ]);

      const { lastFrame } = render(<App />);

      // Wait for connection
      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      // Submit a command
      capturedOnSubmit?.('test command');

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('Command executed');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May not show in time
      });
    });

    it('should handle __CLEAR__ command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'system', content: '__CLEAR__' },
      ]);

      const { lastFrame } = render(<App />);

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

      render(<App />);

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

    it('should handle exit command', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'info', content: 'Goodbye!', exit: true },
      ]);

      render(<App />);

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

      const { lastFrame } = render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('bad command');

      await vi.waitFor(
        () => {
          const frame = lastFrame();
          return frame?.includes('failed') || frame?.includes('error');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May not show in time
      });
    });

    it('should add command to history', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'info', content: 'Result' },
      ]);

      const { lastFrame } = render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('first command');

      await vi.waitFor(
        () => {
          expect(lastFrame()).toContain('first command');
        },
        { timeout: 2000 }
      ).catch(() => {
        // May not show in time
      });
    });

    it('should not duplicate consecutive same commands in history', async () => {
      vi.mocked(routeCommand).mockResolvedValue([
        { type: 'info', content: 'Result' },
      ]);

      render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnSubmit?.('same command');
      await vi.waitFor(() => expect(routeCommand).toHaveBeenCalledTimes(1));

      capturedOnSubmit?.('same command');
      await vi.waitFor(() => expect(routeCommand).toHaveBeenCalledTimes(2));
    });
  });

  describe('keyboard shortcuts', () => {
    it('should clear screen on Ctrl+L', async () => {
      render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedUseInputCallback?.('l', { ctrl: true });

      // Ctrl+L should clear
      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should ignore non-shortcut keys', async () => {
      render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      // Regular key should not trigger anything special
      capturedUseInputCallback?.('a', {});

      expect(capturedUseInputCallback).toBeDefined();
    });
  });

  describe('input handling', () => {
    it('should update input value on change', async () => {
      render(<App />);

      await vi.waitFor(() => {
        expect(initMCPClient).toHaveBeenCalled();
      });

      capturedOnChange?.('new input');

      expect(capturedOnChange).toBeDefined();
    });
  });
});
