/**
 * Tests for admin module.
 *
 * Tests MCP client functions for admin operations:
 * createAdmin and resetPassword.
 */

import { describe, it, expect, vi, beforeAll, beforeEach, afterAll } from 'vitest';

describe('Admin MCP Functions', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };
  let createAdmin: typeof import('../../src/lib/admin.js').createAdmin;
  let resetPassword: typeof import('../../src/lib/admin.js').resetPassword;

  beforeAll(async () => {
    // Mock the mcp-client module
    vi.mock('../../src/lib/mcp-client.js', () => ({
      getMCPClient: vi.fn(),
    }));

    mockClient = {
      callTool: vi.fn(),
    };

    const mcpModule = await import('../../src/lib/mcp-client.js');
    vi.mocked(mcpModule.getMCPClient).mockReturnValue(
      mockClient as unknown as ReturnType<typeof mcpModule.getMCPClient>,
    );

    // Now import the admin module
    const adminModule = await import('../../src/lib/admin.js');
    createAdmin = adminModule.createAdmin;
    resetPassword = adminModule.resetPassword;
  });

  beforeEach(async () => {
    vi.clearAllMocks();
    const mcpModule = await import('../../src/lib/mcp-client.js');
    vi.mocked(mcpModule.getMCPClient).mockReturnValue(
      mockClient as unknown as ReturnType<typeof mcpModule.getMCPClient>,
    );
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  describe('createAdmin via MCP', () => {
    it('should call MCP with correct arguments', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { username: 'newadmin' },
      });

      await createAdmin('newadmin', 'password123');

      expect(mockClient.callTool).toHaveBeenCalledWith('create_initial_admin', {
        username: 'newadmin',
        password: 'password123',
      });
    });

    it('should return success true on success', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { username: 'newadmin' },
      });

      const result = await createAdmin('newadmin', 'password123');
      expect(result).toEqual({ success: true });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Username already exists',
      });

      const result = await createAdmin('existing', 'password123');
      expect(result).toEqual({
        success: false,
        error: 'Username already exists',
      });
    });
  });

  describe('resetPassword via MCP', () => {
    it('should call MCP with correct arguments', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
      });

      await resetPassword('admin', 'newpassword123');

      expect(mockClient.callTool).toHaveBeenCalledWith('reset_user_password', {
        username: 'admin',
        password: 'newpassword123',
      });
    });

    it('should return success true on success', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
      });

      const result = await resetPassword('admin', 'newpassword123');
      expect(result).toEqual({ success: true });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'User not found',
      });

      const result = await resetPassword('nonexistent', 'newpassword');
      expect(result).toEqual({
        success: false,
        error: 'User not found',
      });
    });
  });
});
