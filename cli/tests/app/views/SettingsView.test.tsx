/**
 * Tests for SettingsView component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React, { act } from 'react';

let capturedUseInputCallback:
  | ((_input: string, key: Record<string, boolean>) => void)
  | undefined;

vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useInput: (
      callback: (_input: string, key: Record<string, boolean>) => void
    ) => {
      capturedUseInputCallback = callback;
    },
  };
});

import { SettingsView } from '../../../src/app/views/SettingsView.js';

const defaultProps = {
  mcpUrl: 'http://localhost:8000/mcp',
  refreshInterval: 30000,
  autoRefresh: true,
  version: '0.1.0',
};

describe('SettingsView', () => {
  beforeEach(() => {
    capturedUseInputCallback = undefined;
    vi.clearAllMocks();
  });

  it('should render settings panel', () => {
    const { lastFrame } = render(<SettingsView {...defaultProps} />);
    expect(lastFrame()).toContain('[ SETTINGS ]');
  });

  it('should render sub-tab bar', () => {
    const { lastFrame } = render(<SettingsView {...defaultProps} />);
    const frame = lastFrame() || '';
    expect(frame).toContain('CONNECTION');
    expect(frame).toContain('PREFERENCES');
    expect(frame).toContain('ABOUT');
  });

  it('should show arrow key hint', () => {
    const { lastFrame } = render(<SettingsView {...defaultProps} />);
    expect(lastFrame()).toContain('navigate');
  });

  describe('connection tab (default)', () => {
    it('should show MCP URL', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);
      expect(lastFrame()).toContain('http://localhost:8000/mcp');
    });

    it('should show env var hint', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);
      expect(lastFrame()).toContain('MCP_SERVER_URL');
    });
  });

  describe('preferences tab', () => {
    it('should show refresh interval and auto refresh', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);

      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });

      const frame = lastFrame() || '';
      expect(frame).toContain('30s');
      expect(frame).toContain('ON');
    });

    it('should show auto refresh OFF', () => {
      const { lastFrame } = render(
        <SettingsView {...defaultProps} autoRefresh={false} />
      );

      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });

      expect(lastFrame()).toContain('OFF');
    });
  });

  describe('about tab', () => {
    it('should show CLI version', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);

      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });
      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });

      expect(lastFrame()).toContain('0.1.0');
    });

    it('should show environment variables hint', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);

      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });
      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });

      expect(lastFrame()).toContain('environment variables');
    });
  });

  describe('navigation', () => {
    it('should wrap around when navigating right past last tab', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);

      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });
      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });
      act(() => {
        capturedUseInputCallback?.('', { rightArrow: true });
      });

      expect(lastFrame()).toContain('MCP Server URL');
    });

    it('should wrap around when navigating left from first tab', () => {
      const { lastFrame } = render(<SettingsView {...defaultProps} />);

      act(() => {
        capturedUseInputCallback?.('', { leftArrow: true });
      });

      expect(lastFrame()).toContain('CLI Version');
    });
  });
});
