/**
 * useAgentAudit Hook Tests
 *
 * Unit tests for agent audit hook functionality including
 * data fetching, filtering, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAgentAudit } from '../useAgentAudit'
import type { AgentAuditEntry } from '@/services/auditMcpClient'

// Mock audit client
const mockGetAgentAudit = vi.fn()
const mockUseAuditMcpClient = vi.fn<[], { getAgentAudit: typeof mockGetAgentAudit } | null>(() => ({
  getAgentAudit: mockGetAgentAudit
}))

vi.mock('@/services/auditMcpClient', () => ({
  useAuditMcpClient: () => mockUseAuditMcpClient()
}))

const mockAuditEntries: AgentAuditEntry[] = [
  {
    id: 'log-1',
    timestamp: '2026-01-25T10:00:00Z',
    level: 'INFO',
    event_type: 'AGENT_CONNECTED',
    server_id: 'srv-1',
    server_name: 'Test Server',
    agent_id: 'agent-1',
    success: true,
    message: 'Agent connected',
    tags: ['agent', 'lifecycle']
  },
  {
    id: 'log-2',
    timestamp: '2026-01-25T10:05:00Z',
    level: 'WARNING',
    event_type: 'AGENT_DISCONNECTED',
    server_id: 'srv-1',
    server_name: 'Test Server',
    agent_id: 'agent-1',
    success: false,
    message: 'Agent disconnected: timeout',
    tags: ['agent', 'lifecycle']
  }
]

describe('useAgentAudit', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetAgentAudit.mockReset()
    mockUseAuditMcpClient.mockReturnValue({
      getAgentAudit: mockGetAgentAudit
    })
  })

  describe('initialization', () => {
    it('should start with loading state', () => {
      mockGetAgentAudit.mockResolvedValue({ entries: [], total: 0 })

      const { result } = renderHook(() => useAgentAudit())

      expect(result.current.isLoading).toBe(true)
      expect(result.current.entries).toEqual([])
      expect(result.current.error).toBeNull()
    })

    it('should fetch audit entries on mount', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: mockAuditEntries, total: 2 })

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // May be called multiple times in strict mode
      expect(mockGetAgentAudit).toHaveBeenCalled()
      expect(result.current.entries).toEqual(mockAuditEntries)
      expect(result.current.total).toBe(2)
      expect(result.current.error).toBeNull()
    })

    it('should use initial filters when provided', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: [], total: 0 })

      const initialFilters = { serverId: 'srv-1', limit: 50 }
      renderHook(() => useAgentAudit(initialFilters))

      await waitFor(() => {
        expect(mockGetAgentAudit).toHaveBeenCalledWith(initialFilters)
      })
    })
  })

  describe('error handling', () => {
    it('should handle fetch errors', async () => {
      const error = new Error('Network error')
      mockGetAgentAudit.mockRejectedValue(error)

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Network error')
      expect(result.current.entries).toEqual([])
    })

    it('should handle non-Error objects', async () => {
      mockGetAgentAudit.mockRejectedValue('String error')

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Failed to fetch agent audit')
    })
  })

  describe('filtering', () => {
    it('should refetch when filters change', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: mockAuditEntries, total: 2 })

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const initialCallCount = mockGetAgentAudit.mock.calls.length

      // Update filters
      act(() => {
        result.current.setFilters({ eventType: 'AGENT_CONNECTED' })
      })

      await waitFor(() => {
        expect(mockGetAgentAudit.mock.calls.length).toBeGreaterThan(initialCallCount)
      })

      expect(mockGetAgentAudit).toHaveBeenLastCalledWith({ eventType: 'AGENT_CONNECTED' })
    })

    it('should provide current filters', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: [], total: 0 })

      const initialFilters = { serverId: 'srv-1' }
      const { result } = renderHook(() => useAgentAudit(initialFilters))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.filters).toEqual(initialFilters)
    })
  })

  describe('refresh', () => {
    it('should allow manual refresh', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: mockAuditEntries, total: 2 })

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const initialCallCount = mockGetAgentAudit.mock.calls.length

      // Manual refresh
      await act(async () => {
        await result.current.refresh()
      })

      expect(mockGetAgentAudit.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    it('should update entries after refresh', async () => {
      mockGetAgentAudit
        .mockResolvedValueOnce({ entries: [], total: 0 })
        .mockResolvedValueOnce({ entries: mockAuditEntries, total: 2 })

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Initially empty
      expect(result.current.entries).toEqual([])

      // Manual refresh with new data
      await act(async () => {
        await result.current.refresh()
      })

      await waitFor(() => {
        expect(result.current.entries).toEqual(mockAuditEntries)
      })
    })

    it('should expose truncated status', async () => {
      mockGetAgentAudit.mockResolvedValue({ entries: mockAuditEntries, total: 1500, truncated: true })

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.total).toBe(1500)
      expect(result.current.truncated).toBe(true)
    })
  })

  describe('client availability', () => {
    it('should handle missing audit client', async () => {
      // Mock the hook to return null
      mockUseAuditMcpClient.mockReturnValue(null)

      const { result } = renderHook(() => useAgentAudit())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Audit client not available')
      expect(result.current.entries).toEqual([])
    })
  })
})
