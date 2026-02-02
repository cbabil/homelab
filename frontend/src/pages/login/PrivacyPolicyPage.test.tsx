/**
 * PrivacyPolicyPage Test Suite
 *
 * Tests for PrivacyPolicyPage component including rendering,
 * content display, and window close functionality.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { PrivacyPolicyPage } from './PrivacyPolicyPage'

// Mock window.close
const { mockWindowClose } = vi.hoisted(() => {
  const mockWindowClose = vi.fn()
  return { mockWindowClose }
})

Object.defineProperty(window, 'close', {
  writable: true,
  value: mockWindowClose
})

// Mock PrivacyPolicyContent component
vi.mock('@/components/legal/PrivacyPolicyContent', () => ({
  PrivacyPolicyContent: () => (
    <div data-testid="privacy-policy-content">
      <p>Mocked privacy policy content</p>
    </div>
  )
}))

describe('PrivacyPolicyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering and UI', () => {
    it('should render privacy policy page correctly', () => {
      render(<PrivacyPolicyPage />)

      expect(screen.getByRole('heading', { name: /privacy policy/i })).toBeInTheDocument()
      expect(screen.getByTestId('privacy-policy-content')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /close window/i })).toBeInTheDocument()
    })

    it('should have proper page structure with MUI Paper layout', () => {
      render(<PrivacyPolicyPage />)

      const heading = screen.getByRole('heading', { name: /privacy policy/i })
      expect(heading).toBeInTheDocument()
      expect(heading.closest('.MuiPaper-root')).toBeInTheDocument()
    })

    it('should display privacy policy content', () => {
      render(<PrivacyPolicyPage />)

      expect(screen.getByText(/mocked privacy policy content/i)).toBeInTheDocument()
    })
  })

  describe('Window Close Functionality', () => {
    it('should call window.close when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<PrivacyPolicyPage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      await user.click(closeButton)

      expect(mockWindowClose).toHaveBeenCalledOnce()
    })

    it('should have MUI contained button styling', () => {
      render(<PrivacyPolicyPage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toHaveClass('MuiButton-contained')
    })
  })

  describe('Layout and Styling', () => {
    it('should render within MUI Box container', () => {
      render(<PrivacyPolicyPage />)

      const heading = screen.getByRole('heading', { name: /privacy policy/i })
      expect(heading).toBeInTheDocument()
    })

    it('should use MUI Container for content width', () => {
      render(<PrivacyPolicyPage />)

      const container = document.querySelector('.MuiContainer-root')
      expect(container).toBeInTheDocument()
    })

    it('should use MUI Paper for card styling', () => {
      render(<PrivacyPolicyPage />)

      const paper = document.querySelector('.MuiPaper-root')
      expect(paper).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<PrivacyPolicyPage />)

      const heading = screen.getByRole('heading', { name: /privacy policy/i })
      expect(heading).toBeInTheDocument()
      expect(heading.tagName).toBe('H3')
    })

    it('should have accessible close button', () => {
      render(<PrivacyPolicyPage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toBeInTheDocument()
      expect(closeButton).toHaveAccessibleName()
    })
  })
})
