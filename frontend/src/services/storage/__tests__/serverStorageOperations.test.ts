/**
 * Server Storage Operations Tests
 * 
 * Tests for server storage operations including system info updates.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { updateServerSystemInfoInStorage } from '../serverStorageOperations'
import { StorageData } from '../storageTypes'
import { SystemInfo, ServerConnection } from '@/types/server'

// Mock the saveToStorage function
vi.mock('../storageHelpers', () => ({
  saveToStorage: vi.fn()
}))

const mockSystemInfo: SystemInfo = {
  os: 'Ubuntu 22.04',
  kernel: '5.15.0-91-generic',
  architecture: 'x86_64',
  uptime: '15 days, 8:32',
  docker_version: '24.0.7'
}

const mockServer: ServerConnection = {
  id: 'srv-123',
  name: 'Test Server',
  host: '192.168.1.100',
  port: 22,
  username: 'testuser',
  auth_type: 'password',
  status: 'connected',
  created_at: '2024-01-01T00:00:00Z'
}

const mockStorageData: StorageData = {
  servers: [mockServer],
  settings: {
    theme: 'light',
    language: 'en',
    auto_save: true,
    developer_mode: false
  }
}

describe('updateServerSystemInfoInStorage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update system info for existing server', () => {
    const result = updateServerSystemInfoInStorage(
      mockStorageData,
      'srv-123',
      mockSystemInfo
    )

    const updatedServer = result.servers.find(s => s.id === 'srv-123')
    expect(updatedServer).toBeDefined()
    expect(updatedServer!.system_info).toEqual(mockSystemInfo)
    expect(updatedServer!.updated_at).toBeDefined()
    
    // Should have ISO timestamp format
    expect(updatedServer!.updated_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/)
  })

  it('should not modify data when server not found', () => {
    const result = updateServerSystemInfoInStorage(
      mockStorageData,
      'nonexistent-id',
      mockSystemInfo
    )

    expect(result).toBe(mockStorageData)
  })

  it('should preserve other server properties', () => {
    const result = updateServerSystemInfoInStorage(
      mockStorageData,
      'srv-123',
      mockSystemInfo
    )

    const updatedServer = result.servers.find(s => s.id === 'srv-123')
    expect(updatedServer).toMatchObject({
      id: 'srv-123',
      name: 'Test Server',
      host: '192.168.1.100',
      port: 22,
      username: 'testuser',
      auth_type: 'password',
      status: 'connected',
      created_at: '2024-01-01T00:00:00Z',
      system_info: mockSystemInfo
    })
  })

  it('should preserve other servers unchanged', () => {
    const anotherServer: ServerConnection = {
      id: 'srv-456',
      name: 'Another Server',
      host: '192.168.1.101',
      port: 22,
      username: 'user2',
      auth_type: 'key',
      status: 'disconnected',
      created_at: '2024-01-02T00:00:00Z'
    }

    const dataWithMultipleServers: StorageData = {
      ...mockStorageData,
      servers: [mockServer, anotherServer]
    }

    const result = updateServerSystemInfoInStorage(
      dataWithMultipleServers,
      'srv-123',
      mockSystemInfo
    )

    expect(result.servers).toHaveLength(2)
    
    const unchangedServer = result.servers.find(s => s.id === 'srv-456')
    expect(unchangedServer).toEqual(anotherServer)
  })

  it('should overwrite existing system info', () => {
    const serverWithExistingInfo: ServerConnection = {
      ...mockServer,
      system_info: {
        os: 'CentOS 7',
        kernel: '3.10.0',
        architecture: 'x86_64',
        uptime: '1 day, 2:30'
      }
    }

    const dataWithExistingInfo: StorageData = {
      ...mockStorageData,
      servers: [serverWithExistingInfo]
    }

    const result = updateServerSystemInfoInStorage(
      dataWithExistingInfo,
      'srv-123',
      mockSystemInfo
    )

    const updatedServer = result.servers.find(s => s.id === 'srv-123')
    expect(updatedServer!.system_info).toEqual(mockSystemInfo)
    expect(updatedServer!.system_info!.os).toBe('Ubuntu 22.04')
  })

  it('should create new data object without mutating original', () => {
    const result = updateServerSystemInfoInStorage(
      mockStorageData,
      'srv-123',
      mockSystemInfo
    )

    expect(result).not.toBe(mockStorageData)
    expect(result.servers).not.toBe(mockStorageData.servers)
    
    // Original should be unchanged
    expect(mockStorageData.servers[0].system_info).toBeUndefined()
  })
})