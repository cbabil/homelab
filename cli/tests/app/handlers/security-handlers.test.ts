/**
 * Tests for security command handlers.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../../../src/lib/security.js', () => ({
  getLockedAccounts: vi.fn(),
  unlockAccount: vi.fn(),
}));

import { handleSecurityCommand } from '../../../src/app/handlers/security-handlers.js';
import { getLockedAccounts, unlockAccount } from '../../../src/lib/security.js';
import type { AppState } from '../../../src/app/types.js';

describe('security-handlers', () => {
  let mockState: AppState;

  beforeEach(() => {
    vi.clearAllMocks();
    mockState = {
      mcpConnected: true,
      mcpUrl: 'http://localhost:8000/mcp',
      mcpConnecting: false,
      mcpError: null,
      authenticated: true,
      username: 'admin',
      history: [],
      inputValue: '',
      commandHistory: [],
      historyIndex: -1,
      isRunningCommand: false,
    };
  });

  describe('list-locked', () => {
    it('should return locked accounts', async () => {
      vi.mocked(getLockedAccounts).mockResolvedValue([
        {
          id: 'lock-1',
          identifier: 'user1',
          identifier_type: 'username',
          attempt_count: 5,
          locked_at: '2024-01-15T10:00:00Z',
          lock_expires_at: null,
          ip_address: '192.168.1.1',
        },
      ]);

      const results = await handleSecurityCommand('list-locked', [], mockState);

      expect(results[0]!.content).toContain('1 locked account');
      expect(results[1]!.content).toContain('lock-1');
      expect(results[1]!.content).toContain('user1');
    });

    it('should handle no locked accounts', async () => {
      vi.mocked(getLockedAccounts).mockResolvedValue([]);

      const results = await handleSecurityCommand('list-locked', [], mockState);

      expect(results[0]!.content).toContain('No locked accounts');
    });
  });

  describe('unlock', () => {
    it('should unlock an account', async () => {
      vi.mocked(unlockAccount).mockResolvedValue({ success: true, lock_id: 'lock-1' });

      const results = await handleSecurityCommand('unlock', ['lock-1'], mockState);

      expect(unlockAccount).toHaveBeenCalledWith('lock-1', 'admin', undefined);
      expect(results[0]!.type).toBe('success');
      expect(results[0]!.content).toContain('lock-1');
    });

    it('should pass notes when provided', async () => {
      vi.mocked(unlockAccount).mockResolvedValue({ success: true, lock_id: 'lock-1' });

      await handleSecurityCommand('unlock', ['lock-1', 'user', 'requested'], mockState);

      expect(unlockAccount).toHaveBeenCalledWith('lock-1', 'admin', 'user requested');
    });

    it('should return error when lock-id missing', async () => {
      const results = await handleSecurityCommand('unlock', [], mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });

    it('should return error when not logged in', async () => {
      mockState.username = null;

      const results = await handleSecurityCommand('unlock', ['lock-1'], mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('logged in');
    });

    it('should handle unlock failure', async () => {
      vi.mocked(unlockAccount).mockResolvedValue({
        success: false,
        error: 'Lock not found',
      });

      const results = await handleSecurityCommand('unlock', ['lock-1'], mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Lock not found');
    });
  });

  describe('unknown subcommand', () => {
    it('should return error for unknown subcommand', async () => {
      const results = await handleSecurityCommand('unknown', [], mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Unknown security subcommand');
    });

    it('should return usage when no subcommand', async () => {
      const results = await handleSecurityCommand('', [], mockState);

      expect(results[0]!.type).toBe('error');
      expect(results[0]!.content).toContain('Usage:');
    });
  });
});
