/**
 * Tests for CommandPrompt component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

let capturedOnSubmit: ((value: string) => void) | undefined;

// Mock ink-text-input
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
      return React.createElement(Text, null, value || placeholder || '');
    },
  };
});

// Mock useInput
vi.mock('ink', async () => {
  const actual = await vi.importActual<typeof import('ink')>('ink');
  return {
    ...actual,
    useInput: vi.fn(),
  };
});

import { CommandPrompt } from '../../../src/components/dashboard/CommandPrompt.js';

describe('CommandPrompt', () => {
  beforeEach(() => {
    capturedOnSubmit = undefined;
    vi.clearAllMocks();
  });

  it('should render the prompt with username', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
      />
    );

    expect(lastFrame()).toContain('admin@tomo:~$');
  });

  it('should show placeholder text when empty', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
      />
    );

    expect(lastFrame()).toContain('/help');
  });

  it('should show Processing when disabled', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        disabled={true}
      />
    );

    expect(lastFrame()).toContain('Processing...');
  });

  it('should show current value when disabled', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value="running command"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        disabled={true}
      />
    );

    expect(lastFrame()).toContain('running command');
  });

  it('should call onSubmit with trimmed value', () => {
    const mockSubmit = vi.fn();

    render(
      <CommandPrompt
        username="admin"
        value="test"
        onChange={vi.fn()}
        onSubmit={mockSubmit}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
      />
    );

    capturedOnSubmit?.('  /help  ');
    expect(mockSubmit).toHaveBeenCalledWith('/help');
  });

  it('should not submit when disabled', () => {
    const mockSubmit = vi.fn();

    render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={mockSubmit}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        disabled={true}
      />
    );

    capturedOnSubmit?.('test');
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('should not submit empty input', () => {
    const mockSubmit = vi.fn();

    render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={mockSubmit}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
      />
    );

    capturedOnSubmit?.('   ');
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('should show offline indicator when offline', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        offline={true}
      />
    );

    expect(lastFrame()).toContain('OFFLINE');
    expect(lastFrame()).toContain('tomo:~$');
    expect(lastFrame()).not.toContain('admin@tomo');
  });

  it('should show normal prompt when online', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        offline={false}
      />
    );

    expect(lastFrame()).toContain('admin@tomo:~$');
    expect(lastFrame()).not.toContain('OFFLINE');
  });

  it('should use promptLabel instead of offline indicator when both set', () => {
    const { lastFrame } = render(
      <CommandPrompt
        username="admin"
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        commandHistory={[]}
        historyIndex={-1}
        onHistoryNavigate={vi.fn()}
        offline={true}
        promptLabel="Username: "
      />
    );

    expect(lastFrame()).toContain('Username:');
    expect(lastFrame()).not.toContain('OFFLINE');
  });
});
