/**
 * SettingsPage Test Suite
 *
 * Comprehensive tests for SettingsPage component including tab navigation,
 * settings state management, component integration, and i18n translations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { SettingsPage } from './SettingsPage'
import { useSettingsState } from './useSettingsState'
import { useSettingsHandlers } from './useSettingsHandlers'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock hooks
vi.mock('./useSettingsState')
vi.mock('./useSettingsHandlers')

const { mockSettingsState, mockSettingsHandlers, mockAddToast, mockResetSettings } = vi.hoisted(
  () => {
    // Mock settings state
    const mockSettingsState = {
      activeTab: 'general',
      setActiveTab: vi.fn(),
      activeServerTab: 'connection',
      setActiveServerTab: vi.fn(),
      connectionTimeout: '30',
      setConnectionTimeout: vi.fn(),
      retryCount: '3',
      setRetryCount: vi.fn(),
      autoRetry: true,
      setAutoRetry: vi.fn(),
      mcpConfig: { mcpServers: { 'tomo': { url: 'http://localhost:8000' } } },
      setMcpConfig: vi.fn(),
      isEditingMcpConfig: false,
      setIsEditingMcpConfig: vi.fn(),
      mcpConfigText: '{}',
      setMcpConfigText: vi.fn(),
      mcpConfigError: '',
      setMcpConfigError: vi.fn(),
      originalMcpConfig: '',
      setOriginalMcpConfig: vi.fn(),
      mcpConnectionStatus: 'disconnected' as const,
      setMcpConnectionStatus: vi.fn(),
      mcpConnectionError: '',
      setMcpConnectionError: vi.fn(),
      sortBy: 'lastActivity' as const,
      setSortBy: vi.fn(),
      sortOrder: 'desc' as const,
      setSortOrder: vi.fn(),
      sessions: [],
      setSessions: vi.fn(),
      serverAlerts: true,
      setServerAlerts: vi.fn(),
      resourceAlerts: true,
      setResourceAlerts: vi.fn(),
      updateAlerts: false,
      setUpdateAlerts: vi.fn(),
      // Agent settings
      preferAgent: true,
      setPreferAgent: vi.fn(),
      agentAutoUpdate: true,
      setAgentAutoUpdate: vi.fn(),
      heartbeatInterval: '30',
      setHeartbeatInterval: vi.fn(),
      heartbeatTimeout: '90',
      setHeartbeatTimeout: vi.fn(),
      commandTimeout: '120',
      setCommandTimeout: vi.fn()
    }

    const mockSettingsHandlers = {
      handleSort: vi.fn(),
      handleTerminateSession: vi.fn(),
      handleRestoreSession: vi.fn(),
      handleMcpConfigEdit: vi.fn(),
      handleMcpConfigSave: vi.fn(),
      handleMcpConfigCancel: vi.fn(),
      handleMcpConnect: vi.fn(),
      handleMcpDisconnect: vi.fn()
    }

    const mockAddToast = vi.fn()
    const mockResetSettings = vi.fn().mockResolvedValue({ success: true })

    return { mockSettingsState, mockSettingsHandlers, mockAddToast, mockResetSettings }
  }
)

// Mock SettingsProvider
vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: { ui: { language: 'en', timezone: 'UTC' } },
    updateSettings: vi.fn(),
    resetSettings: mockResetSettings
  })
}))

// Mock Toast
vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({
    addToast: mockAddToast
  })
}))

// Mock settings components
vi.mock('./SettingsHeader', () => ({
  SettingsHeader: () => <div data-testid="settings-header">Settings</div>
}))

vi.mock('./SettingsTabNavigation', () => ({
  SettingsTabNavigation: ({
    activeTab,
    onTabChange
  }: {
    activeTab: string
    onTabChange: (tab: string) => void
  }) => (
    <div data-testid="settings-tab-navigation">
      <button onClick={() => onTabChange('general')} data-active={activeTab === 'general'}>
        General
      </button>
      <button onClick={() => onTabChange('servers')} data-active={activeTab === 'servers'}>
        Servers
      </button>
      <button onClick={() => onTabChange('security')} data-active={activeTab === 'security'}>
        Security
      </button>
      <button
        onClick={() => onTabChange('notifications')}
        data-active={activeTab === 'notifications'}
      >
        Notifications
      </button>
      <button onClick={() => onTabChange('system')} data-active={activeTab === 'system'}>
        System
      </button>
    </div>
  )
}))

interface ServerSettingsProps {
  connectionTimeout: string
  retryCount: string
}

interface NotificationSettingsProps {
  serverAlerts: boolean
  resourceAlerts: boolean
}

vi.mock('./index', () => ({
  GeneralSettings: () => <div data-testid="general-settings">General Settings Content</div>,
  ServerSettings: (props: ServerSettingsProps) => (
    <div data-testid="server-settings">
      Server Settings Content
      <span data-testid="connection-timeout">{props.connectionTimeout}</span>
      <span data-testid="retry-count">{props.retryCount}</span>
    </div>
  ),
  SecuritySettings: () => <div data-testid="security-settings">Security Settings Content</div>,
  NotificationSettings: (props: NotificationSettingsProps) => (
    <div data-testid="notification-settings">
      Notification Settings Content
      <span data-testid="server-alerts">{props.serverAlerts.toString()}</span>
      <span data-testid="resource-alerts">{props.resourceAlerts.toString()}</span>
    </div>
  ),
  SystemSettings: () => <div data-testid="system-settings">System Settings Content</div>
}))

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useSettingsState).mockReturnValue(mockSettingsState)
    vi.mocked(useSettingsHandlers).mockReturnValue(mockSettingsHandlers)
  })

  describe('Rendering and Layout', () => {
    it('should render settings page correctly', () => {
      render(<SettingsPage />)

      expect(screen.getByTestId('settings-header')).toBeInTheDocument()
      expect(screen.getByTestId('settings-tab-navigation')).toBeInTheDocument()
    })

    it('should have proper layout structure', () => {
      render(<SettingsPage />)

      // MUI Stack component - check for presence instead of specific classes
      const header = screen.getByTestId('settings-header')
      expect(header).toBeInTheDocument()

      // Check content area exists
      const contentArea = screen.getByTestId('general-settings')
      expect(contentArea).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    it('should render general settings by default', () => {
      render(<SettingsPage />)

      expect(screen.getByTestId('general-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('server-settings')).not.toBeInTheDocument()
      expect(screen.queryByTestId('security-settings')).not.toBeInTheDocument()
      expect(screen.queryByTestId('notification-settings')).not.toBeInTheDocument()
    })

    it('should switch to servers tab', async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      const serversTab = screen.getByRole('button', { name: /servers/i })
      await user.click(serversTab)

      expect(mockSettingsState.setActiveTab).toHaveBeenCalledWith('servers')
    })

    it('should switch to security tab', async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      const securityTab = screen.getByRole('button', { name: /security/i })
      await user.click(securityTab)

      expect(mockSettingsState.setActiveTab).toHaveBeenCalledWith('security')
    })

    it('should switch to notifications tab', async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      const notificationsTab = screen.getByRole('button', { name: /notifications/i })
      await user.click(notificationsTab)

      expect(mockSettingsState.setActiveTab).toHaveBeenCalledWith('notifications')
    })

    it('should switch to system tab', async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      const systemTab = screen.getByRole('button', { name: /system/i })
      await user.click(systemTab)

      expect(mockSettingsState.setActiveTab).toHaveBeenCalledWith('system')
    })
  })

  describe('Tab Content Rendering', () => {
    it('should render servers settings when servers tab is active', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'servers'
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('server-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render security settings when security tab is active', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'security'
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('security-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render notification settings when notifications tab is active', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'notifications'
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('notification-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render system settings when system tab is active', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'system'
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('system-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render nothing for invalid tab', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'invalid'
      })

      render(<SettingsPage />)

      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
      expect(screen.queryByTestId('server-settings')).not.toBeInTheDocument()
      expect(screen.queryByTestId('security-settings')).not.toBeInTheDocument()
      expect(screen.queryByTestId('notification-settings')).not.toBeInTheDocument()
    })
  })

  describe('Server Settings Props', () => {
    it('should pass correct props to ServerSettings', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'servers',
        connectionTimeout: '45',
        retryCount: '5'
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('connection-timeout')).toHaveTextContent('45')
      expect(screen.getByTestId('retry-count')).toHaveTextContent('5')
    })
  })

  describe('Notification Settings Props', () => {
    it('should pass correct props to NotificationSettings', () => {
      vi.mocked(useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'notifications',
        serverAlerts: false,
        resourceAlerts: true
      })

      render(<SettingsPage />)

      expect(screen.getByTestId('server-alerts')).toHaveTextContent('false')
      expect(screen.getByTestId('resource-alerts')).toHaveTextContent('true')
    })
  })

  describe('State Integration', () => {
    it('should use settings state hook', () => {
      render(<SettingsPage />)

      expect(vi.mocked(useSettingsState)).toHaveBeenCalled()
    })

    it('should use settings handlers hook with correct parameters', () => {
      render(<SettingsPage />)

      expect(vi.mocked(useSettingsHandlers)).toHaveBeenCalledWith({
        mcpConfigText: mockSettingsState.mcpConfigText,
        setMcpConfig: mockSettingsState.setMcpConfig,
        setMcpConfigError: mockSettingsState.setMcpConfigError,
        setIsEditingMcpConfig: mockSettingsState.setIsEditingMcpConfig,
        setOriginalMcpConfig: mockSettingsState.setOriginalMcpConfig,
        setMcpConfigText: mockSettingsState.setMcpConfigText,
        setSortBy: mockSettingsState.setSortBy,
        setSortOrder: mockSettingsState.setSortOrder,
        setSessions: mockSettingsState.setSessions,
        sortBy: mockSettingsState.sortBy,
        sortOrder: mockSettingsState.sortOrder,
        mcpConfig: mockSettingsState.mcpConfig,
        originalMcpConfig: mockSettingsState.originalMcpConfig,
        setMcpConnectionStatus: mockSettingsState.setMcpConnectionStatus,
        setMcpConnectionError: mockSettingsState.setMcpConnectionError
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper tab navigation structure', () => {
      render(<SettingsPage />)

      const tabButtons = screen.getAllByRole('button')
      const navigationButtons = tabButtons.filter((btn) =>
        ['General', 'Servers', 'Security', 'Notifications', 'System'].includes(
          btn.textContent || ''
        )
      )

      expect(navigationButtons).toHaveLength(5)
    })

    it('should indicate active tab', () => {
      render(<SettingsPage />)

      const generalTab = screen.getByRole('button', { name: /general/i })
      expect(generalTab).toHaveAttribute('data-active', 'true')
    })
  })
})
