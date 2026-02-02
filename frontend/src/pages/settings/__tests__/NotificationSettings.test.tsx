/**
 * NotificationSettings Test Suite
 *
 * Tests for the NotificationSettings component including
 * server, resource, and update alert toggles.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { NotificationSettings } from '../NotificationSettings'

describe('NotificationSettings', () => {
  const defaultProps = {
    serverAlerts: true,
    resourceAlerts: true,
    updateAlerts: false,
    onServerAlertsChange: vi.fn(),
    onResourceAlertsChange: vi.fn(),
    onUpdateAlertsChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render system alerts section', () => {
      render(<NotificationSettings {...defaultProps} />)

      expect(screen.getByText('System Alerts')).toBeInTheDocument()
    })

    it('should render all alert toggles', () => {
      render(<NotificationSettings {...defaultProps} />)

      expect(screen.getByText('Server alerts')).toBeInTheDocument()
      expect(screen.getByText('Resource alerts')).toBeInTheDocument()
      expect(screen.getByText('Update alerts')).toBeInTheDocument()
    })

    it('should render correct number of toggle switches', () => {
      render(<NotificationSettings {...defaultProps} />)

      const switches = screen.getAllByRole('switch')
      expect(switches).toHaveLength(3)
    })
  })

  describe('Toggle States', () => {
    it('should reflect serverAlerts state', () => {
      render(<NotificationSettings {...defaultProps} serverAlerts={true} />)

      const switches = screen.getAllByRole('switch')
      expect(switches[0]).toHaveAttribute('aria-checked', 'true')
    })

    it('should reflect resourceAlerts state', () => {
      render(<NotificationSettings {...defaultProps} resourceAlerts={false} />)

      const switches = screen.getAllByRole('switch')
      expect(switches[1]).toHaveAttribute('aria-checked', 'false')
    })

    it('should reflect updateAlerts state', () => {
      render(<NotificationSettings {...defaultProps} updateAlerts={true} />)

      const switches = screen.getAllByRole('switch')
      expect(switches[2]).toHaveAttribute('aria-checked', 'true')
    })
  })

  describe('Interactions', () => {
    it('should call onServerAlertsChange when server alerts toggle is clicked', () => {
      const onServerAlertsChange = vi.fn()
      render(<NotificationSettings {...defaultProps} onServerAlertsChange={onServerAlertsChange} />)

      const switches = screen.getAllByRole('switch')
      fireEvent.click(switches[0])

      expect(onServerAlertsChange).toHaveBeenCalled()
    })

    it('should call onResourceAlertsChange when resource alerts toggle is clicked', () => {
      const onResourceAlertsChange = vi.fn()
      render(<NotificationSettings {...defaultProps} onResourceAlertsChange={onResourceAlertsChange} />)

      const switches = screen.getAllByRole('switch')
      fireEvent.click(switches[1])

      expect(onResourceAlertsChange).toHaveBeenCalled()
    })

    it('should call onUpdateAlertsChange when update alerts toggle is clicked', () => {
      const onUpdateAlertsChange = vi.fn()
      render(<NotificationSettings {...defaultProps} onUpdateAlertsChange={onUpdateAlertsChange} />)

      const switches = screen.getAllByRole('switch')
      fireEvent.click(switches[2])

      expect(onUpdateAlertsChange).toHaveBeenCalled()
    })
  })
})
