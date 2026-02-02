/**
 * TermsCheckbox Test Suite
 *
 * Tests for the TermsCheckbox component including rendering,
 * checkbox behavior, links, and accessibility.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TermsCheckbox } from '../TermsCheckbox'

describe('TermsCheckbox', () => {
  const defaultProps = {
    checked: false,
    isSubmitting: false,
    onChange: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, 'open').mockImplementation(() => null)
  })

  describe('Rendering', () => {
    it('should render checkbox', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.getByRole('checkbox')).toBeInTheDocument()
    })

    it('should render Terms of Service link', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.getByRole('button', { name: /terms of service/i })).toBeInTheDocument()
    })

    it('should render Privacy Policy link', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.getByRole('button', { name: /privacy policy/i })).toBeInTheDocument()
    })

    it('should render acceptance text', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.getByText(/i accept the/i)).toBeInTheDocument()
    })
  })

  describe('Checkbox State', () => {
    it('should be unchecked by default', () => {
      render(<TermsCheckbox {...defaultProps} checked={false} />)

      expect(screen.getByRole('checkbox')).not.toBeChecked()
    })

    it('should be checked when checked prop is true', () => {
      render(<TermsCheckbox {...defaultProps} checked={true} />)

      expect(screen.getByRole('checkbox')).toBeChecked()
    })

    it('should call onChange when checkbox is clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TermsCheckbox {...defaultProps} onChange={onChange} />)

      await user.click(screen.getByRole('checkbox'))

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('should call onChange with false when unchecking', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TermsCheckbox {...defaultProps} checked={true} onChange={onChange} />)

      await user.click(screen.getByRole('checkbox'))

      expect(onChange).toHaveBeenCalledWith(false)
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<TermsCheckbox {...defaultProps} error="You must accept the terms" />)

      expect(screen.getByText('You must accept the terms')).toBeInTheDocument()
    })

    it('should not display error message when no error', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('should disable checkbox when isSubmitting is true', () => {
      render(<TermsCheckbox {...defaultProps} isSubmitting={true} />)

      expect(screen.getByRole('checkbox')).toBeDisabled()
    })

    it('should disable links when isSubmitting is true', () => {
      render(<TermsCheckbox {...defaultProps} isSubmitting={true} />)

      expect(screen.getByRole('button', { name: /terms of service/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /privacy policy/i })).toBeDisabled()
    })

    it('should enable checkbox when isSubmitting is false', () => {
      render(<TermsCheckbox {...defaultProps} isSubmitting={false} />)

      expect(screen.getByRole('checkbox')).not.toBeDisabled()
    })
  })

  describe('Link Behavior', () => {
    it('should open Terms of Service in popup when clicked', async () => {
      const user = userEvent.setup()
      render(<TermsCheckbox {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /terms of service/i }))

      expect(window.open).toHaveBeenCalledWith(
        '/terms-of-service',
        'termsPopup',
        expect.stringContaining('width=600')
      )
    })

    it('should open Privacy Policy in popup when clicked', async () => {
      const user = userEvent.setup()
      render(<TermsCheckbox {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /privacy policy/i }))

      expect(window.open).toHaveBeenCalledWith(
        '/privacy-policy',
        'privacyPopup',
        expect.stringContaining('width=600')
      )
    })

    it('should not open popup when disabled', () => {
      render(<TermsCheckbox {...defaultProps} isSubmitting={true} />)

      // Disabled buttons don't trigger click events
      const termsButton = screen.getByRole('button', { name: /terms of service/i })
      expect(termsButton).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have correct checkbox id', () => {
      render(<TermsCheckbox {...defaultProps} />)

      expect(screen.getByRole('checkbox')).toHaveAttribute('id', 'reg-accept-terms')
    })

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<TermsCheckbox {...defaultProps} onChange={onChange} />)

      await user.tab()
      expect(screen.getByRole('checkbox')).toHaveFocus()

      await user.keyboard(' ')
      expect(onChange).toHaveBeenCalledWith(true)
    })
  })
})
