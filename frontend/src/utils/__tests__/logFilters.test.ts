import { describe, it, expect } from 'vitest'
import { filterLogsByKey, LOG_FILTERS, LogFilterKey } from '../logFilters'
import type { LogEntry } from '@/types/logs'

const sampleLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'info',
    source: 'auth_service',
    message: 'User admin logged in',
    category: 'security',
    tags: ['security', 'authentication', 'success'],
    metadata: {},
    createdAt: new Date().toISOString()
  },
  {
    id: '2',
    timestamp: new Date().toISOString(),
    level: 'info',
    source: 'application',
    message: 'Job completed',
    category: 'application',
    tags: ['application'],
    metadata: {},
    createdAt: new Date().toISOString()
  },
  {
    id: '3',
    timestamp: new Date().toISOString(),
    level: 'warn',
    source: 'system_monitor',
    message: 'High CPU usage detected',
    category: 'system',
    tags: ['system'],
    metadata: {},
    createdAt: new Date().toISOString()
  },
  {
    id: '4',
    timestamp: new Date().toISOString(),
    level: 'info',
    source: 'docker',
    message: 'Container restarted',
    category: 'application',
    tags: ['docker'],
    metadata: {},
    createdAt: new Date().toISOString()
  }
]

describe('LOG_FILTERS', () => {
  it('includes security filter option', () => {
    const keys = LOG_FILTERS.map((filter) => filter.key)
    expect(keys).toContain('security')
  })
})

describe('filterLogsByKey', () => {
  const runFilter = (key: LogFilterKey) => filterLogsByKey(sampleLogs, key).map((log) => log.id)

  it('returns all logs when key is all', () => {
    expect(runFilter('all')).toHaveLength(sampleLogs.length)
  })

  it('returns only security related logs', () => {
    expect(runFilter('security')).toEqual(['1'])
  })

  it('returns only application logs', () => {
    expect(runFilter('application')).toEqual(['2', '4'])
  })

  it('returns only system logs', () => {
    expect(runFilter('system')).toEqual(['3'])
  })

  it('returns docker logs', () => {
    expect(runFilter('docker')).toEqual(['4'])
  })
})
