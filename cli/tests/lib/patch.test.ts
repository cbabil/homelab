/**
 * Tests for patch (update) module.
 *
 * Tests update checking and version retrieval functions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock mcp-client before importing
vi.mock('../../src/lib/mcp-client.js', () => ({
  getMCPClient: vi.fn()
}));

import { getComponentVersions, checkForUpdates } from '../../src/lib/patch.js';
import { getMCPClient } from '../../src/lib/mcp-client.js';

describe('patch module', () => {
  let mockClient: {
    callTool: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    mockClient = {
      callTool: vi.fn()
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getComponentVersions', () => {
    it('should return component versions from MCP response', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          backend: '2.0.0',
          frontend: '2.1.0',
          api: '1.5.0'
        }
      });

      const result = await getComponentVersions();

      expect(result).toEqual({
        backend: '2.0.0',
        frontend: '2.1.0',
        api: '1.5.0'
      });
      expect(mockClient.callTool).toHaveBeenCalledWith('get_component_versions');
    });

    it('should return default versions when API call fails', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Connection failed'
      });

      const result = await getComponentVersions();

      expect(result).toEqual({
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0'
      });
    });

    it('should return default versions when data is missing', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null
      });

      const result = await getComponentVersions();

      expect(result).toEqual({
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0'
      });
    });
  });

  describe('checkForUpdates', () => {
    it('should return update information when update is available', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          components: {
            backend: '2.0.0',
            frontend: '2.1.0',
            api: '1.5.0'
          },
          latest_version: 'v2.1.0',
          update_available: true,
          release_url: 'https://github.com/project/releases/v2.1.0',
          release_notes: 'Bug fixes and improvements',
          message: 'New version available'
        }
      });

      const result = await checkForUpdates();

      expect(result).toEqual({
        success: true,
        components: {
          backend: '2.0.0',
          frontend: '2.1.0',
          api: '1.5.0'
        },
        latest_version: 'v2.1.0',
        update_available: true,
        release_url: 'https://github.com/project/releases/v2.1.0',
        release_notes: 'Bug fixes and improvements',
        message: 'New version available'
      });
      expect(mockClient.callTool).toHaveBeenCalledWith('check_updates');
    });

    it('should return no update available when on latest version', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          components: {
            backend: '2.1.0',
            frontend: '2.1.0',
            api: '1.5.0'
          },
          latest_version: 'v2.1.0',
          update_available: false,
          message: 'You are on the latest version'
        }
      });

      const result = await checkForUpdates();

      expect(result.success).toBe(true);
      expect(result.update_available).toBe(false);
      expect(result.message).toBe('You are on the latest version');
    });

    it('should return error when API call fails', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Failed to connect to update server'
      });

      const result = await checkForUpdates();

      expect(result).toEqual({
        success: false,
        update_available: false,
        error: 'Failed to connect to update server'
      });
    });

    it('should use default versions when components are missing', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          components: {},
          update_available: false
        }
      });

      const result = await checkForUpdates();

      expect(result.success).toBe(true);
      expect(result.components).toEqual({
        backend: '1.0.0',
        frontend: '1.0.0',
        api: '1.0.0'
      });
    });

    it('should handle missing data gracefully', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: null
      });

      const result = await checkForUpdates();

      expect(result).toEqual({
        success: false,
        update_available: false,
        error: 'Failed to check for updates'
      });
    });

    it('should pass through optional fields when present', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          components: {
            backend: '1.0.0',
            frontend: '1.0.0',
            api: '1.0.0'
          },
          latest_version: 'v1.5.0',
          update_available: true,
          release_url: 'https://github.com/releases/v1.5.0',
          release_notes: '# Release Notes\n- Feature 1\n- Feature 2'
        }
      });

      const result = await checkForUpdates();

      expect(result.release_url).toBe('https://github.com/releases/v1.5.0');
      expect(result.release_notes).toBe('# Release Notes\n- Feature 1\n- Feature 2');
    });
  });
});
