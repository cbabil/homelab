/**
 * AgentAuditTable Component Tests
 *
 * Tests for the main audit table component including filtering,
 * loading states, and data display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AgentAuditTable } from '../AgentAuditTable'
import type { AgentAuditEntry } from '@/services/auditMcpClient'
import type { ServerConnection } from '@/types/server'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key
  })
}))

// Mock SettingsProvider
vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: { ui: { timezone: 'UTC' } }
  })
}))

// Mock timezone utils
vi.mock('@/utils/timezone', () => ({
  formatLogTimestamp: (ts: string) => ts
}))

const mockEntries: AgentAuditEntry[] = [
  {
    id: 'log-1',
    timestamp: '2026-01-25T10:00:00Z',
    level: 'INFO',
    event_type: 'AGENT_CONNECTED',
    server_id: 'srv-1',
    server_name: 'Test Server',
    agent_id: 'agent-1',
    success: true,
    message: 'Agent connected successfully',
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
    details: { reason: 'heartbeat_timeout' },
    tags: ['agent', 'lifecycle']
  }
]

const mockServers: ServerConnection[] = [
  {
    id: 'srv-1',
    name: 'Test Server',
    host: 'test.local',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'connected',
    docker_installed: true,
    created_at: '2026-01-01T00:00:00Z'
  }
]

const defaultProps = {
  entries: mockEntries,
  isLoading: false,
  error: null,
  filters: {},
  onFilterChange: vi.fn(),
  onRefresh: vi.fn().mockResolvedValue(undefined),
  servers: mockServers
}

describe('AgentAuditTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders table with entries', () => {
      render(<AgentAuditTable {...defaultProps} />)

      // Both entries have the same server name, so use getAllByText
      expect(screen.getAllByText('Test Server')).toHaveLength(2)
      expect(screen.getByText('AGENT_CONNECTED')).toBeInTheDocument()
      expect(screen.getByText('Agent connected successfully')).toBeInTheDocument()
    })

    it('renders multiple entries', () => {
      render(<AgentAuditTable {...defaultProps} />)

      expect(screen.getByText('AGENT_CONNECTED')).toBeInTheDocument()
      expect(screen.getByText('AGENT_DISCONNECTED')).toBeInTheDocument()
    })

    it('renders level badges correctly', () => {
      render(<AgentAuditTable {...defaultProps} />)

      expect(screen.getByText('INFO')).toBeInTheDocument()
      expect(screen.getByText('WARNING')).toBeInTheDocument()
    })

    it('renders success/failed chips', () => {
      render(<AgentAuditTable {...defaultProps} />)

      // First entry is success, second is failed
      expect(screen.getByText('common.success')).toBeInTheDocument()
      expect(screen.getByText('common.failed')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('shows loading indicator when isLoading is true', () => {
      render(<AgentAuditTable {...defaultProps} isLoading={true} entries={[]} />)

      expect(screen.getByText('common.loading')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('shows empty state when no entries', () => {
      render(<AgentAuditTable {...defaultProps} entries={[]} />)

      expect(screen.getByText('audit.empty.title')).toBeInTheDocument()
      expect(screen.getByText('audit.empty.message')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('shows error state when error is provided', () => {
      render(<AgentAuditTable {...defaultProps} error="Network error" />)

      expect(screen.getByText('audit.error.title')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  describe('compact mode', () => {
    it('hides filters in compact mode', () => {
      render(<AgentAuditTable {...defaultProps} compact />)

      // Filter controls should not be rendered in compact mode
      expect(screen.queryByText('audit.filters.allServers')).not.toBeInTheDocument()
    })

    it('shows filters in non-compact mode', () => {
      render(<AgentAuditTable {...defaultProps} compact={false} />)

      expect(screen.getByText('audit.filters.allServers')).toBeInTheDocument()
    })
  })

  describe('table headers', () => {
    it('renders all column headers', () => {
      render(<AgentAuditTable {...defaultProps} />)

      expect(screen.getByText('audit.columns.timestamp')).toBeInTheDocument()
      expect(screen.getByText('audit.columns.server')).toBeInTheDocument()
      expect(screen.getByText('audit.columns.event')).toBeInTheDocument()
      expect(screen.getByText('audit.columns.level')).toBeInTheDocument()
      expect(screen.getByText('audit.columns.message')).toBeInTheDocument()
      expect(screen.getByText('audit.columns.status')).toBeInTheDocument()
    })
  })
})
