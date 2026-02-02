/**
 * AuditFilterControls Component Tests
 *
 * Tests for the filter controls component including server selection,
 * event type filtering, and refresh functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AuditFilterControls } from '../AuditFilterControls'
import type { ServerConnection } from '@/types/server'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key
  })
}))

const mockServers: ServerConnection[] = [
  {
    id: 'srv-1',
    name: 'Server One',
    host: 'server1.local',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'connected',
    docker_installed: true,
    created_at: '2026-01-01T00:00:00Z'
  },
  {
    id: 'srv-2',
    name: 'Server Two',
    host: 'server2.local',
    port: 22,
    username: 'admin',
    auth_type: 'password',
    status: 'connected',
    docker_installed: true,
    created_at: '2026-01-01T00:00:00Z'
  }
]

describe('AuditFilterControls', () => {
  const mockOnFilterChange = vi.fn()
  const mockOnRefresh = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const defaultProps = {
    filters: {},
    onFilterChange: mockOnFilterChange,
    onRefresh: mockOnRefresh,
    isLoading: false,
    servers: mockServers
  }

  describe('rendering', () => {
    it('renders all filter dropdowns', () => {
      render(<AuditFilterControls {...defaultProps} />)

      // All Servers dropdown
      expect(screen.getByText('audit.filters.allServers')).toBeInTheDocument()
      // All Events dropdown
      expect(screen.getByText('audit.filters.allEvents')).toBeInTheDocument()
      // All Levels dropdown
      expect(screen.getByText('audit.filters.allLevels')).toBeInTheDocument()
      // All Results dropdown
      expect(screen.getByText('audit.filters.allResults')).toBeInTheDocument()
    })

    it('renders refresh button', () => {
      render(<AuditFilterControls {...defaultProps} />)

      // Find the refresh button by tooltip
      const refreshButton = screen.getByRole('button')
      expect(refreshButton).toBeInTheDocument()
    })

    it('disables refresh button when loading', () => {
      render(<AuditFilterControls {...defaultProps} isLoading={true} />)

      const refreshButton = screen.getByRole('button')
      expect(refreshButton).toBeDisabled()
    })
  })

  describe('filter changes', () => {
    it('calls onFilterChange when server filter changes', async () => {
      render(<AuditFilterControls {...defaultProps} />)

      // Open the server dropdown - find the combobox inside the testid container
      const serverSelect = screen.getByTestId('filter-server')
      const serverCombobox = serverSelect.querySelector('[role="combobox"]') as HTMLElement
      fireEvent.mouseDown(serverCombobox)

      // Wait for menu to open and select an option
      const serverOption = await screen.findByText('Server One')
      fireEvent.click(serverOption)

      expect(mockOnFilterChange).toHaveBeenCalledWith({ serverId: 'srv-1' })
    })

    it('calls onRefresh when refresh button is clicked', () => {
      render(<AuditFilterControls {...defaultProps} />)

      const refreshButton = screen.getByRole('button')
      fireEvent.click(refreshButton)

      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  describe('with active filters', () => {
    it('displays selected server filter', () => {
      render(
        <AuditFilterControls
          {...defaultProps}
          filters={{ serverId: 'srv-1' }}
        />
      )

      // The dropdown should show the server name for the selected ID
      const serverDropdown = screen.getByTestId('filter-server')
      expect(serverDropdown).toHaveTextContent('Server One')
    })

    it('displays success filter correctly', () => {
      render(
        <AuditFilterControls
          {...defaultProps}
          filters={{ successOnly: true }}
        />
      )

      // The result dropdown should show "success" value
      const resultDropdown = screen.getByTestId('filter-result')
      expect(resultDropdown).toHaveTextContent('success')
    })
  })

  describe('event types', () => {
    it('includes all event types from design spec', async () => {
      render(<AuditFilterControls {...defaultProps} />)

      // Open the event type dropdown - find the combobox inside the testid container
      const eventSelect = screen.getByTestId('filter-event')
      const eventCombobox = eventSelect.querySelector('[role="combobox"]') as HTMLElement
      fireEvent.mouseDown(eventCombobox)

      // Check for key event types (fallback values are the type names)
      expect(await screen.findByText('AGENT_INSTALLED')).toBeInTheDocument()
      expect(screen.getByText('AGENT_REGISTERED')).toBeInTheDocument()
      expect(screen.getByText('AGENT_CONNECTED')).toBeInTheDocument()
      expect(screen.getByText('AGENT_DISCONNECTED')).toBeInTheDocument()
      expect(screen.getByText('AGENT_ERROR')).toBeInTheDocument()
    })
  })
})
