/**
 * Tests for signal-processor classifySignal function.
 */

import { describe, it, expect } from 'vitest';
import { classifySignal } from '../../src/app/signal-processor.js';
import { SIGNALS } from '../../src/app/signals.js';
import type { CommandResult } from '../../src/app/types.js';

function makeResult(content: string): CommandResult {
  return { type: 'system', content };
}

describe('classifySignal', () => {
  describe('simple signals (no payload)', () => {
    it('should classify CLEAR signal', () => {
      const action = classifySignal(makeResult(SIGNALS.CLEAR));
      expect(action).toEqual({ kind: 'clear' });
    });

    it('should classify LOGOUT signal', () => {
      const action = classifySignal(makeResult(SIGNALS.LOGOUT));
      expect(action).toEqual({ kind: 'logout' });
    });

    it('should classify LOGIN signal', () => {
      const action = classifySignal(makeResult(SIGNALS.LOGIN));
      expect(action).toEqual({ kind: 'login' });
    });

    it('should classify REFRESH signal', () => {
      const action = classifySignal(makeResult(SIGNALS.REFRESH));
      expect(action).toEqual({ kind: 'refresh' });
    });

    it('should classify SETUP signal', () => {
      const action = classifySignal(makeResult(SIGNALS.SETUP));
      expect(action).toEqual({ kind: 'setup' });
    });
  });

  describe('signals with payloads', () => {
    it('should classify RESET_PASSWORD with username', () => {
      const action = classifySignal(makeResult(`${SIGNALS.RESET_PASSWORD}admin`));
      expect(action).toEqual({ kind: 'reset_password', username: 'admin' });
    });

    it('should classify BACKUP_EXPORT with path', () => {
      const action = classifySignal(makeResult(`${SIGNALS.BACKUP_EXPORT}./backup.enc`));
      expect(action).toEqual({ kind: 'backup_export', path: './backup.enc' });
    });

    it('should classify BACKUP_IMPORT with path', () => {
      const action = classifySignal(makeResult(`${SIGNALS.BACKUP_IMPORT}./data.enc`));
      expect(action).toEqual({ kind: 'backup_import', path: './data.enc', overwrite: false });
    });

    it('should classify BACKUP_IMPORT_OVERWRITE with path', () => {
      const action = classifySignal(makeResult(`${SIGNALS.BACKUP_IMPORT_OVERWRITE}./data.enc`));
      expect(action).toEqual({ kind: 'backup_import', path: './data.enc', overwrite: true });
    });

    it('should classify VIEW with valid target', () => {
      const action = classifySignal(makeResult(`${SIGNALS.VIEW}agents`));
      expect(action).toEqual({ kind: 'view', target: 'agents' });
    });

    it('should classify VIEW for each valid view mode', () => {
      for (const view of ['dashboard', 'agents', 'logs', 'settings'] as const) {
        const action = classifySignal(makeResult(`${SIGNALS.VIEW}${view}`));
        expect(action).toEqual({ kind: 'view', target: view });
      }
    });
  });

  describe('prefix overlap ordering', () => {
    it('should match BACKUP_IMPORT_OVERWRITE before BACKUP_IMPORT', () => {
      const action = classifySignal(makeResult(`${SIGNALS.BACKUP_IMPORT_OVERWRITE}/tmp/file.enc`));
      expect(action.kind).toBe('backup_import');
      if (action.kind === 'backup_import') {
        expect(action.overwrite).toBe(true);
        expect(action.path).toBe('/tmp/file.enc');
      }
    });

    it('should match BACKUP_IMPORT when not OVERWRITE', () => {
      const action = classifySignal(makeResult(`${SIGNALS.BACKUP_IMPORT}/tmp/file.enc`));
      expect(action.kind).toBe('backup_import');
      if (action.kind === 'backup_import') {
        expect(action.overwrite).toBe(false);
        expect(action.path).toBe('/tmp/file.enc');
      }
    });
  });

  describe('invalid view targets', () => {
    it('should fall through to message for invalid view target', () => {
      const result = makeResult(`${SIGNALS.VIEW}invalid`);
      const action = classifySignal(result);
      expect(action).toEqual({ kind: 'message', result });
    });

    it('should fall through to message for empty view target', () => {
      const result = makeResult(SIGNALS.VIEW);
      const action = classifySignal(result);
      expect(action).toEqual({ kind: 'message', result });
    });
  });

  describe('non-signal messages', () => {
    it('should return kind:message for regular text', () => {
      const result = makeResult('hello world');
      const action = classifySignal(result);
      expect(action).toEqual({ kind: 'message', result });
    });

    it('should return kind:message for empty content', () => {
      const result = makeResult('');
      const action = classifySignal(result);
      expect(action).toEqual({ kind: 'message', result });
    });

    it('should preserve the original CommandResult in message', () => {
      const result: CommandResult = { type: 'error', content: 'something failed' };
      const action = classifySignal(result);
      expect(action.kind).toBe('message');
      if (action.kind === 'message') {
        expect(action.result).toBe(result);
        expect(action.result.type).toBe('error');
      }
    });
  });
});
