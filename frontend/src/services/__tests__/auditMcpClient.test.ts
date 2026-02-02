/**
 * Audit MCP Client Tests
 *
 * Comprehensive tests for the AuditMcpClient including
 * settings audit, auth audit, error handling, and type safety.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { AuditMcpClient } from '../auditMcpClient'

// Mock MCP client interface matching MCPProvider's client type
interface MockMcpClient {
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<{ success: boolean; data?: T; error?: string }>
}

// Mock the MCP provider with vi.hoisted (not needed here - no vi.mock() call)
const mockMcpClient: MockMcpClient = {
  callTool: vi.fn()
}

const mockIsConnected = vi.fn()

describe('AuditMcpClient', () => {
  let client: AuditMcpClient

  beforeEach(() => {
    client = new AuditMcpClient(mockMcpClient as ReturnType<typeof import('@/providers/MCPProvider').useMCP>['client'], mockIsConnected)
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Constructor and Initialization', () => {
    it('should initialize with MCP client and connection checker', () => {
      expect(client).toBeInstanceOf(AuditMcpClient)
    })
  })

  describe('Settings Audit', () => {
    it('should get settings audit successfully', async () => {
      const mockAuditEntries = [
        {
          id: 1,
          table_name: 'system_settings',
          record_id: '1',
          user_id: 'user_123',
          setting_key: 'ui.theme',
          old_value: '"light"',
          new_value: '"dark"',
          change_type: 'UPDATE',
          created_at: '2023-01-01T00:00:00Z'
        }
      ]

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: mockAuditEntries }
      })

      const result = await client.getSettingsAudit()

      expect(result).toHaveLength(1)
      expect(result[0].setting_key).toBe('ui.theme')
      expect(result[0].change_type).toBe('UPDATE')
    })

    it('should get settings audit with filter_user_id', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getSettingsAudit('user_123', undefined, 50, 0)

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_settings_audit',
        expect.objectContaining({
          filter_user_id: 'user_123',
          setting_key: undefined,
          limit: 50,
          offset: 0
        })
      )
    })

    it('should get settings audit with setting_key filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getSettingsAudit(undefined, 'ui.theme', 25, 10)

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_settings_audit',
        expect.objectContaining({
          filter_user_id: undefined,
          setting_key: 'ui.theme',
          limit: 25,
          offset: 10
        })
      )
    })

    it('should handle settings audit retrieval errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Audit service error'
      })

      const result = await client.getSettingsAudit()

      expect(result).toEqual([])
    })

    it('should handle MCP call exceptions', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue(new Error('Connection lost'))

      const result = await client.getSettingsAudit()

      expect(result).toEqual([])
    })
  })

  describe('Auth Audit', () => {
    it('should get auth audit successfully', async () => {
      const mockAuditEntries = [
        {
          id: 'sec-abc123',
          timestamp: '2024-01-15T10:00:00Z',
          level: 'INFO',
          event_type: 'LOGIN',
          username: 'admin',
          success: true,
          client_ip: '192.168.1.100',
          user_agent: 'Mozilla/5.0',
          message: 'LOGIN successful for user: admin',
          tags: ['security', 'authentication', 'login', 'success']
        },
        {
          id: 'sec-def456',
          timestamp: '2024-01-15T11:00:00Z',
          level: 'WARNING',
          event_type: 'LOGIN',
          username: 'unknown',
          success: false,
          client_ip: '10.0.0.50',
          user_agent: 'curl/7.68.0',
          message: 'LOGIN failed for user: unknown',
          tags: ['security', 'authentication', 'login', 'failure']
        }
      ]

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: mockAuditEntries }
      })

      const result = await client.getAuthAudit()

      expect(result).toHaveLength(2)
      expect(result[0].event_type).toBe('LOGIN')
      expect(result[0].success).toBe(true)
      expect(result[1].success).toBe(false)
    })

    it('should get auth audit with event_type filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getAuthAudit('LOGIN')

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_auth_audit',
        expect.objectContaining({
          event_type: 'LOGIN',
          username: undefined,
          success_only: undefined,
          limit: 50,
          offset: 0
        })
      )
    })

    it('should get auth audit with username filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getAuthAudit(undefined, 'admin')

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_auth_audit',
        expect.objectContaining({
          event_type: undefined,
          username: 'admin',
          success_only: undefined,
          limit: 50,
          offset: 0
        })
      )
    })

    it('should get auth audit with success filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getAuthAudit(undefined, undefined, false)

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_auth_audit',
        expect.objectContaining({
          event_type: undefined,
          username: undefined,
          success_only: false,
          limit: 50,
          offset: 0
        })
      )
    })

    it('should get auth audit with pagination', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [] }
      })

      await client.getAuthAudit(undefined, undefined, undefined, 25, 50)

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_auth_audit',
        expect.objectContaining({
          limit: 25,
          offset: 50
        })
      )
    })

    it('should handle auth audit retrieval errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Admin required'
      })

      const result = await client.getAuthAudit()

      expect(result).toEqual([])
    })

    it('should handle MCP call exceptions', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue(new Error('Connection lost'))

      const result = await client.getAuthAudit()

      expect(result).toEqual([])
    })
  })

  describe('Agent Audit', () => {
    it('should get agent audit successfully', async () => {
      const mockAuditEntries = [
        {
          id: 'agent-log-1',
          timestamp: '2026-01-25T10:00:00Z',
          level: 'INFO',
          event_type: 'AGENT_CONNECTED',
          server_id: 'srv-1',
          server_name: 'Test Server',
          agent_id: 'agent-1',
          success: true,
          message: 'Agent connected successfully',
          details: { version: '1.0.0' },
          tags: ['agent', 'lifecycle']
        }
      ]

      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: mockAuditEntries, total: 1, truncated: false }
      })

      const result = await client.getAgentAudit()

      expect(result.entries).toHaveLength(1)
      expect(result.entries[0].event_type).toBe('AGENT_CONNECTED')
      expect(result.entries[0].success).toBe(true)
      expect(result.total).toBe(1)
      expect(result.truncated).toBe(false)
    })

    it('should get agent audit with server_id filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 0 }
      })

      await client.getAgentAudit({ serverId: 'srv-1' })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_agent_audit',
        expect.objectContaining({
          server_id: 'srv-1',
          event_type: undefined,
          success_only: undefined,
          level: undefined,
          limit: 50,
          offset: 0
        })
      )
    })

    it('should get agent audit with event_type filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 0 }
      })

      await client.getAgentAudit({ eventType: 'AGENT_INSTALLED' })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_agent_audit',
        expect.objectContaining({
          event_type: 'AGENT_INSTALLED'
        })
      )
    })

    it('should get agent audit with success filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 0 }
      })

      await client.getAgentAudit({ successOnly: true })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_agent_audit',
        expect.objectContaining({
          success_only: true
        })
      )
    })

    it('should get agent audit with level filter', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 0 }
      })

      await client.getAgentAudit({ level: 'ERROR' })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_agent_audit',
        expect.objectContaining({
          level: 'ERROR'
        })
      )
    })

    it('should get agent audit with pagination', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 0 }
      })

      await client.getAgentAudit({ limit: 25, offset: 50 })

      expect(mockMcpClient.callTool).toHaveBeenCalledWith(
        'get_agent_audit',
        expect.objectContaining({
          limit: 25,
          offset: 50
        })
      )
    })

    it('should handle truncated results', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: true,
        data: { audit_entries: [], total: 1500, truncated: true }
      })

      const result = await client.getAgentAudit()

      expect(result.total).toBe(1500)
      expect(result.truncated).toBe(true)
    })

    it('should handle agent audit retrieval errors', async () => {
      vi.mocked(mockMcpClient.callTool).mockResolvedValue({
        success: false,
        error: 'Admin required'
      })

      const result = await client.getAgentAudit()

      expect(result.entries).toEqual([])
      expect(result.total).toBe(0)
    })

    it('should handle MCP call exceptions', async () => {
      vi.mocked(mockMcpClient.callTool).mockRejectedValue(new Error('Connection lost'))

      const result = await client.getAgentAudit()

      expect(result.entries).toEqual([])
      expect(result.total).toBe(0)
    })
  })
})
