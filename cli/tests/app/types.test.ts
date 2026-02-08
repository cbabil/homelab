/**
 * Tests for app types module.
 */

import { describe, it, expect } from 'vitest';
import {
  createMessage,
  initialAppState,
  type OutputMessage,
  type MessageType,
} from '../../src/app/types.js';

describe('app/types', () => {
  describe('createMessage', () => {
    it('should create a message with correct type and content', () => {
      const msg = createMessage('info', 'Test message');

      expect(msg.type).toBe('info');
      expect(msg.content).toBe('Test message');
    });

    it('should generate unique IDs for each message', () => {
      const msg1 = createMessage('info', 'Message 1');
      const msg2 = createMessage('info', 'Message 2');

      expect(msg1.id).not.toBe(msg2.id);
    });

    it('should set timestamp to current time', () => {
      const before = new Date();
      const msg = createMessage('success', 'Test');
      const after = new Date();

      expect(msg.timestamp.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(msg.timestamp.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it('should support all message types', () => {
      const types: MessageType[] = ['info', 'success', 'error', 'system'];

      for (const type of types) {
        const msg = createMessage(type, `${type} message`);
        expect(msg.type).toBe(type);
      }
    });

    it('should have id starting with msg-', () => {
      const msg = createMessage('info', 'Test');
      expect(msg.id).toMatch(/^msg-\d+-\d+$/);
    });
  });

  describe('initialAppState', () => {
    it('should have correct default values', () => {
      expect(initialAppState.mcpConnected).toBe(false);
      expect(initialAppState.mcpConnecting).toBe(true);
      expect(initialAppState.mcpError).toBeNull();
      expect(initialAppState.authenticated).toBe(false);
      expect(initialAppState.username).toBeNull();
      expect(initialAppState.history).toEqual([]);
      expect(initialAppState.inputValue).toBe('');
      expect(initialAppState.commandHistory).toEqual([]);
      expect(initialAppState.historyIndex).toBe(-1);
      expect(initialAppState.isRunningCommand).toBe(false);
    });

    it('should have default MCP URL', () => {
      expect(initialAppState.mcpUrl).toBe('http://localhost:8000/mcp');
    });
  });
});
