/**
 * Tests for auth module.
 *
 * Tests checkSystemSetup, authenticateAdmin, and clearAuth.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock dependencies before importing the module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn()
}));

// Import after mocks are set up
import {
  checkSystemSetup,
  authenticateAdmin,
  clearAuth,
  getAuthToken,
  getRefreshToken,
  getUsername,
  getRole,
  revokeToken,
  refreshAuthToken,
} from '../../src/lib/auth.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';

describe('auth module', () => {
  let mockClient: {
    callTool: ReturnType<typeof vi.fn>;
    callToolRaw: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    clearAuth();

    mockClient = {
      callTool: vi.fn(),
      callToolRaw: vi.fn(),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);
  });

  afterEach(() => {
    clearAuth();
  });

  describe('checkSystemSetup', () => {
    it('should return true when system needs setup', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { needs_setup: true, is_setup: false }
      });

      const result = await checkSystemSetup();

      expect(result).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledWith('get_system_setup', {});
    });

    it('should return false when system is already set up', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { needs_setup: false, is_setup: true }
      });

      const result = await checkSystemSetup();

      expect(result).toBe(false);
    });

    it('should return false when API call fails', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection error'
      });

      const result = await checkSystemSetup();

      expect(result).toBe(false);
    });

    it('should return false when response data is missing', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null
      });

      const result = await checkSystemSetup();

      expect(result).toBe(false);
    });
  });

  describe('authenticateAdmin', () => {
    it('should authenticate successfully with valid admin credentials', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          user: {
            id: '1',
            username: 'admin',
            role: 'admin'
          }
        }
      });

      const result = await authenticateAdmin('admin', 'password123');

      expect(result).toEqual({ success: true });
    });

    it('should reject non-admin users', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          user: {
            id: '2',
            username: 'user',
            role: 'user'
          }
        }
      });

      const result = await authenticateAdmin('user', 'password123');

      expect(result).toEqual({ success: false, error: 'Only admin users can run CLI commands' });
    });

    it('should return failure with invalid credentials', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Invalid credentials'
      });

      const result = await authenticateAdmin('admin', 'wrongpassword');

      expect(result).toEqual({ success: false, error: 'Invalid credentials' });
    });

    it('should reject invalid token from server', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'short',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      const result = await authenticateAdmin('admin', 'password');

      expect(result).toEqual({ success: false, error: 'Invalid token received from server' });
      expect(getAuthToken()).toBeNull();
    });

    it('should reject empty token from server', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: '',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      const result = await authenticateAdmin('admin', 'password');

      expect(result).toEqual({ success: false, error: 'Invalid token received from server' });
    });

    it('should call login tool with correct parameters', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'valid-token-1234',
          user: { id: '1', username: 'testadmin', role: 'admin' }
        }
      });

      await authenticateAdmin('testadmin', 'testpass');

      expect(mockClient.callTool).toHaveBeenCalledWith('login', {
        username: 'testadmin',
        password: 'testpass'
      });
    });
  });

  describe('getAuthToken', () => {
    it('should return null when not authenticated', () => {
      clearAuth();
      expect(getAuthToken()).toBeNull();
    });

    it('should return token after successful authentication', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-abc',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin('admin', 'password');
      expect(getAuthToken()).toBe('jwt-token-abc');
    });

    it('should return null after clearAuth', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-abc',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin('admin', 'password');
      clearAuth();
      expect(getAuthToken()).toBeNull();
    });
  });

  describe('clearAuth', () => {
    it('should be safe to call multiple times', () => {
      expect(() => {
        clearAuth();
        clearAuth();
        clearAuth();
      }).not.toThrow();
    });
  });

  describe('getRefreshToken', () => {
    it('should return null when not authenticated', () => {
      expect(getRefreshToken()).toBeNull();
    });

    it('should return refresh token after authentication with refresh token', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-valid',
          refresh_token: 'refresh-token-abc',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      await authenticateAdmin('admin', 'password');
      expect(getRefreshToken()).toBe('refresh-token-abc');
    });

    it('should return null after authentication without refresh token', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-valid',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      await authenticateAdmin('admin', 'password');
      expect(getRefreshToken()).toBeNull();
    });
  });

  describe('getUsername and getRole', () => {
    it('should return null when not authenticated', () => {
      expect(getUsername()).toBeNull();
      expect(getRole()).toBeNull();
    });

    it('should return username and role after authentication', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-valid',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      await authenticateAdmin('admin', 'password');
      expect(getUsername()).toBe('admin');
      expect(getRole()).toBe('admin');
    });
  });

  describe('revokeToken', () => {
    it('should revoke both access and refresh tokens', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          refresh_token: 'refresh-token-456',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockResolvedValue({ success: true });

      await revokeToken();

      expect(mockClient.callToolRaw).toHaveBeenCalledWith('revoke_token', {
        token: 'jwt-token-123',
      });
      expect(mockClient.callToolRaw).toHaveBeenCalledWith('revoke_token', {
        token: 'refresh-token-456',
      });
      expect(getAuthToken()).toBeNull();
      expect(getRefreshToken()).toBeNull();
    });

    it('should clear auth before server calls (no race condition)', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      // Verify auth is cleared before callToolRaw resolves
      mockClient.callToolRaw.mockImplementation(async () => {
        expect(getAuthToken()).toBeNull();
        return { success: true };
      });

      await revokeToken();
    });

    it('should clear auth even when MCP call fails', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-valid',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockRejectedValue(new Error('Network error'));

      await revokeToken();

      expect(getAuthToken()).toBeNull();
    });

    it('should be a no-op when no token is present', async () => {
      await revokeToken();

      expect(mockClient.callToolRaw).not.toHaveBeenCalled();
      expect(getAuthToken()).toBeNull();
    });

    it('should revoke refresh token even when access token revocation fails', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          refresh_token: 'refresh-token-456',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      // Match on token value to decide which call fails, not call order
      mockClient.callToolRaw.mockImplementation(async (_name: string, args: Record<string, unknown>) => {
        if (args.token === 'jwt-token-123') {
          throw new Error('Network error');
        }
        return { success: true };
      });

      await revokeToken();

      expect(mockClient.callToolRaw).toHaveBeenCalledTimes(2);
      expect(mockClient.callToolRaw).toHaveBeenCalledWith('revoke_token', {
        token: 'jwt-token-123',
      });
      expect(mockClient.callToolRaw).toHaveBeenCalledWith('revoke_token', {
        token: 'refresh-token-456',
      });
    });
  });

  describe('refreshAuthToken', () => {
    it('should update tokens on successful refresh', async () => {
      // First authenticate to set a refresh token
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      // Mock the refresh call
      mockClient.callToolRaw.mockResolvedValue({
        success: true,
        data: {
          token: 'new-token-valid',
          refresh_token: 'new-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      const result = await refreshAuthToken();

      expect(result).toBe(true);
      expect(getAuthToken()).toBe('new-token-valid');
      expect(getRefreshToken()).toBe('new-refresh');
      expect(mockClient.callToolRaw).toHaveBeenCalledWith('refresh_token', {
        refresh_token: 'old-refresh',
      });
    });

    it('should clear auth on refresh failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockResolvedValue({
        success: false,
        error: 'Invalid refresh token',
      });

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should clear auth when no refresh token is stored', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-valid',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should clear auth when refresh call throws', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockRejectedValue(new Error('Network error'));

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should clear auth when refresh returns invalid token', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockResolvedValue({
        success: true,
        data: {
          token: 'short',
          refresh_token: 'new-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should abort refresh if auth state changed during in-flight call', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      // Simulate a logout happening while the refresh call is in-flight
      mockClient.callToolRaw.mockImplementation(async () => {
        clearAuth();
        return {
          success: true,
          data: {
            token: 'new-token-valid',
            refresh_token: 'new-refresh',
            user: { id: '1', username: 'admin', role: 'admin' },
          },
        };
      });

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should return false without calling server when auth is cleared', async () => {
      clearAuth();

      const result = await refreshAuthToken();

      expect(result).toBe(false);
      expect(mockClient.callToolRaw).not.toHaveBeenCalled();
    });

    it('should deduplicate concurrent refresh calls', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'old-token-valid',
          refresh_token: 'old-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });
      await authenticateAdmin('admin', 'password');

      mockClient.callToolRaw.mockResolvedValue({
        success: true,
        data: {
          token: 'new-token-valid',
          refresh_token: 'new-refresh',
          user: { id: '1', username: 'admin', role: 'admin' },
        },
      });

      const [result1, result2] = await Promise.all([
        refreshAuthToken(),
        refreshAuthToken(),
      ]);

      expect(result1).toBe(true);
      expect(result2).toBe(true);
      expect(mockClient.callToolRaw).toHaveBeenCalledTimes(1);
    });
  });
});
