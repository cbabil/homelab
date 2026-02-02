/**
 * Modal Component Test Suite
 *
 * Tests for the Modal component including rendering, keyboard interactions,
 * focus management, backdrop click, and accessibility.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Modal, ModalHeader, ModalBody, ModalFooter } from '../Modal'

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    children: <div>Modal content</div>
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    document.body.style.overflow = ''
  })

  describe('Rendering', () => {
    it('should render when isOpen is true', () => {
      render(<Modal {...defaultProps} />)

      expect(screen.getByText('Modal content')).toBeInTheDocument()
    })

    it('should not render when isOpen is false', () => {
      render(<Modal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
    })

    it('should render title when provided', () => {
      render(<Modal {...defaultProps} title="Test Title" />)

      expect(screen.getByText('Test Title')).toBeInTheDocument()
    })

    it('should render footer when provided', () => {
      render(
        <Modal {...defaultProps} footer={<button>Save</button>} />
      )

      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument()
    })

    it('should render close button by default', () => {
      render(<Modal {...defaultProps} title="Title" />)

      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })

    it('should hide close button when showCloseButton is false', () => {
      render(<Modal {...defaultProps} title="Title" showCloseButton={false} />)

      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it.each(['sm', 'md', 'lg', 'xl', 'full'] as const)('should render %s size', (size) => {
      render(<Modal {...defaultProps} size={size} />)

      expect(screen.getByText('Modal content')).toBeInTheDocument()
    })
  })

  describe('Close Behavior', () => {
    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} title="Title" onClose={onClose} />)

      await user.click(screen.getByRole('button', { name: /close/i }))

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} onClose={onClose} />)

      const backdrop = screen.getByRole('dialog')
      await user.click(backdrop)

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('should not call onClose when modal content is clicked', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} onClose={onClose} />)

      await user.click(screen.getByText('Modal content'))

      expect(onClose).not.toHaveBeenCalled()
    })

    it('should not close on backdrop click when closeOnBackdrop is false', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} onClose={onClose} closeOnBackdrop={false} />)

      const backdrop = screen.getByRole('dialog')
      await user.click(backdrop)

      expect(onClose).not.toHaveBeenCalled()
    })
  })

  describe('Keyboard Interactions', () => {
    it('should close on Escape key press', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} onClose={onClose} />)

      await user.keyboard('{Escape}')

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('should not close on Escape when closeOnEscape is false', async () => {
      const user = userEvent.setup()
      const onClose = vi.fn()
      render(<Modal {...defaultProps} onClose={onClose} closeOnEscape={false} />)

      await user.keyboard('{Escape}')

      expect(onClose).not.toHaveBeenCalled()
    })
  })

  describe('Focus Management', () => {
    it('should focus first focusable element on open', async () => {
      render(
        <Modal {...defaultProps} title="Title">
          <input data-testid="input1" />
          <button>Button 1</button>
        </Modal>
      )

      // First focusable element (close button) should receive focus
      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i })
        expect(closeButton).toHaveFocus()
      })
    })

    it('should lock body scroll when open', () => {
      render(<Modal {...defaultProps} />)

      expect(document.body.style.overflow).toBe('hidden')
    })

    it('should restore body scroll when closed', () => {
      const { rerender } = render(<Modal {...defaultProps} />)

      rerender(<Modal {...defaultProps} isOpen={false} />)

      expect(document.body.style.overflow).toBe('')
    })
  })

  describe('Accessibility', () => {
    it('should have role="dialog"', () => {
      render(<Modal {...defaultProps} />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should have aria-modal="true"', () => {
      render(<Modal {...defaultProps} />)

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
    })

    it('should have aria-labelledby when title is provided', () => {
      render(<Modal {...defaultProps} title="Test Title" />)

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'modal-title')
    })

    it('should not have aria-labelledby when no title', () => {
      render(<Modal {...defaultProps} />)

      expect(screen.getByRole('dialog')).not.toHaveAttribute('aria-labelledby')
    })
  })
})

describe('ModalHeader', () => {
  it('should render children', () => {
    render(<ModalHeader>Header Content</ModalHeader>)

    expect(screen.getByText('Header Content')).toBeInTheDocument()
  })
})

describe('ModalBody', () => {
  it('should render children', () => {
    render(<ModalBody>Body Content</ModalBody>)

    expect(screen.getByText('Body Content')).toBeInTheDocument()
  })
})

describe('ModalFooter', () => {
  it('should render children', () => {
    render(<ModalFooter>Footer Content</ModalFooter>)

    expect(screen.getByText('Footer Content')).toBeInTheDocument()
  })
})
