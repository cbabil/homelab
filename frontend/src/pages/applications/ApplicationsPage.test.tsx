/**
 * ApplicationsPage Test Suite
 *
 * Comprehensive tests for ApplicationsPage component including filtering,
 * search functionality, app management, and user interactions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ApplicationsPage } from './ApplicationsPage'

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Setup hoisted mocks
const {
  mockApps,
  mockClient,
  mockRefresh,
  mockRefreshLiveStatus,
  mockAddNotification
} = vi.hoisted(() => {
  const mockApps = [
    {
      id: '1',
      appId: 'app-1',
      appName: 'Test App 1',
      appVersion: '1.0.0',
      appDescription: 'Test application',
      appCategory: 'Development',
      appIcon: null,
      appSource: 'Community',
      serverId: 'server-1',
      serverName: 'Server 1',
      serverHost: 'localhost',
      containerName: 'test-app-1',
      status: 'running' as const,
      ports: { '80': '8080' },
      networks: ['bridge'],
      namedVolumes: [],
      bindMounts: [],
      env: {},
      installedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
      errorMessage: null
    },
    {
      id: '2',
      appId: 'app-2',
      appName: 'Test App 2',
      appVersion: '2.0.0',
      appDescription: 'Another test application',
      appCategory: 'Productivity',
      appIcon: null,
      appSource: 'Official',
      serverId: 'server-1',
      serverName: 'Server 1',
      serverHost: 'localhost',
      containerName: 'test-app-2',
      status: 'stopped' as const,
      ports: {},
      networks: [],
      namedVolumes: [],
      bindMounts: [],
      env: {},
      installedAt: new Date().toISOString(),
      startedAt: null,
      errorMessage: null
    }
  ]

  const mockClient = {
    callTool: vi.fn().mockResolvedValue({ success: true })
  }
  const mockRefresh = vi.fn()
  const mockRefreshLiveStatus = vi.fn()
  const mockAddNotification = vi.fn()

  return {
    mockApps,
    mockClient,
    mockRefresh,
    mockRefreshLiveStatus,
    mockAddNotification
  }
})

// Mock providers
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: mockClient,
    isConnected: true
  })
}))

vi.mock('@/providers/NotificationProvider', () => ({
  useNotifications: () => ({
    addNotification: mockAddNotification
  })
}))

vi.mock('@/hooks/useInstalledApps', () => ({
  useInstalledApps: () => ({
    apps: mockApps,
    isLoading: false,
    isRefreshingStatus: false,
    error: null,
    refresh: mockRefresh,
    refreshLiveStatus: mockRefreshLiveStatus
  })
}))

vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: {
      ui: { timezone: 'UTC' }
    }
  })
}))

vi.mock('@/hooks/useDataServices', () => ({
  useDataServices: () => ({
    logs: {
      getAll: vi.fn().mockResolvedValue({ success: true, data: [] })
    },
    isConnected: true
  })
}))

// Mock subcomponents that might cause issues
vi.mock('./AppDetailsPanel', () => ({
  AppDetailsPanel: ({
    app,
    onClose
  }: {
    app: { appName: string } | null
    onClose: () => void
  }) =>
    app ? (
      <div data-testid="app-details-panel">
        <span>{app.appName}</span>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null
}))

function renderApplicationsPage() {
  return render(
    <BrowserRouter>
      <ApplicationsPage />
    </BrowserRouter>
  )
}

describe('ApplicationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering and UI', () => {
    it('should render applications page correctly', () => {
      renderApplicationsPage()

      // Page title (uses translations)
      expect(screen.getByRole('heading', { name: 'Applications' })).toBeInTheDocument()

      // Refresh button
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()

      // Search input
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
    })

    it('should display app count', () => {
      renderApplicationsPage()

      // App count (2 apps) - uses translation key "appCount"
      expect(screen.getByText('2 applications')).toBeInTheDocument()
    })

    it('should display apps in table', () => {
      renderApplicationsPage()

      expect(screen.getByText('Test App 1')).toBeInTheDocument()
      expect(screen.getByText('Test App 2')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('should filter apps by search query', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()

      const searchInput = screen.getByPlaceholderText(/search/i)
      await user.type(searchInput, 'Test App 1')

      // Should show filtered count - uses translation "appCountFiltered"
      await waitFor(() => {
        expect(screen.getByText('1 of 2 applications')).toBeInTheDocument()
      })
    })

    it('should filter by server name', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()

      const searchInput = screen.getByPlaceholderText(/search/i)
      await user.type(searchInput, 'Server 1')

      // Both apps are on Server 1 - uses translation "appCountFiltered"
      await waitFor(() => {
        expect(screen.getByText('2 of 2 applications')).toBeInTheDocument()
      })
    })
  })

  describe('Refresh Functionality', () => {
    it('should call refresh when refresh button is clicked', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()

      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(mockRefresh).toHaveBeenCalled()
        expect(mockRefreshLiveStatus).toHaveBeenCalled()
      })
    })
  })

  describe('App Actions', () => {
    it('should call start_app when start action is triggered', async () => {
      mockClient.callTool.mockResolvedValueOnce({ success: true })
      renderApplicationsPage()

      // Find the enabled start button - Test App 2 is stopped so its start button is enabled
      const startButtons = screen.getAllByTitle('Start')
      // Click on the enabled one (find button that is not disabled)
      const enabledStartButton = startButtons.find(btn => !(btn as HTMLButtonElement).disabled)
      if (enabledStartButton) {
        fireEvent.click(enabledStartButton)
      }

      await waitFor(() => {
        expect(mockClient.callTool).toHaveBeenCalledWith(
          'start_app',
          expect.objectContaining({ app_id: expect.any(String) })
        )
      })
    })

    it('should call stop_app when stop action is triggered', async () => {
      mockClient.callTool.mockResolvedValueOnce({ success: true })
      renderApplicationsPage()

      // Find the enabled stop button - Test App 1 is running so its stop button is enabled
      const stopButtons = screen.getAllByTitle('Stop')
      // Click on the enabled one (find button that is not disabled)
      const enabledStopButton = stopButtons.find(btn => !(btn as HTMLButtonElement).disabled)
      if (enabledStopButton) {
        fireEvent.click(enabledStopButton)
      }

      await waitFor(() => {
        expect(mockClient.callTool).toHaveBeenCalledWith(
          'stop_app',
          expect.objectContaining({ app_id: expect.any(String) })
        )
      })
    })
  })

  describe('App Selection', () => {
    it('should open details panel when app row is clicked', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()

      // Click on the first app row
      const appRow = screen.getByText('Test App 1').closest('tr')
      if (appRow) {
        await user.click(appRow)
      }

      await waitFor(() => {
        expect(screen.getByTestId('app-details-panel')).toBeInTheDocument()
      })
    })

    it('should close details panel when close button is clicked', async () => {
      const user = userEvent.setup()
      renderApplicationsPage()

      // Open panel
      const appRow = screen.getByText('Test App 1').closest('tr')
      if (appRow) {
        await user.click(appRow)
      }

      await waitFor(() => {
        expect(screen.getByTestId('app-details-panel')).toBeInTheDocument()
      })

      // Close panel
      const closeButton = screen.getByRole('button', { name: /close/i })
      await user.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByTestId('app-details-panel')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should show notification when action fails', async () => {
      mockClient.callTool.mockResolvedValueOnce({
        success: false,
        message: 'Failed to start app'
      })
      renderApplicationsPage()

      // Find the enabled start button (Test App 2 is stopped)
      const startButtons = screen.getAllByTitle('Start')
      const enabledStartButton = startButtons.find(btn => !(btn as HTMLButtonElement).disabled)
      if (enabledStartButton) {
        fireEvent.click(enabledStartButton)
      }

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'error' })
        )
      })
    })
  })
})
