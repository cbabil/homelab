/**
 * Server Info Service Tests
 * 
 * Tests for server information fetching functionality.
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
  created_at: '2024-01-01T00:00:00Z'
}

describe('ServerInfoService', () => {
  beforeEach(() => {
    // Reset any mocks
    vi.clearAllMocks()
  })

  describe('fetchServerInfo', () => {
    it('should successfully fetch server info', async () => {
      // Mock Math.random to avoid failures
      const originalRandom = Math.random
      Math.random = () => 0.5 // Greater than 0.1, no failure
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        
        expect(result.success).toBe(true)
        expect(result.system_info).toBeDefined()
        expect(result.message).toBe('Server information retrieved successfully')
        
        if (result.system_info) {
          expect(result.system_info.os).toBeDefined()
          expect(result.system_info.architecture).toBeDefined()
          expect(result.system_info.uptime).toBeDefined()
          expect(result.system_info.kernel).toBeDefined()
        }
      } finally {
        Math.random = originalRandom
      }
    })

    it('should handle connection failures', async () => {
      // Mock Math.random to always trigger failure
      const originalRandom = Math.random
      Math.random = () => 0.05 // Less than 0.1, should trigger failure
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        
        expect(result.success).toBe(false)
        expect(result.error).toContain('SSH connection failed')
        expect(result.message).toBe('Failed to fetch server information')
      } finally {
        Math.random = originalRandom
      }
    })

    it('should generate valid system info structure', async () => {
      // Mock Math.random to avoid failures
      const originalRandom = Math.random
      Math.random = () => 0.5 // Greater than 0.1, no failure
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        
        expect(result.success).toBe(true)
        expect(result.system_info).toMatchObject({
          os: expect.any(String),
          kernel: expect.any(String),
          architecture: expect.any(String),
          uptime: expect.any(String)
        })
        
        // Docker version is optional
        if (result.system_info?.docker_version) {
          expect(result.system_info.docker_version).toMatch(/^\d+\.\d+\.\d+$/)
        }
      } finally {
        Math.random = originalRandom
      }
    })

    it('should generate realistic uptime formats', async () => {
      const originalRandom = Math.random
      Math.random = () => 0.5
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        const uptime = result.system_info?.uptime
        
        expect(uptime).toBeDefined()
        if (uptime) {
          // Should match either "X days, H:MM" or "H:MM" format
          const uptimeRegex = /^(\d+ days, \d+:\d{2}|\d+:\d{2})$/
          expect(uptime).toMatch(uptimeRegex)
        }
      } finally {
        Math.random = originalRandom
      }
    })

    it('should generate valid architecture values', async () => {
      const originalRandom = Math.random
      Math.random = () => 0.5
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        const arch = result.system_info?.architecture
        
        expect(arch).toBeDefined()
        expect(['x86_64', 'aarch64', 'armv7l']).toContain(arch)
      } finally {
        Math.random = originalRandom
      }
    })

    it('should generate kernel versions matching OS', async () => {
      const originalRandom = Math.random
      Math.random = () => 0.5
      
      try {
        const result = await serverInfoService.fetchServerInfo(mockServer)
        const os = result.system_info?.os
        const kernel = result.system_info?.kernel
        
        expect(os).toBeDefined()
        expect(kernel).toBeDefined()
        
        if (os && kernel) {
          // Ubuntu kernels should contain 'generic'
          if (os === 'Ubuntu') {
            expect(kernel).toContain('generic')
          }
          // CentOS kernels should be simpler format
          if (os === 'CentOS') {
            expect(kernel).toMatch(/^\d+\.\d+\.\d+-\d+/)
          }
        }
      } finally {
        Math.random = originalRandom
      }
    })
  })
})