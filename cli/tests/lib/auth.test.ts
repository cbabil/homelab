/**
 * Tests for auth module.
 *
 * Tests authentication functions including checkSystemSetup,
 * authenticateAdmin, requireAdmin, and auth state management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock dependencies before importing the module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn()
}));

vi.mock('inquirer', () => ({
  default: {
    prompt: vi.fn()
  }
}));

vi.mock('chalk', () => ({
  default: {
    cyan: (s: string) => s,
    red: (s: string) => s,
    yellow: (s: string) => s,
    green: (s: string) => s
  }
}));

// Import after mocks are set up
import {
  checkSystemSetup,
  authenticateAdmin,
  requireAdmin,
  isAuthenticated,
  getAuthToken,
  clearAuth
} from '../../src/lib/auth.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';
import inquirer from 'inquirer';

describe('auth module', () => {
  let mockClient: {
    callTool: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    clearAuth(); // Reset auth state before each test

    // Set up mock MCP client
    mockClient = {
      callTool: vi.fn()
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
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password123'
      });

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

      const result = await authenticateAdmin();

      expect(result).toBe(true);
      expect(isAuthenticated()).toBe(true);
      expect(getAuthToken()).toBe('jwt-token-123');
    });

    it('should reject non-admin users', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'user',
        password: 'password123'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'jwt-token-123',
          user: {
            id: '2',
            username: 'user',
            role: 'user' // Not admin
          }
        }
      });

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const result = await authenticateAdmin();

      expect(result).toBe(false);
      expect(isAuthenticated()).toBe(false);
      consoleSpy.mockRestore();
    });

    it('should return false with invalid credentials', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'wrongpassword'
      });

      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Invalid credentials'
      });

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const result = await authenticateAdmin();

      expect(result).toBe(false);
      expect(isAuthenticated()).toBe(false);
      consoleSpy.mockRestore();
    });

    it('should call login tool with correct parameters', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'testadmin',
        password: 'testpass'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'testadmin', role: 'admin' }
        }
      });

      await authenticateAdmin();

      expect(mockClient.callTool).toHaveBeenCalledWith('login', {
        username: 'testadmin',
        password: 'testpass'
      });
    });
  });

  describe('requireAdmin', () => {
    it('should allow access without auth when system needs setup', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { needs_setup: true }
      });

      const result = await requireAdmin();

      expect(result).toBe(true);
    });

    it('should require authentication when system is set up', async () => {
      // First call: checkSystemSetup returns false
      mockClient.callTool.mockResolvedValueOnce({
        success: true,
        data: { needs_setup: false }
      });

      // Second call: login succeeds
      mockClient.callTool.mockResolvedValueOnce({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const result = await requireAdmin();

      expect(result).toBe(true);
      expect(mockClient.callTool).toHaveBeenCalledTimes(2);
      consoleSpy.mockRestore();
    });
  });

  describe('isAuthenticated', () => {
    it('should return false initially', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('should return true after successful authentication', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin();

      expect(isAuthenticated()).toBe(true);
    });

    it('should return false after clearAuth', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin();
      expect(isAuthenticated()).toBe(true);

      clearAuth();
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('getAuthToken', () => {
    it('should return null initially', () => {
      expect(getAuthToken()).toBeNull();
    });

    it('should return token after authentication', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'my-auth-token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin();

      expect(getAuthToken()).toBe('my-auth-token');
    });

    it('should return null after clearAuth', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin();
      clearAuth();

      expect(getAuthToken()).toBeNull();
    });
  });

  describe('clearAuth', () => {
    it('should reset all auth state', async () => {
      vi.mocked(inquirer.prompt).mockResolvedValue({
        username: 'admin',
        password: 'password'
      });

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          token: 'token',
          user: { id: '1', username: 'admin', role: 'admin' }
        }
      });

      await authenticateAdmin();

      // Verify authenticated
      expect(isAuthenticated()).toBe(true);
      expect(getAuthToken()).not.toBeNull();

      // Clear auth
      clearAuth();

      // Verify cleared
      expect(isAuthenticated()).toBe(false);
      expect(getAuthToken()).toBeNull();
    });

    it('should be safe to call multiple times', () => {
      expect(() => {
        clearAuth();
        clearAuth();
        clearAuth();
      }).not.toThrow();

      expect(isAuthenticated()).toBe(false);
    });
  });
});
