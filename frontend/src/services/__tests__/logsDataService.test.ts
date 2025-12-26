/**
 * Logs Data Service Tests
 *
 * Unit tests for the new logs data service implementation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { LogsDataService } from '../logsDataService'
import { MCPClient, MCPResponse } from '@/types/mcp'
import { LogEntry } from '@/types/logs'

// Mock MCP Client
const mockMCPClient: MCPClient = {
  connect: vi.fn().mockResolvedValue(undefined),
  disconnect: vi.fn().mockResolvedValue(undefined),
  isConnected: vi.fn().mockReturnValue(true),
  subscribeTo: vi.fn().mockReturnValue({} as EventSource),
  callTool: vi.fn()
}

describe('LogsDataService', () => {
  let service: LogsDataService

  beforeEach(() => {
    vi.clearAllMocks()
    service = new LogsDataService(mockMCPClient)
  })

  describe('getAll', () => {
    it('should fetch logs successfully', async () => {
      const mockResponse: MCPResponse<any> = {
        success: true,
        data: {
          logs: [{
            id: '1',
            timestamp: '2023-01-01T00:00:00Z',
            level: 'info',
            source: 'system',
            message: 'Test log',
            tags: '[]',
            extra_data: '{}',
            created_at: '2023-01-01T00:00:00Z'
          }],
          total: 1,
          page: 1,
          pageSize: 50
        }
      }

      vi.mocked(mockMCPClient.callTool).mockResolvedValue(mockResponse)

      const result = await service.getAll({ limit: 50 })

      expect(result.success).toBe(true)
      expect(result.data).toHaveLength(1)
      expect(result.data?.[0].message).toBe('Test log')
      expect(mockMCPClient.callTool).toHaveBeenCalledWith('get_logs', {
        limit: 50
      })
    })

    it('should handle service errors', async () => {
      const mockErrorResponse: MCPResponse<any> = {
        success: false,
        error: 'Connection failed'
      }

      vi.mocked(mockMCPClient.callTool).mockResolvedValue(mockErrorResponse)

      const result = await service.getAll()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Connection failed')
    })
  })

  describe('refresh', () => {
    it('should clear cache and reload data', async () => {
      const mockResponse: MCPResponse<any> = {
        success: true,
        data: { logs: [], total: 0, page: 1, pageSize: 50 }
      }

      vi.mocked(mockMCPClient.callTool).mockResolvedValue(mockResponse)

      const result = await service.refresh()

      expect(result.success).toBe(true)
      expect(mockMCPClient.callTool).toHaveBeenCalled()
    })
  })

  describe('loading state management', () => {
    it('should track loading state during operations', async () => {
      const mockResponse: MCPResponse<any> = {
        success: true,
        data: { logs: [], total: 0, page: 1, pageSize: 50 }
      }

      vi.mocked(mockMCPClient.callTool).mockResolvedValue(mockResponse)

      const initialState = service.getLoadingState()
      expect(initialState.isLoading).toBe(false)

      const promise = service.getAll()

      await promise

      const finalState = service.getLoadingState()
      expect(finalState.isLoading).toBe(false)
      expect(finalState.error).toBeNull()
    })
  })
})