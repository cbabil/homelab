/**
 * Tests for backup module.
 *
 * Tests backup export and import operations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

import { getMCPClient } from '../../src/lib/mcp-client.js';
import { exportBackup, importBackup } from '../../src/lib/backup.js';

describe('Backup Module', () => {
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

  describe('exportBackup', () => {
    it('should return success with path and checksum', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          path: '/tmp/backup.enc',
          checksum: 'abc123def456',
        },
      });

      const result = await exportBackup('/tmp/backup.enc', 'password123');

      expect(result.success).toBe(true);
      expect(result.path).toBe('/tmp/backup.enc');
      expect(result.checksum).toBe('abc123def456');
      expect(mockClient.callTool).toHaveBeenCalledWith('export_backup', {
        output_path: '/tmp/backup.enc',
        password: 'password123',
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Permission denied',
      });

      const result = await exportBackup('/invalid/path', 'password');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Permission denied');
    });

    it('should handle missing response data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: undefined,
      });

      const result = await exportBackup('/tmp/backup.enc', 'password');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to export backup');
    });
  });

  describe('importBackup', () => {
    it('should return success with import counts', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          users_imported: 5,
          servers_imported: 10,
          apps_imported: 3,
        },
      });

      const result = await importBackup('/tmp/backup.enc', 'password123', false);

      expect(result.success).toBe(true);
      expect(result.users_imported).toBe(5);
      expect(result.servers_imported).toBe(10);
      expect(result.apps_imported).toBe(3);
      expect(mockClient.callTool).toHaveBeenCalledWith('import_backup', {
        input_path: '/tmp/backup.enc',
        password: 'password123',
        overwrite: false,
      });
    });

    it('should pass overwrite flag', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          users_imported: 0,
          servers_imported: 0,
        },
      });

      await importBackup('/tmp/backup.enc', 'password', true);

      expect(mockClient.callTool).toHaveBeenCalledWith('import_backup', {
        input_path: '/tmp/backup.enc',
        password: 'password',
        overwrite: true,
      });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Invalid password',
      });

      const result = await importBackup('/tmp/backup.enc', 'wrong');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid password');
    });

    it('should handle import without apps', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          users_imported: 2,
          servers_imported: 3,
        },
      });

      const result = await importBackup('/tmp/backup.enc', 'password');

      expect(result.success).toBe(true);
      expect(result.users_imported).toBe(2);
      expect(result.servers_imported).toBe(3);
      expect(result.apps_imported).toBeUndefined();
    });
  });
});
