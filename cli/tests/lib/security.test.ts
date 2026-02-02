/**
 * Tests for security module.
 *
 * Tests locked accounts listing and unlock operations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

import { getMCPClient } from '../../src/lib/mcp-client.js';
import { getLockedAccounts, unlockAccount } from '../../src/lib/security.js';

describe('Security Module', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockClient = {
      callTool: vi.fn(),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getLockedAccounts', () => {
    it('should return empty array when no accounts found', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { accounts: [], count: 0 },
      });

      const result = await getLockedAccounts();

      expect(result).toEqual([]);
      expect(mockClient.callTool).toHaveBeenCalledWith('get_locked_accounts', {
        include_expired: false,
        include_unlocked: false,
      });
    });

    it('should return locked accounts when found', async () => {
      const mockAccounts = [
        {
          id: 'lock-1',
          identifier: 'user1',
          identifier_type: 'username',
          attempt_count: 5,
          locked_at: '2024-01-01T00:00:00Z',
          lock_expires_at: '2024-01-01T01:00:00Z',
          ip_address: '192.168.1.1',
        },
      ];

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { accounts: mockAccounts, count: 1 },
      });

      const result = await getLockedAccounts();

      expect(result).toHaveLength(1);
      expect(result[0].identifier).toBe('user1');
    });

    it('should pass includeExpired flag', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { accounts: [], count: 0 },
      });

      await getLockedAccounts(true, false);

      expect(mockClient.callTool).toHaveBeenCalledWith('get_locked_accounts', {
        include_expired: true,
        include_unlocked: false,
      });
    });

    it('should pass includeUnlocked flag', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { accounts: [], count: 0 },
      });

      await getLockedAccounts(false, true);

      expect(mockClient.callTool).toHaveBeenCalledWith('get_locked_accounts', {
        include_expired: false,
        include_unlocked: true,
      });
    });

    it('should return empty array on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection failed',
      });

      const result = await getLockedAccounts();

      expect(result).toEqual([]);
    });
  });

  describe('unlockAccount', () => {
    it('should return success when account is unlocked', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { lock_id: 'lock-1' },
      });

      const result = await unlockAccount('lock-1', 'admin', 'Test unlock');

      expect(result.success).toBe(true);
      expect(result.lock_id).toBe('lock-1');
      expect(mockClient.callTool).toHaveBeenCalledWith('update_account_lock', {
        lock_id: 'lock-1',
        action: 'unlock',
        admin_username: 'admin',
        notes: 'Test unlock',
      });
    });

    it('should use default notes if not provided', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { lock_id: 'lock-1' },
      });

      await unlockAccount('lock-1', 'admin');

      expect(mockClient.callTool).toHaveBeenCalledWith('update_account_lock', {
        lock_id: 'lock-1',
        action: 'unlock',
        admin_username: 'admin',
        notes: 'Unlocked via CLI by admin',
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Lock not found',
      });

      const result = await unlockAccount('invalid-lock', 'admin');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Lock not found');
    });
  });
});
