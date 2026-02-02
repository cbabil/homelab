/**
 * useAgentAudit Hook
 *
 * Fetches and manages agent audit log data with filtering support.
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuditMcpClient, AgentAuditEntry, AgentAuditFilters } from '@/services/auditMcpClient'

export interface UseAgentAuditReturn {
  entries: AgentAuditEntry[]
  total: number
  truncated: boolean
  isLoading: boolean
  error: string | null
  filters: AgentAuditFilters
  setFilters: (filters: AgentAuditFilters) => void
  refresh: () => Promise<void>
}

export function useAgentAudit(initialFilters: AgentAuditFilters = {}): UseAgentAuditReturn {
  const auditClient = useAuditMcpClient()
  const [entries, setEntries] = useState<AgentAuditEntry[]>([])
  const [total, setTotal] = useState(0)
  const [truncated, setTruncated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<AgentAuditFilters>(initialFilters)

  const fetchAudit = useCallback(async () => {
    if (!auditClient) {
      setError('Audit client not available')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const result = await auditClient.getAgentAudit(filters)
      setEntries(result.entries)
      setTotal(result.total)
      setTruncated(result.truncated ?? false)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch agent audit'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [auditClient, filters])

  useEffect(() => {
    fetchAudit()
  }, [fetchAudit])

  return {
    entries,
    total,
    truncated,
    isLoading,
    error,
    filters,
    setFilters,
    refresh: fetchAudit
  }
}
