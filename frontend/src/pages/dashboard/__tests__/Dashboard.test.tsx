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

describe('Dashboard', () => {
  let mockClient: any

  beforeEach(() => {
    vi.useFakeTimers()
    mockClient = {
      callTool: vi.fn()
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

    expect(screen.getByText('Connecting to Server...')).toBeInTheDocument()
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

    expect(screen.getByText('Monitor your homelab infrastructure and manage applications.')).toBeInTheDocument()
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
      expect(screen.getByText('healthy')).toBeInTheDocument()
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

    await waitFor(() => {
      expect(screen.getByText('Total Servers')).toBeInTheDocument()
    })

    expect(screen.getByText('Total Applications')).toBeInTheDocument()
    expect(screen.getByText('Running Apps')).toBeInTheDocument()
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

  it('should display quick actions section', async () => {
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
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
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

  it('should show refresh button', async () => {
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
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
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
