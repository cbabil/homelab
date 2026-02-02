/**
 * SystemSettings Test Suite
 *
 * Tests for the SystemSettings component which wraps
 * DataRetentionSettings and BackupSection.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReactElement } from 'react'
import { NotificationProvider } from '../../../providers/NotificationProvider'
import { MCPProvider } from '../../../providers/MCPProvider'

// Mock useMcpClient to avoid real network connections
vi.mock('@/hooks/useMcpClient', () => ({
  useMcpClient: () => ({
    callTool: vi.fn().mockResolvedValue({ success: true, data: null }),
    isConnected: false,
    error: null
  })
}))

// Mock the child components
vi.mock('../components/DataRetentionSettings', () => ({
  DataRetentionSettings: () => (
    <div data-testid="data-retention-settings">Data Retention Settings</div>
  )
}))

vi.mock('@/components/settings/BackupSection', () => ({
  BackupSection: () => <div data-testid="backup-section">Backup Section</div>
}))

import { SystemSettings } from '../SystemSettings'

/**
 * Render component with required providers
 */
const renderWithProviders = (ui: ReactElement) => {
  return render(
    <MCPProvider serverUrl="http://localhost:8000">
      <NotificationProvider>
        {ui}
      </NotificationProvider>
    </MCPProvider>
  )
}

describe('SystemSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render DataRetentionSettings component', () => {
      renderWithProviders(<SystemSettings />)

      expect(screen.getByTestId('data-retention-settings')).toBeInTheDocument()
    })

    it('should render BackupSection component', () => {
      renderWithProviders(<SystemSettings />)

      expect(screen.getByTestId('backup-section')).toBeInTheDocument()
    })

    it('should render both sections', () => {
      renderWithProviders(<SystemSettings />)

      expect(screen.getByText('Data Retention Settings')).toBeInTheDocument()
      expect(screen.getByText('Backup Section')).toBeInTheDocument()
    })
  })

  describe('Layout', () => {
    it('should render version information section', () => {
      renderWithProviders(<SystemSettings />)

      // Version info section should be present (uses MUI Box, not Tailwind classes)
      expect(screen.getByText('Version Information')).toBeInTheDocument()
    })
  })
})
