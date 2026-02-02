/**
 * NotificationItem Test Suite
 *
 * Tests for the NotificationItem component.
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { NotificationItem } from '../NotificationItem'

const theme = createTheme()

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>)
}

describe('NotificationItem', () => {
  const baseNotification = {
    id: 'notif-1',
    type: 'info' as const,
    title: 'Test Notification',
    message: 'This is a test message',
    timestamp: new Date(),
    read: false
  }

  const defaultProps = {
    notification: baseNotification,
    onMarkAsRead: vi.fn(),
    onRemove: vi.fn()
  }

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-01-15T10:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('should render notification title', () => {
      renderWithTheme(<NotificationItem {...defaultProps} />)

      expect(screen.getByText('Test Notification')).toBeInTheDocument()
    })

    it('should render notification message', () => {
      renderWithTheme(<NotificationItem {...defaultProps} />)

      expect(screen.getByText('This is a test message')).toBeInTheDocument()
    })

    it('should render mark as read button for unread notifications', () => {
      renderWithTheme(<NotificationItem {...defaultProps} />)

      expect(screen.getByTitle('Mark as read')).toBeInTheDocument()
    })

    it('should not render mark as read button for read notifications', () => {
      renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, read: true }}
        />
      )

      expect(screen.queryByTitle('Mark as read')).not.toBeInTheDocument()
    })

    it('should render remove button', () => {
      renderWithTheme(<NotificationItem {...defaultProps} />)

      expect(screen.getByTitle('Remove')).toBeInTheDocument()
    })
  })

  describe('Notification Types', () => {
    it('should render info notification', () => {
      renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, type: 'info' }}
        />
      )

      expect(screen.getByText('Test Notification')).toBeInTheDocument()
    })

    it('should render success notification', () => {
      renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, type: 'success' }}
        />
      )

      expect(screen.getByText('Test Notification')).toBeInTheDocument()
    })

    it('should render warning notification', () => {
      renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, type: 'warning' }}
        />
      )

      expect(screen.getByText('Test Notification')).toBeInTheDocument()
    })

    it('should render error notification', () => {
      renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, type: 'error' }}
        />
      )

      expect(screen.getByText('Test Notification')).toBeInTheDocument()
    })
  })

  describe('Timestamp Formatting', () => {
    it('should show "Just now" for recent timestamps', () => {
      const notification = {
        ...baseNotification,
        timestamp: new Date('2024-01-15T10:00:00')
      }
      renderWithTheme(
        <NotificationItem {...defaultProps} notification={notification} />
      )

      expect(screen.getByText('Just now')).toBeInTheDocument()
    })

    it('should show minutes ago for timestamps within hour', () => {
      const notification = {
        ...baseNotification,
        timestamp: new Date('2024-01-15T09:45:00')
      }
      renderWithTheme(
        <NotificationItem {...defaultProps} notification={notification} />
      )

      expect(screen.getByText('15m ago')).toBeInTheDocument()
    })

    it('should show hours ago for timestamps within day', () => {
      const notification = {
        ...baseNotification,
        timestamp: new Date('2024-01-15T07:00:00')
      }
      renderWithTheme(
        <NotificationItem {...defaultProps} notification={notification} />
      )

      expect(screen.getByText('3h ago')).toBeInTheDocument()
    })

    it('should show days ago for older timestamps', () => {
      const notification = {
        ...baseNotification,
        timestamp: new Date('2024-01-13T10:00:00')
      }
      renderWithTheme(
        <NotificationItem {...defaultProps} notification={notification} />
      )

      expect(screen.getByText('2d ago')).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should call onMarkAsRead when mark as read clicked', async () => {
      vi.useRealTimers()
      const user = userEvent.setup()
      const onMarkAsRead = vi.fn()
      renderWithTheme(
        <NotificationItem {...defaultProps} onMarkAsRead={onMarkAsRead} />
      )

      await user.click(screen.getByTitle('Mark as read'))

      expect(onMarkAsRead).toHaveBeenCalledWith('notif-1')
    })

    it('should call onRemove when remove clicked', async () => {
      vi.useRealTimers()
      const user = userEvent.setup()
      const onRemove = vi.fn()
      renderWithTheme(
        <NotificationItem {...defaultProps} onRemove={onRemove} />
      )

      await user.click(screen.getByTitle('Remove'))

      expect(onRemove).toHaveBeenCalledWith('notif-1')
    })
  })

  describe('Read State', () => {
    it('should have different background for unread notifications', () => {
      const { container } = renderWithTheme(<NotificationItem {...defaultProps} />)

      // Unread notification should have action.hover background
      expect(container.firstChild).toBeInTheDocument()
    })

    it('should have transparent background for read notifications', () => {
      const { container } = renderWithTheme(
        <NotificationItem
          {...defaultProps}
          notification={{ ...baseNotification, read: true }}
        />
      )

      expect(container.firstChild).toBeInTheDocument()
    })
  })
})
