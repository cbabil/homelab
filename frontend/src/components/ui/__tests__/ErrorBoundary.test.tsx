/**
 * ErrorBoundary Test Suite
 *
 * Tests for the ErrorBoundary component including error catching,
 * fallback rendering, and recovery actions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from '../ErrorBoundary'

// Component that throws an error
function ThrowError({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>Content rendered successfully</div>
}

// Suppress console.error for expected errors in tests
const originalError = console.error
beforeEach(() => {
  console.error = vi.fn()
})
afterEach(() => {
  console.error = originalError
})

describe('ErrorBoundary', () => {
  describe('Normal Rendering', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })

    it('should render multiple children', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should catch errors and show error UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should show error description text', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument()
    })

    it('should show Refresh Page button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /refresh page/i })).toBeInTheDocument()
    })

    it('should show Go Home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /go home/i })).toBeInTheDocument()
    })

    it('should call onError callback when error occurs', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledTimes(1)
      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({ componentStack: expect.any(String) })
      )
    })
  })

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', () => {
      render(
        <ErrorBoundary fallback={<div>Custom error message</div>}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error message')).toBeInTheDocument()
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })
  })

  describe('Recovery Actions', () => {
    it('should have clickable Refresh Page button', async () => {
      const user = userEvent.setup()
      const reloadMock = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { reload: reloadMock, href: '' },
        writable: true
      })

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const refreshButton = screen.getByRole('button', { name: /refresh page/i })
      await user.click(refreshButton)

      expect(reloadMock).toHaveBeenCalled()
    })

    it('should have clickable Go Home button', async () => {
      const user = userEvent.setup()
      const hrefSetter = vi.fn()
      Object.defineProperty(window, 'location', {
        value: {
          reload: vi.fn(),
          get href() { return '' },
          set href(value) { hrefSetter(value) }
        },
        writable: true
      })

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const homeButton = screen.getByRole('button', { name: /go home/i })
      await user.click(homeButton)

      expect(hrefSetter).toHaveBeenCalledWith('/')
    })
  })

  describe('Error Details (Development Mode)', () => {
    it('should show error message in development', () => {
      // import.meta.env.DEV should be true in test environment
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      // Error details should be visible in dev mode
      expect(screen.getByText('Test error message')).toBeInTheDocument()
    })
  })
})
