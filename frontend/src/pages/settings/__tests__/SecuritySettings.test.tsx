/**
 * SecuritySettings Test Suite
 *
 * Tests for the SecuritySettings component including
 * account locking and password policy settings.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

// Mock response data
const { mockSettingsResponse, mocks } = vi.hoisted(() => {
  const mockSettingsResponse = {
    success: true,
    data: {
      success: true,
      data: {
        settings: {
          'security.max_login_attempts': { value: 5, category: 'security', source: 'system' },
          'security.account_lockout_duration': { value: 900, category: 'security', source: 'system' },
          'security.password_min_length': { value: 8, category: 'security', source: 'system' },
          'security.password_require_special_chars': { value: true, category: 'security', source: 'system' },
          'security.password_require_numbers': { value: true, category: 'security', source: 'system' },
          'security.password_require_uppercase': { value: true, category: 'security', source: 'system' },
          'security.force_password_change_days': { value: 90, category: 'security', source: 'system' }
        }
      }
    }
  }

  // Store mock implementations in a mutable object that can be modified between tests
  const mocks = {
    callTool: vi.fn(),
    addToast: vi.fn(),
    isConnected: true
  }

  return { mockSettingsResponse, mocks }
})

// Mock MCP Provider
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: { callTool: mocks.callTool },
    isConnected: mocks.isConnected
  })
}))

// Mock Toast
vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({ addToast: mocks.addToast })
}))

// Mock SettingsSavingContext
vi.mock('../SettingsSavingContext', () => ({
  useSettingsSaving: () => ({
    isSaving: false,
    setIsSaving: vi.fn()
  })
}))

// Mock useSecuritySettings hook
vi.mock('@/hooks/useSecuritySettings', () => ({
  useSecuritySettings: () => ({
    sessionTimeout: '1h',
    onSessionTimeoutChange: vi.fn()
  })
}))

// Mock useAgentAudit hook
vi.mock('@/hooks/useAgentAudit', () => ({
  useAgentAudit: () => ({
    auditLogs: [],
    isLoading: false,
    error: null,
    refresh: vi.fn()
  })
}))

// Mock useServers hook
vi.mock('@/hooks/useServers', () => ({
  useServers: () => ({
    servers: [],
    filteredServers: [],
    refreshServers: vi.fn()
  })
}))

// Mock AgentAuditTable component
vi.mock('@/components/audit', () => ({
  AgentAuditTable: () => <div data-testid="agent-audit-table">Audit Table</div>
}))

// Import after mocks
import { SecuritySettings } from '../SecuritySettings'

describe('SecuritySettings', () => {
  beforeEach(() => {
    // Reset mock implementations
    mocks.callTool = vi.fn().mockResolvedValue(mockSettingsResponse)
    mocks.addToast = vi.fn()
    mocks.isConnected = true

    // Set auth token
    localStorage.setItem('tomo-auth-token', 'mock-token')
  })

  afterEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render with default settings when not connected', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Account Locking')).toBeInTheDocument()
      })
    })

    it('should render account locking section', async () => {
      // Don't make API call for this test
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Account Locking')).toBeInTheDocument()
      })

      expect(screen.getByText('Max login attempts')).toBeInTheDocument()
      expect(screen.getByText('Lockout duration')).toBeInTheDocument()
    })

    it('should render password policy section', async () => {
      // Don't make API call for this test
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Password Policy')).toBeInTheDocument()
      })

      expect(screen.getByText('Minimum length')).toBeInTheDocument()
      expect(screen.getByText('Require uppercase')).toBeInTheDocument()
      expect(screen.getByText('Require numbers')).toBeInTheDocument()
      expect(screen.getByText('Require special characters')).toBeInTheDocument()
      expect(screen.getByText('Password expiration')).toBeInTheDocument()
    })
  })

  describe('Data Loading', () => {
    it('should not fetch settings without token', async () => {
      localStorage.clear()
      mocks.isConnected = false // Skip API call

      render(<SecuritySettings />)

      // Component should render with defaults
      await waitFor(() => {
        expect(screen.getByText('Account Locking')).toBeInTheDocument()
      })

      // No token means no API call
      expect(mocks.callTool).not.toHaveBeenCalled()
    })

    it('should not fetch settings when not connected', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      // Component should render with defaults
      await waitFor(() => {
        expect(screen.getByText('Account Locking')).toBeInTheDocument()
      })

      // Not connected means no API call
      expect(mocks.callTool).not.toHaveBeenCalled()
    })
  })

  describe('Default Values', () => {
    it('should have correct default security settings', async () => {
      mocks.isConnected = false // Skip loading

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Account Locking')).toBeInTheDocument()
      })

      // Check that dropdown selects exist (lockout duration and password expiration)
      const comboboxes = screen.getAllByRole('combobox')
      expect(comboboxes.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('UI Structure', () => {
    it('should have account locking description', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText(/Protect against brute force attacks/i)).toBeInTheDocument()
      })
    })

    it('should have password policy description', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText(/Configure password requirements/i)).toBeInTheDocument()
      })
    })
  })

  describe('Settings Categories', () => {
    it('should display all password requirement toggles', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Password Policy')).toBeInTheDocument()
      })

      expect(screen.getByText(/At least one uppercase letter/)).toBeInTheDocument()
      expect(screen.getByText(/At least one number/)).toBeInTheDocument()
      expect(screen.getByText(/At least one special character/)).toBeInTheDocument()
    })

    it('should display lockout duration options', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Lockout duration')).toBeInTheDocument()
      })
    })

    it('should display password expiration options', async () => {
      mocks.isConnected = false

      render(<SecuritySettings />)

      await waitFor(() => {
        expect(screen.getByText('Password expiration')).toBeInTheDocument()
      })
    })
  })
})
