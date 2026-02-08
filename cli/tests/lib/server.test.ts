/**
 * Tests for server lib module.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn(),
}));

import { listServers } from '../../src/lib/server.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';

describe('server', () => {
  let mockClient: { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockClient = { callTool: vi.fn() };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('listServers', () => {
    it('should return servers on success', async () => {
      const servers = [
        { id: 'srv-001', name: 'Web', hostname: 'web.local', status: 'online' },
        { id: 'srv-002', name: 'DB', hostname: 'db.local', status: 'offline' },
      ];

      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { servers },
      });

      const result = await listServers();
      expect(result).toEqual(servers);
      expect(mockClient.callTool).toHaveBeenCalledWith('list_servers', {});
    });

    it('should throw on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Not authorized',
      });

      await expect(listServers()).rejects.toThrow('Not authorized');
    });

    it('should return empty array when no data', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null,
      });

      const result = await listServers();
      expect(result).toEqual([]);
    });
  });
});
