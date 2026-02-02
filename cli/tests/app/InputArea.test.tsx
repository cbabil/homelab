/**
 * Tests for InputArea component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Store captured useInput callback
let capturedUseInputCallback:
  | ((input: string, key: Record<string, boolean>) => void)
  | undefined;
let capturedOnSubmit: ((value: string) => void) | undefined;
let capturedOnChange: ((value: string) => void) | undefined;

// Mock ink to capture useInput
vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useInput: (
      callback: (input: string, key: Record<string, boolean>) => void,
      options?: { isActive: boolean }
    ) => {
      if (options?.isActive !== false) {
        capturedUseInputCallback = callback;
      }
    },
  };
});

// Mock ink-text-input to capture callbacks
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

import { InputArea } from '../../src/app/InputArea.js';

describe('InputArea', () => {
  beforeEach(() => {
    capturedUseInputCallback = undefined;
    capturedOnSubmit = undefined;
    capturedOnChange = undefined;
    vi.clearAllMocks();
  });

  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    onSubmit: vi.fn(),
    commandHistory: [] as string[],
    historyIndex: -1,
    onHistoryNavigate: vi.fn(),
  };

  describe('rendering', () => {
    it('should render with prompt', () => {
      const { lastFrame } = render(<InputArea {...defaultProps} />);

      expect(lastFrame()).toContain('>');
    });

    it('should render input value', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} value="test input" />
      );

      expect(lastFrame()).toContain('test input');
    });

    it('should show placeholder when empty', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} placeholder="Type here" />
      );

      expect(lastFrame()).toContain('Type here');
    });
  });

  describe('disabled state', () => {
    it('should show disabled state when disabled', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} disabled={true} value="running" />
      );

      expect(lastFrame()).toContain('running');
    });

    it('should show Processing when disabled with no value', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} disabled={true} value="" />
      );

      expect(lastFrame()).toContain('Processing');
    });
  });

  describe('submit handling', () => {
    it('should not submit empty input', () => {
      const onSubmit = vi.fn();
      const { stdin } = render(
        <InputArea {...defaultProps} value="" onSubmit={onSubmit} />
      );

      stdin.write('\r');

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('should not submit when disabled', () => {
      const onSubmit = vi.fn();
      const { stdin } = render(
        <InputArea
          {...defaultProps}
          value="test"
          onSubmit={onSubmit}
          disabled={true}
        />
      );

      stdin.write('\r');

      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  describe('props interface', () => {
    it('should accept all required props', () => {
      const props = {
        value: 'test',
        onChange: vi.fn(),
        onSubmit: vi.fn(),
        commandHistory: ['cmd1', 'cmd2'],
        historyIndex: 0,
        onHistoryNavigate: vi.fn(),
      };

      const { lastFrame } = render(<InputArea {...props} />);

      expect(lastFrame()).toBeDefined();
    });

    it('should accept optional disabled prop', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} disabled={false} />
      );

      expect(lastFrame()).toBeDefined();
    });

    it('should accept optional placeholder prop', () => {
      const { lastFrame } = render(
        <InputArea {...defaultProps} placeholder="Custom placeholder" />
      );

      expect(lastFrame()).toContain('Custom placeholder');
    });
  });

  describe('command history navigation', () => {
    it('should navigate back in history on up arrow', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();
      const commandHistory = ['cmd1', 'cmd2', 'cmd3'];

      render(
        <InputArea
          {...defaultProps}
          value="current"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={commandHistory}
          historyIndex={-1}
        />
      );

      // Simulate up arrow
      capturedUseInputCallback?.('', { upArrow: true });

      expect(onHistoryNavigate).toHaveBeenCalledWith(2); // Last index
      expect(onChange).toHaveBeenCalledWith('cmd3');
    });

    it('should continue navigating back on repeated up arrow', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();
      const commandHistory = ['cmd1', 'cmd2', 'cmd3'];

      render(
        <InputArea
          {...defaultProps}
          value="cmd3"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={commandHistory}
          historyIndex={2}
        />
      );

      // Simulate up arrow again
      capturedUseInputCallback?.('', { upArrow: true });

      expect(onHistoryNavigate).toHaveBeenCalledWith(1);
      expect(onChange).toHaveBeenCalledWith('cmd2');
    });

    it('should do nothing on up arrow when at start of history', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();
      const commandHistory = ['cmd1', 'cmd2'];

      render(
        <InputArea
          {...defaultProps}
          value="cmd1"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={commandHistory}
          historyIndex={0}
        />
      );

      capturedUseInputCallback?.('', { upArrow: true });

      expect(onHistoryNavigate).not.toHaveBeenCalled();
    });

    it('should do nothing on up arrow when history is empty', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={[]}
          historyIndex={-1}
        />
      );

      capturedUseInputCallback?.('', { upArrow: true });

      expect(onHistoryNavigate).not.toHaveBeenCalled();
      expect(onChange).not.toHaveBeenCalled();
    });

    it('should navigate forward in history on down arrow', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();
      const commandHistory = ['cmd1', 'cmd2', 'cmd3'];

      render(
        <InputArea
          {...defaultProps}
          value="cmd1"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={commandHistory}
          historyIndex={0}
        />
      );

      capturedUseInputCallback?.('', { downArrow: true });

      expect(onHistoryNavigate).toHaveBeenCalledWith(1);
      expect(onChange).toHaveBeenCalledWith('cmd2');
    });

    it('should return to current input on down arrow at end of history', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();
      const commandHistory = ['cmd1', 'cmd2'];

      render(
        <InputArea
          {...defaultProps}
          value="cmd2"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={commandHistory}
          historyIndex={1}
        />
      );

      capturedUseInputCallback?.('', { downArrow: true });

      expect(onHistoryNavigate).toHaveBeenCalledWith(-1);
    });

    it('should do nothing on down arrow when not in history', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={['cmd1']}
          historyIndex={-1}
        />
      );

      capturedUseInputCallback?.('', { downArrow: true });

      expect(onHistoryNavigate).not.toHaveBeenCalled();
    });

    it('should clear input on Ctrl+C', () => {
      const onChange = vi.fn();
      const onHistoryNavigate = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          value="something"
          onChange={onChange}
          onHistoryNavigate={onHistoryNavigate}
          commandHistory={['cmd1']}
          historyIndex={0}
        />
      );

      capturedUseInputCallback?.('c', { ctrl: true });

      expect(onChange).toHaveBeenCalledWith('');
      expect(onHistoryNavigate).toHaveBeenCalledWith(-1);
    });
  });

  describe('handleSubmit', () => {
    it('should call onSubmit with trimmed value', () => {
      const onSubmit = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          value="  test command  "
          onSubmit={onSubmit}
        />
      );

      capturedOnSubmit?.('  test command  ');

      expect(onSubmit).toHaveBeenCalledWith('test command');
    });

    it('should not submit when value is only whitespace', () => {
      const onSubmit = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          value="   "
          onSubmit={onSubmit}
        />
      );

      capturedOnSubmit?.('   ');

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('should not submit when disabled', () => {
      const onSubmit = vi.fn();

      render(
        <InputArea
          {...defaultProps}
          value="test"
          onSubmit={onSubmit}
          disabled={true}
        />
      );

      capturedOnSubmit?.('test');

      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  describe('disabled keyboard input', () => {
    it('should not capture input when disabled', () => {
      render(
        <InputArea
          {...defaultProps}
          disabled={true}
        />
      );

      // When disabled, useInput should not be active
      expect(capturedUseInputCallback).toBeUndefined();
    });
  });
});
