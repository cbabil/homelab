/**
 * SessionWarning Test Suite
 *
 * Tests for the SessionWarning component including rendering,
 * severity levels, actions, and time formatting.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SessionWarning } from '../SessionWarning'
import { SessionWarning as SessionWarningType } from '@/types/auth'

const createWarning = (
  overrides: Partial<SessionWarningType> = {}
): SessionWarningType => ({
  isShowing: true,
  warningLevel: 'warning',
  minutesRemaining: 5,
  ...overrides
})

describe('SessionWarning', () => {
  describe('Rendering', () => {
    it('should not render when isShowing is false', () => {
      const { container } = render(
        <SessionWarning warning={createWarning({ isShowing: false })} />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should render when isShowing is true', () => {
      render(<SessionWarning warning={createWarning()} />)

      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument()
    })

    it('should show time remaining', () => {
      render(<SessionWarning warning={createWarning({ minutesRemaining: 5 })} />)

      expect(screen.getByText('5 minutes remaining')).toBeInTheDocument()
    })
  })

  describe('Time Formatting', () => {
    it('should show singular "minute" for 1 minute', () => {
      render(<SessionWarning warning={createWarning({ minutesRemaining: 1 })} />)

      expect(screen.getByText('1 minute remaining')).toBeInTheDocument()
    })

    it('should show plural "minutes" for multiple minutes', () => {
      render(<SessionWarning warning={createWarning({ minutesRemaining: 10 })} />)

      expect(screen.getByText('10 minutes remaining')).toBeInTheDocument()
    })

    it('should show "Session has expired" for 0 minutes', () => {
      render(<SessionWarning warning={createWarning({ minutesRemaining: 0 })} />)

      expect(screen.getByText('Session has expired')).toBeInTheDocument()
    })
  })

  describe('Warning Levels', () => {
    it('should show "Session Expiring Soon" for warning level', () => {
      render(<SessionWarning warning={createWarning({ warningLevel: 'warning' })} />)

      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument()
    })

    it('should show "Session Expiring Soon" for info level', () => {
      render(
        <SessionWarning
          warning={createWarning({ warningLevel: 'info', minutesRemaining: 10 })}
        />
      )

      expect(screen.getByText('Session Expiring Soon')).toBeInTheDocument()
    })

    it('should show "Session Expired" for critical level with 1 minute', () => {
      render(
        <SessionWarning
          warning={createWarning({ warningLevel: 'critical', minutesRemaining: 1 })}
        />
      )

      expect(screen.getByText('Session Expired')).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should render Extend Session button when not urgent', () => {
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onExtendSession={vi.fn()}
        />
      )

      expect(screen.getByRole('button', { name: /extend session/i })).toBeInTheDocument()
    })

    it('should not render Extend Session button when urgent (1 minute)', () => {
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 1 })}
          onExtendSession={vi.fn()}
        />
      )

      expect(screen.queryByRole('button', { name: /extend session/i })).not.toBeInTheDocument()
    })

    it('should call onExtendSession when button clicked', async () => {
      const user = userEvent.setup()
      const onExtendSession = vi.fn()
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onExtendSession={onExtendSession}
        />
      )

      await user.click(screen.getByRole('button', { name: /extend session/i }))

      expect(onExtendSession).toHaveBeenCalledTimes(1)
    })

    it('should render Logout button', () => {
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onLogout={vi.fn()}
        />
      )

      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
    })

    it('should show "Login Again" when urgent', () => {
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 1 })}
          onLogout={vi.fn()}
        />
      )

      expect(screen.getByRole('button', { name: /login again/i })).toBeInTheDocument()
    })

    it('should call onLogout when button clicked', async () => {
      const user = userEvent.setup()
      const onLogout = vi.fn()
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onLogout={onLogout}
        />
      )

      await user.click(screen.getByRole('button', { name: /logout/i }))

      expect(onLogout).toHaveBeenCalledTimes(1)
    })

    it('should render dismiss button when not urgent', () => {
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onDismiss={vi.fn()}
        />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should not render dismiss button when urgent', () => {
      const { container } = render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 1 })}
          onDismiss={vi.fn()}
          onLogout={vi.fn()}
        />
      )

      // Only logout button should be present
      const buttons = container.querySelectorAll('button')
      expect(buttons).toHaveLength(1)
    })

    it('should call onDismiss when dismiss clicked', async () => {
      const user = userEvent.setup()
      const onDismiss = vi.fn()
      render(
        <SessionWarning
          warning={createWarning({ minutesRemaining: 5 })}
          onDismiss={onDismiss}
        />
      )

      // Find the close button (IconButton)
      const closeButton = screen.getByRole('button')
      await user.click(closeButton)

      expect(onDismiss).toHaveBeenCalledTimes(1)
    })
  })

  describe('No Actions Provided', () => {
    it('should render without action buttons when none provided', () => {
      const { container } = render(
        <SessionWarning warning={createWarning({ minutesRemaining: 5 })} />
      )

      expect(container.querySelectorAll('button')).toHaveLength(0)
    })
  })
})
