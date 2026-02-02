/**
 * Server Info Service Tests
 *
 * Tests for server information fetching functionality.
 * Note: The current implementation returns undefined values as placeholders
 * for real SSH integration that will be implemented with the backend.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { serverInfoService } from '../serverInfoService'
import { ServerConnection } from '@/types/server'

// Mock server for testing
const mockServer: ServerConnection = {
  id: 'test-server-1',
  name: 'Test Server',
  host: '192.168.1.100',
  port: 22,
  username: 'testuser',
  auth_type: 'password',
  status: 'disconnected',
  created_at: '2024-01-01T00:00:00Z',
  docker_installed: false
}

describe('ServerInfoService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchServerInfo', () => {
    it('should successfully fetch server info', async () => {
      const result = await serverInfoService.fetchServerInfo(mockServer)

      expect(result.success).toBe(true)
      expect(result.system_info).toBeDefined()
      expect(result.message).toBe('Server information retrieved successfully')
    }, 10000) // Increase timeout for simulated delay

    it('should return system_info object with expected structure', async () => {
      const result = await serverInfoService.fetchServerInfo(mockServer)

      expect(result.success).toBe(true)
      expect(result.system_info).toBeDefined()

      // Current implementation returns undefined values as placeholders
      // for real SSH integration
      if (result.system_info) {
        expect(result.system_info).toHaveProperty('os')
        expect(result.system_info).toHaveProperty('kernel')
        expect(result.system_info).toHaveProperty('architecture')
        expect(result.system_info).toHaveProperty('docker_version')
      }
    }, 10000)

    it('should handle server connection parameter', async () => {
      const result = await serverInfoService.fetchServerInfo(mockServer)

      // Should complete without throwing
      expect(result).toBeDefined()
      expect(result.success).toBe(true)
    }, 10000)

    it('should return correct message on success', async () => {
      const result = await serverInfoService.fetchServerInfo(mockServer)

      expect(result.message).toBe('Server information retrieved successfully')
    }, 10000)

    it('should return undefined fields as placeholders', async () => {
      // The current implementation returns undefined values
      // that will be populated when real SSH integration is added
      const result = await serverInfoService.fetchServerInfo(mockServer)

      expect(result.success).toBe(true)
      expect(result.system_info).toBeDefined()

      // Current placeholder implementation returns undefined values
      if (result.system_info) {
        // These are expected to be undefined until SSH integration is implemented
        expect(result.system_info.os).toBeUndefined()
        expect(result.system_info.architecture).toBeUndefined()
        expect(result.system_info.kernel).toBeUndefined()
      }
    }, 10000)

    it('should not throw errors for valid server connection', async () => {
      // Test that the service handles the request gracefully
      await expect(
        serverInfoService.fetchServerInfo(mockServer)
      ).resolves.not.toThrow()
    }, 10000)
  })
})