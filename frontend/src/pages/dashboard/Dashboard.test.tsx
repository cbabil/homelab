/**
 * Dashboard Test Suite
 * 
 * Comprehensive tests for Dashboard component including MCP connection,
 * health status fetching, loading states, and component integration.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Dashboard } from './Dashboard'

// Mock health status data and MCP provider
const { mockHealthStatus, mockCallTool } = vi.hoisted(() => {
  const mockHealthStatus = {
    system: { status: 'healthy', uptime: 3600 },
    services: [
      { name: 'Docker', status: 'running' },
      { name: 'Nginx', status: 'running' }
    ],
    resources: {
      cpu: { usage: 45 },
      memory: { usage: 60 },
      disk: { usage: 30 }
    }
  }

  const mockCallTool = vi.fn()

  return { mockHealthStatus, mockCallTool }
})

vi.mock('@/providers/MCPProvider', () => ({
  useMCP: vi.fn(() => ({
    client: { callTool: mockCallTool },
    isConnected: true
  }))
}))

// Mock SettingsProvider
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
    agentStatuses: {},
    refreshAllAgentStatuses: vi.fn()
  })
}))

// Mock useDashboardData hook
vi.mock('./useDashboardData', () => ({
  useDashboardData: () => ({
    dashboardData: mockHealthStatus,
    healthStatus: mockHealthStatus,
    loading: false,
    refreshing: false,
    isConnected: true,
    refresh: vi.fn(),
    servers: []
  })
}))

// Mock dashboard components
vi.mock('./DashboardStatusCards', () => ({
  DashboardStatusCards: ({ healthStatus }: { healthStatus: Record<string, unknown> | null }) => (
    <div data-testid="dashboard-status-cards">
      Status Cards - {healthStatus ? 'with data' : 'no data'}
    </div>
  )
}))

vi.mock('./DashboardLoadingState', () => ({
  DashboardLoadingState: () => (
    <div data-testid="dashboard-loading-state">Loading dashboard...</div>
  )
}))

vi.mock('./DashboardQuickActions', () => ({
  DashboardQuickActions: () => (
    <div data-testid="dashboard-quick-actions">Quick Actions</div>
  )
}))

vi.mock('./DashboardSystemHealth', () => ({
  DashboardSystemHealth: ({ healthStatus }: { healthStatus: Record<string, unknown> | null }) => (
    <div data-testid="dashboard-system-health">
      System Health - {healthStatus ? 'with data' : 'no data'}
    </div>
  )
}))

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockCallTool.mockResolvedValue({
      success: true,
      data: mockHealthStatus
    })
  })

  describe('Connected State', () => {
    it('should render dashboard when connected', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
        expect(screen.getByText(/monitor your tomo infrastructure/i)).toBeInTheDocument()
        expect(screen.getByTestId('dashboard-status-cards')).toBeInTheDocument()
        expect(screen.getByTestId('dashboard-quick-actions')).toBeInTheDocument()
        expect(screen.getByTestId('dashboard-system-health')).toBeInTheDocument()
      })
    })

    it('should have proper layout structure', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        const gridContainer = screen.getByTestId('dashboard-quick-actions').parentElement
        expect(gridContainer).toHaveClass(
          'grid',
          'grid-cols-1',
          'lg:grid-cols-2',
          'gap-6'
        )
      })
    })

    it('should pass health status to components', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/status cards - with data/i)).toBeInTheDocument()
        expect(screen.getByText(/system health - with data/i)).toBeInTheDocument()
      })
    })
  })

  describe('Disconnected State', () => {
    it('should show connecting message when not connected', () => {
      vi.mocked(require('@/providers/MCPProvider').useMCP).mockReturnValue({
        client: { callTool: mockCallTool },
        isConnected: false
      })
      
      render(<Dashboard />)
      
      expect(screen.getByRole('heading', { name: /connecting to server/i })).toBeInTheDocument()
      expect(screen.getByText(/check notifications for connection status/i)).toBeInTheDocument()
      
      // Should not show dashboard components
      expect(screen.queryByTestId('dashboard-status-cards')).not.toBeInTheDocument()
      expect(screen.queryByTestId('dashboard-quick-actions')).not.toBeInTheDocument()
    })

    it('should display activity icon in disconnected state', () => {
      vi.mocked(require('@/providers/MCPProvider').useMCP).mockReturnValue({
        client: { callTool: mockCallTool },
        isConnected: false
      })
      
      render(<Dashboard />)
      
      const iconContainer = screen.getByRole('heading').previousElementSibling
      expect(iconContainer?.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('should show loading state while fetching health status', async () => {
      mockCallTool.mockImplementation(() => new Promise(() => {})) // Never resolves
      
      render(<Dashboard />)
      
      expect(screen.getByTestId('dashboard-loading-state')).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: /dashboard/i })).not.toBeInTheDocument()
    })

    it('should hide loading state after data is fetched', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.queryByTestId('dashboard-loading-state')).not.toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
      })
    })
  })

  describe('Health Status Fetching', () => {
    it('should fetch health status on mount', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(mockCallTool).toHaveBeenCalledWith('get_health_status', {})
      })
    })

    it('should not fetch when disconnected', () => {
      vi.mocked(require('@/providers/MCPProvider').useMCP).mockReturnValue({
        client: { callTool: mockCallTool },
        isConnected: false
      })
      
      render(<Dashboard />)
      
      expect(mockCallTool).not.toHaveBeenCalled()
    })

    it('should handle fetch errors gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockCallTool.mockRejectedValue(new Error('Fetch failed'))
      
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Failed to fetch health status:', expect.any(Error))
      })
      
      // Should still render dashboard
      expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
      
      consoleError.mockRestore()
    })

    it('should handle unsuccessful API response', async () => {
      mockCallTool.mockResolvedValue({
        success: false,
        error: 'API Error'
      })
      
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/status cards - no data/i)).toBeInTheDocument()
        expect(screen.getByText(/system health - no data/i)).toBeInTheDocument()
      })
    })
  })

  describe('Component Integration', () => {
    it('should render all main dashboard sections', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        // Header section
        expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
        expect(screen.getByText(/monitor your tomo infrastructure/i)).toBeInTheDocument()
        
        // Status cards
        expect(screen.getByTestId('dashboard-status-cards')).toBeInTheDocument()
        
        // Quick actions and system health grid
        expect(screen.getByTestId('dashboard-quick-actions')).toBeInTheDocument()
        expect(screen.getByTestId('dashboard-system-health')).toBeInTheDocument()
      })
    })

    it('should have proper spacing between sections', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        const container = screen.getByRole('heading', { name: /dashboard/i }).closest('div.space-y-8')
        expect(container).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        const heading = screen.getByRole('heading', { name: /dashboard/i })
        expect(heading).toHaveClass('text-3xl', 'font-bold', 'tracking-tight')
      })
    })

    it('should provide descriptive text', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/monitor your tomo infrastructure and manage applications/i)).toBeInTheDocument()
      })
    })
  })
})