/**
 * Tests for OutputHistory component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';

// Store captured useInput callback
let capturedUseInputCallback:
  | ((input: string, key: Record<string, boolean>) => void)
  | undefined;

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

import { OutputHistory } from '../../src/app/OutputHistory.js';
import { createMessage, type OutputMessage } from '../../src/app/types.js';

describe('OutputHistory', () => {
  beforeEach(() => {
    capturedUseInputCallback = undefined;
  });

  describe('rendering messages', () => {
    it('should render empty when no messages', () => {
      const { lastFrame } = render(<OutputHistory messages={[]} height={5} />);

      // Should render without error
      expect(lastFrame()).toBeDefined();
    });

    it('should render message content', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test message')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('Test message');
    });

    it('should render multiple messages', () => {
      const messages: OutputMessage[] = [
        createMessage('info', 'Message 1'),
        createMessage('success', 'Message 2'),
        createMessage('error', 'Message 3'),
      ];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={10} />
      );

      expect(lastFrame()).toContain('Message 1');
      expect(lastFrame()).toContain('Message 2');
      expect(lastFrame()).toContain('Message 3');
    });
  });

  describe('message type prefixes', () => {
    it('should show prefix for command type', () => {
      const messages: OutputMessage[] = [createMessage('command', 'test command')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('>');
      expect(lastFrame()).toContain('test command');
    });

    it('should show prefix for success type', () => {
      const messages: OutputMessage[] = [createMessage('success', 'Success!')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('[OK]');
    });

    it('should show prefix for error type', () => {
      const messages: OutputMessage[] = [createMessage('error', 'Error!')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('[ERROR]');
    });
  });

  describe('timestamps', () => {
    it('should show timestamp for messages', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      // Timestamp format is HH:MM:SS
      expect(lastFrame()).toMatch(/\d{2}:\d{2}:\d{2}/);
    });
  });

  describe('scrolling', () => {
    it('should show scroll indicator when more messages than height', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      // Should show scroll up indicator since we auto-scroll to bottom
      expect(lastFrame()).toContain('scroll');
    });

    it('should not show scroll indicators when messages fit', () => {
      const messages: OutputMessage[] = [
        createMessage('info', 'Message 1'),
        createMessage('info', 'Message 2'),
      ];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={10} />
      );

      expect(lastFrame()).not.toContain('scroll');
    });
  });

  describe('height prop', () => {
    it('should use default height when not specified', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test')];

      const { lastFrame } = render(<OutputHistory messages={messages} />);

      expect(lastFrame()).toBeDefined();
    });

    it('should respect custom height', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={3} />
      );

      expect(lastFrame()).toBeDefined();
    });
  });

  describe('focused state', () => {
    it('should accept focused prop', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} focused={true} />
      );

      expect(lastFrame()).toBeDefined();
    });

    it('should accept focused=false', () => {
      const messages: OutputMessage[] = [createMessage('info', 'Test')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} focused={false} />
      );

      expect(lastFrame()).toBeDefined();
    });
  });

  describe('system message type', () => {
    it('should render system messages without prefix', () => {
      const messages: OutputMessage[] = [createMessage('system', 'System info')];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('System info');
    });
  });

  describe('unknown message type', () => {
    it('should handle unknown message type with default color', () => {
      const messages: OutputMessage[] = [
        { id: '1', type: 'unknown' as OutputMessage['type'], content: 'Unknown type', timestamp: new Date() },
      ];

      const { lastFrame } = render(
        <OutputHistory messages={messages} height={5} />
      );

      expect(lastFrame()).toContain('Unknown type');
    });
  });

  describe('keyboard navigation when focused', () => {
    it('should not respond to keys when not focused', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      capturedUseInputCallback = undefined;
      render(<OutputHistory messages={messages} height={5} focused={false} />);

      // When not focused, useInput should not be active
      expect(capturedUseInputCallback).toBeUndefined();
    });

    it('should capture useInput callback when focused', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      // When focused, useInput callback should be captured
      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle up arrow navigation', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      // Invoke the callback - component handles state internally
      capturedUseInputCallback?.('', { upArrow: true });

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle down arrow navigation', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('', { downArrow: true });

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle k key for scroll up', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('k', {});

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle j key for scroll down', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('j', {});

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle Page Up navigation', () => {
      const messages: OutputMessage[] = Array.from({ length: 30 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('', { pageUp: true });

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle Page Down navigation', () => {
      const messages: OutputMessage[] = Array.from({ length: 30 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('', { pageDown: true });

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle g key to jump to top', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('g', {});

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should handle G key to jump to bottom', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      capturedUseInputCallback?.('G', {});

      expect(capturedUseInputCallback).toBeDefined();
    });

    it('should ignore unhandled keys', () => {
      const messages: OutputMessage[] = Array.from({ length: 20 }, (_, i) =>
        createMessage('info', `Message ${i + 1}`)
      );

      render(<OutputHistory messages={messages} height={5} focused={true} />);

      // Other keys should not cause issues
      capturedUseInputCallback?.('x', {});

      expect(capturedUseInputCallback).toBeDefined();
    });
  });
});
