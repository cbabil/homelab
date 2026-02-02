/**
 * Unit tests for Dashboard component
 *
 * Tests main dashboard layout and data integration.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import './setup'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Dashboard } from '../Dashboard'
import { useMCP } from '@/providers/MCPProvider'

// Mock the MCP provider
vi.mock('@/providers/MCPProvider')

// Mock the SettingsProvider
vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: {
      ui: { refreshRate: 60 },
      applications: { autoRefreshStatus: true }
    },
    updateSettings: vi.fn(),
    isLoading: false,
    error: null
  })
}))

// Mock useAgentStatus hook
vi.mock('@/hooks/useAgentStatus', () => ({
  useAgentStatus: () => ({
    agentStatuses: new Map(),
    refreshAllAgentStatuses: vi.fn()
  })
}))

const mockUseMCP = vi.mocked(useMCP)

const mockDashboardSummary = {
  total_servers: 5,
  online_servers: 4,
  offline_servers: 1,
  total_apps: 10,
  running_apps: 8,
  stopped_apps: 1,
  error_apps: 1,
  avg_cpu_percent: 45.5,
  avg_memory_percent: 60.2,
  avg_disk_percent: 35.0,
  recent_activities: []
}

const mockHealthStatus = {
  status: 'healthy'
}

interface MockClient {
  callTool: ReturnType<typeof vi.fn>
  isConnected: () => boolean
}

describe('Dashboard', () => {
  let mockClient: MockClient

  beforeEach(() => {
    // Use fake timers with shouldAdvanceTime to allow waitFor to work
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockClient = {
      callTool: vi.fn() as ReturnType<typeof vi.fn>,
      isConnected: () => true
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  const renderDashboard = () => {
    return render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )
  }

  it('should show connecting state when not connected', () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: false,
      error: null
    })

    renderDashboard()

    expect(screen.getByText('Connecting to Server')).toBeInTheDocument()
    expect(screen.getByText('Check notifications for connection status updates.')).toBeInTheDocument()
  })

  it('should show loading skeleton when loading', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool.mockImplementation(() => new Promise(() => {}))

    renderDashboard()

    // Should show loading skeletons
    await waitFor(() => {
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
    })
  })

  it('should display dashboard after data loads', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    expect(screen.getByText('Monitor your tomo infrastructure')).toBeInTheDocument()
  })

  it('should display health status badge', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Healthy')).toBeInTheDocument()
    })
  })

  it('should display stats section', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    // Stats section titles - Servers appears twice (stats and overview), so use getAllByText
    await waitFor(() => {
      expect(screen.getAllByText('Servers').length).toBeGreaterThanOrEqual(1)
    })

    expect(screen.getByText('Applications')).toBeInTheDocument()
    expect(screen.getByText('Running')).toBeInTheDocument()
    expect(screen.getByText('Issues')).toBeInTheDocument()
  })

  it('should display resource usage section', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Resource Usage')).toBeInTheDocument()
    })
  })

  it('should display servers overview section', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    // The Servers title appears in both stats and overview, View all appears in both overview and activity
    await waitFor(() => {
      // Servers appears in both stats and overview sections
      const serverElements = screen.getAllByText('Servers')
      expect(serverElements.length).toBe(2) // One in stats, one in servers overview
    })
  })

  it('should display recent activity section', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    })
  })

  it('should show refresh interval controls', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    // Check for refresh interval options in the dropdown
    await waitFor(() => {
      // These interval options are always visible in the dropdown
      expect(screen.getByText('15 seconds')).toBeInTheDocument()
      expect(screen.getByText('Manual only')).toBeInTheDocument()
    })
  })

  it('should display last updated time', async () => {
    mockUseMCP.mockReturnValue({
      client: mockClient as any,
      isConnected: true,
      error: null
    })

    mockClient.callTool
      .mockResolvedValueOnce({ success: true, data: mockDashboardSummary })
      .mockResolvedValueOnce({ success: true, data: mockHealthStatus })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText(/Updated/)).toBeInTheDocument()
    })
  })
})
