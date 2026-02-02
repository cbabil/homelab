/**
 * Toast Test Suite
 *
 * Tests for the Toast notification system.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from '../Toast'

// Test component that uses the toast hook
function ToastConsumer({ type = 'success' as 'success' | 'error' | 'warning' | 'info', title = 'Test', message = '' }) {
  const { addToast } = useToast()

  return (
    <button onClick={() => addToast({ type, title, message })}>
      Show Toast
    </button>
  )
}

describe('Toast', () => {
  describe('ToastProvider', () => {
    it('should render children', () => {
      render(
        <ToastProvider>
          <div>Child content</div>
        </ToastProvider>
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })
  })

  describe('useToast', () => {
    it('should throw error when used outside provider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<ToastConsumer />)
      }).toThrow('useToast must be used within a ToastProvider')

      consoleSpy.mockRestore()
    })
  })

  describe('Toast Display', () => {
    it('should show success toast', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="success" title="Success!" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument()
      })
    })

    it('should show error toast', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="error" title="Error occurred" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Error occurred')).toBeInTheDocument()
      })
    })

    it('should show warning toast', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="warning" title="Warning!" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Warning!')).toBeInTheDocument()
      })
    })

    it('should show info toast', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="info" title="Info" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Info')).toBeInTheDocument()
      })
    })

    it('should show toast with message', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="success" title="Title" message="Additional details" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Title')).toBeInTheDocument()
        expect(screen.getByText('Additional details')).toBeInTheDocument()
      })
    })
  })

  describe('Toast Accessibility', () => {
    it('should use alert role for error toasts', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="error" title="Error" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })
    })

    it('should use alert role for warning toasts', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="warning" title="Warning" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })
    })

    it('should use status role for success toasts', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="success" title="Success" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
      })
    })

    it('should use status role for info toasts', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="info" title="Info" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument()
      })
    })

    it('should have accessible dismiss button', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="success" title="Test Toast" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        const dismissButton = screen.getByLabelText(/Dismiss success notification: Test Toast/i)
        expect(dismissButton).toBeInTheDocument()
      })
    })
  })

  describe('Toast Dismissal', () => {
    it('should dismiss toast when close button clicked', async () => {
      const user = userEvent.setup()
      render(
        <ToastProvider>
          <ToastConsumer type="success" title="Dismissable" />
        </ToastProvider>
      )

      await user.click(screen.getByText('Show Toast'))

      await waitFor(() => {
        expect(screen.getByText('Dismissable')).toBeInTheDocument()
      })

      const dismissButton = screen.getByLabelText(/Dismiss success notification/i)
      await user.click(dismissButton)

      await waitFor(
        () => {
          expect(screen.queryByText('Dismissable')).not.toBeInTheDocument()
        },
        { timeout: 1000 }
      )
    })
  })

  describe('Multiple Toasts', () => {
    it('should show multiple toasts', async () => {
      const user = userEvent.setup()

      function MultiToastConsumer() {
        const { addToast } = useToast()

        return (
          <>
            <button onClick={() => addToast({ type: 'success', title: 'Success Toast' })}>
              Add Success
            </button>
            <button onClick={() => addToast({ type: 'error', title: 'Error Toast' })}>
              Add Error
            </button>
          </>
        )
      }

      render(
        <ToastProvider>
          <MultiToastConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByText('Add Success'))
      await user.click(screen.getByText('Add Error'))

      await waitFor(() => {
        expect(screen.getByText('Success Toast')).toBeInTheDocument()
        expect(screen.getByText('Error Toast')).toBeInTheDocument()
      })
    })
  })
})
