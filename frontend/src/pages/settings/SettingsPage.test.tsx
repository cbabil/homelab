/**
 * SettingsPage Test Suite
 * 
 * Comprehensive tests for SettingsPage component including tab navigation,
 * settings state management, and component integration.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { SettingsPage } from './SettingsPage'

// Mock settings state
const mockSettingsState = {
  activeTab: 'general',
  setActiveTab: vi.fn(),
  activeServerTab: 'connection',
  setActiveServerTab: vi.fn(),
  connectionTimeout: 30,
  setConnectionTimeout: vi.fn(),
  retryCount: 3,
  setRetryCount: vi.fn(),
  autoRetry: true,
  setAutoRetry: vi.fn(),
  mcpConfig: { host: 'localhost', port: 3001 },
  setMcpConfig: vi.fn(),
  isEditingMcpConfig: false,
  setIsEditingMcpConfig: vi.fn(),
  mcpConfigText: '{}',
  setMcpConfigText: vi.fn(),
  mcpConfigError: '',
  setMcpConfigError: vi.fn(),
  originalMcpConfig: null,
  setOriginalMcpConfig: vi.fn(),
  sortBy: 'createdAt',
  setSortBy: vi.fn(),
  sortOrder: 'desc',
  setSortOrder: vi.fn(),
  sessions: [],
  setSessions: vi.fn(),
  serverAlerts: true,
  setServerAlerts: vi.fn(),
  resourceAlerts: true,
  setResourceAlerts: vi.fn(),
  updateAlerts: false,
  setUpdateAlerts: vi.fn()
}

const mockSettingsHandlers = {
  handleMcpConfigEdit: vi.fn(),
  handleMcpConfigSave: vi.fn(),
  handleMcpConfigCancel: vi.fn()
}

// Mock hooks
vi.mock('./useSettingsState', () => ({
  useSettingsState: vi.fn(() => mockSettingsState)
}))

vi.mock('./useSettingsHandlers', () => ({
  useSettingsHandlers: vi.fn(() => mockSettingsHandlers)
}))

// Mock settings components
vi.mock('./SettingsHeader', () => ({
  SettingsHeader: () => (
    <div data-testid="settings-header">Settings</div>
  )
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
      <button 
        onClick={() => onTabChange('general')}
        data-active={activeTab === 'general'}
      >
        General
      </button>
      <button 
        onClick={() => onTabChange('servers')}
        data-active={activeTab === 'servers'}
      >
        Servers
      </button>
      <button 
        onClick={() => onTabChange('security')}
        data-active={activeTab === 'security'}
      >
        Security
      </button>
      <button 
        onClick={() => onTabChange('notifications')}
        data-active={activeTab === 'notifications'}
      >
        Notifications
      </button>
    </div>
  )
}))

vi.mock('./SettingsActionFooter', () => ({
  SettingsActionFooter: () => (
    <div data-testid="settings-action-footer">Action Footer</div>
  )
}))

vi.mock('./index', () => ({
  GeneralSettings: () => (
    <div data-testid="general-settings">General Settings Content</div>
  ),
  ServerSettings: (props: any) => (
    <div data-testid="server-settings">
      Server Settings Content
      <span data-testid="connection-timeout">{props.connectionTimeout}</span>
      <span data-testid="retry-count">{props.retryCount}</span>
    </div>
  ),
  SecuritySettings: () => (
    <div data-testid="security-settings">Security Settings Content</div>
  ),
  NotificationSettings: (props: any) => (
    <div data-testid="notification-settings">
      Notification Settings Content
      <span data-testid="server-alerts">{props.serverAlerts.toString()}</span>
      <span data-testid="resource-alerts">{props.resourceAlerts.toString()}</span>
    </div>
  )
}))

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering and Layout', () => {
    it('should render settings page correctly', () => {
      render(<SettingsPage />)
      
      expect(screen.getByTestId('settings-header')).toBeInTheDocument()
      expect(screen.getByTestId('settings-tab-navigation')).toBeInTheDocument()
      expect(screen.getByTestId('settings-action-footer')).toBeInTheDocument()
    })

    it('should have proper layout structure', () => {
      render(<SettingsPage />)
      
      const container = screen.getByTestId('settings-header').closest('div.h-full')
      expect(container).toBeInTheDocument()
      expect(container).toHaveClass('flex', 'flex-col', 'space-y-4')
      
      const contentArea = screen.getByTestId('general-settings').closest('div.flex-1')
      expect(contentArea).toBeInTheDocument()
      expect(contentArea).toHaveClass('min-h-0', 'overflow-auto')
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
  })

  describe('Tab Content Rendering', () => {
    it('should render servers settings when servers tab is active', () => {
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'servers'
      })
      
      render(<SettingsPage />)
      
      expect(screen.getByTestId('server-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render security settings when security tab is active', () => {
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'security'
      })
      
      render(<SettingsPage />)
      
      expect(screen.getByTestId('security-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render notification settings when notifications tab is active', () => {
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'notifications'
      })
      
      render(<SettingsPage />)
      
      expect(screen.getByTestId('notification-settings')).toBeInTheDocument()
      expect(screen.queryByTestId('general-settings')).not.toBeInTheDocument()
    })

    it('should render nothing for invalid tab', () => {
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
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
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
        ...mockSettingsState,
        activeTab: 'servers',
        connectionTimeout: 45,
        retryCount: 5
      })
      
      render(<SettingsPage />)
      
      expect(screen.getByTestId('connection-timeout')).toHaveTextContent('45')
      expect(screen.getByTestId('retry-count')).toHaveTextContent('5')
    })
  })

  describe('Notification Settings Props', () => {
    it('should pass correct props to NotificationSettings', () => {
      vi.mocked(require('./useSettingsState').useSettingsState).mockReturnValue({
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
      
      expect(require('./useSettingsState').useSettingsState).toHaveBeenCalled()
    })

    it('should use settings handlers hook with correct parameters', () => {
      render(<SettingsPage />)
      
      expect(require('./useSettingsHandlers').useSettingsHandlers).toHaveBeenCalledWith({
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
        originalMcpConfig: mockSettingsState.originalMcpConfig
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper tab navigation structure', () => {
      render(<SettingsPage />)
      
      const tabButtons = screen.getAllByRole('button')
      const navigationButtons = tabButtons.filter(btn => 
        ['General', 'Servers', 'Security', 'Notifications'].includes(btn.textContent || '')
      )
      
      expect(navigationButtons).toHaveLength(4)
    })

    it('should indicate active tab', () => {
      render(<SettingsPage />)
      
      const generalTab = screen.getByRole('button', { name: /general/i })
      expect(generalTab).toHaveAttribute('data-active', 'true')
    })
  })
})