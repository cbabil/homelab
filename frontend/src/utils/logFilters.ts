/**
 * Log filter helpers
 *
 * Shared filtering logic for monitoring logs, ensuring UI and tests
 * stay aligned on how categories map to log entries.
 */

import type { LogEntry } from '@/types/logs'

export type LogFilterKey = 'all' | 'security' | 'application' | 'system' | 'docker'

export interface LogFilterOption {
  key: LogFilterKey
  label: string
}

export const LOG_FILTERS: LogFilterOption[] = [
  { key: 'all', label: 'All Logs' },
  { key: 'security', label: 'Security' },
  { key: 'application', label: 'Application' },
  { key: 'system', label: 'System' },
  { key: 'docker', label: 'Docker' }
]

export function filterLogsByKey(logs: LogEntry[], filter: LogFilterKey): LogEntry[] {
  if (filter === 'all') {
    return logs
  }

  return logs.filter((log) => {
    if (filter === 'security') {
      return (
        log.category === 'security' ||
        log.tags?.includes('security') ||
        log.tags?.includes('authentication') ||
        log.source.toLowerCase().includes('auth')
      )
    }

    if (filter === 'application') {
      return log.category === 'application' || log.tags?.includes('application')
    }

    if (filter === 'system') {
      return log.category === 'system' || log.source.toLowerCase().includes('system')
    }

    if (filter === 'docker') {
      return log.source.toLowerCase().includes('docker') || log.tags?.includes('docker')
    }

    return true
  })
}
