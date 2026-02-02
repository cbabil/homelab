/**
 * TabNavigation Test Suite
 *
 * Tests for the TabNavigation component including tab rendering,
 * switching, severity filter, and accessibility.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileText, Shield, Activity } from 'lucide-react'
import { TabNavigation, Tab, SeverityLevel } from '../TabNavigation'

const mockTabs: Tab[] = [
  { id: 'all', label: 'All Logs', icon: FileText, count: 100 },
  { id: 'security', label: 'Security', icon: Shield, count: 25 },
  { id: 'activity', label: 'Activity', icon: Activity, count: 75 }
]

const mockSeverityOptions = [
  { id: 'all' as SeverityLevel, label: 'All', color: '#666', count: 100 },
  { id: 'success' as SeverityLevel, label: 'Success', color: '#4caf50', count: 50 },
  { id: 'error' as SeverityLevel, label: 'Error', color: '#f44336', count: 10 }
]

describe('TabNavigation', () => {
  const defaultProps = {
    activeTab: 'all',
    onTabChange: vi.fn(),
    tabs: mockTabs
  }

  describe('Rendering', () => {
    it('should render all tabs', () => {
      render(<TabNavigation {...defaultProps} />)

      expect(screen.getByText('All Logs')).toBeInTheDocument()
      expect(screen.getByText('Security')).toBeInTheDocument()
      expect(screen.getByText('Activity')).toBeInTheDocument()
    })

    it('should render tab counts', () => {
      render(<TabNavigation {...defaultProps} />)

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('25')).toBeInTheDocument()
      expect(screen.getByText('75')).toBeInTheDocument()
    })

    it('should highlight active tab', () => {
      render(<TabNavigation {...defaultProps} activeTab="security" />)

      const securityButton = screen.getByRole('button', { name: /security/i })
      expect(securityButton).toHaveAttribute('aria-pressed', 'true')
    })
  })

  describe('Tab Switching', () => {
    it('should call onTabChange when tab is clicked', async () => {
      const user = userEvent.setup()
      const onTabChange = vi.fn()
      render(<TabNavigation {...defaultProps} onTabChange={onTabChange} />)

      await user.click(screen.getByRole('button', { name: /security/i }))

      expect(onTabChange).toHaveBeenCalledWith('security')
    })

    it('should call onTabChange with correct tab id', async () => {
      const user = userEvent.setup()
      const onTabChange = vi.fn()
      render(<TabNavigation {...defaultProps} onTabChange={onTabChange} />)

      await user.click(screen.getByRole('button', { name: /activity/i }))

      expect(onTabChange).toHaveBeenCalledWith('activity')
    })
  })

  describe('Severity Filter', () => {
    it('should render filter button when severity options provided', () => {
      render(
        <TabNavigation
          {...defaultProps}
          severity="all"
          onSeverityChange={vi.fn()}
          severityOptions={mockSeverityOptions}
        />
      )

      expect(screen.getByRole('button', { name: /filter by severity/i })).toBeInTheDocument()
    })

    it('should not render filter button when no severity options', () => {
      render(<TabNavigation {...defaultProps} />)

      expect(screen.queryByRole('button', { name: /filter by severity/i })).not.toBeInTheDocument()
    })

    it('should open severity popover on filter click', async () => {
      const user = userEvent.setup()
      render(
        <TabNavigation
          {...defaultProps}
          severity="all"
          onSeverityChange={vi.fn()}
          severityOptions={mockSeverityOptions}
        />
      )

      await user.click(screen.getByRole('button', { name: /filter by severity/i }))

      expect(screen.getByText('Success')).toBeInTheDocument()
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    it('should call onSeverityChange when severity option is selected', async () => {
      const user = userEvent.setup()
      const onSeverityChange = vi.fn()
      render(
        <TabNavigation
          {...defaultProps}
          severity="all"
          onSeverityChange={onSeverityChange}
          severityOptions={mockSeverityOptions}
        />
      )

      await user.click(screen.getByRole('button', { name: /filter by severity/i }))
      await user.click(screen.getByText('Error'))

      expect(onSeverityChange).toHaveBeenCalledWith('error')
    })
  })

  describe('Empty Tabs', () => {
    it('should render without tabs', () => {
      render(<TabNavigation {...defaultProps} tabs={[]} />)

      // Should render the toggle button group even if empty
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have toggle button group role', () => {
      render(<TabNavigation {...defaultProps} />)

      expect(screen.getByRole('group')).toBeInTheDocument()
    })

    it('should have aria-pressed on active tab', () => {
      render(<TabNavigation {...defaultProps} activeTab="all" />)

      const allTab = screen.getByRole('button', { name: /all logs/i })
      expect(allTab).toHaveAttribute('aria-pressed', 'true')
    })

    it('should have aria-pressed false on inactive tabs', () => {
      render(<TabNavigation {...defaultProps} activeTab="all" />)

      const securityTab = screen.getByRole('button', { name: /security/i })
      expect(securityTab).toHaveAttribute('aria-pressed', 'false')
    })
  })
})
