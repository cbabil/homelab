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
const mockWindowClose = vi.fn()
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

    it('should have proper page structure with card layout', () => {
      render(<PrivacyPolicyPage />)
      
      const container = screen.getByRole('heading').closest('div.bg-card')
      expect(container).toBeInTheDocument()
      expect(container).toHaveClass('rounded-lg', 'border', 'shadow-sm')
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

    it('should have proper close button styling', () => {
      render(<PrivacyPolicyPage />)
      
      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toHaveClass(
        'bg-primary',
        'text-primary-foreground',
        'hover:bg-primary/90',
        'px-6',
        'py-2',
        'rounded-md',
        'transition-colors'
      )
    })
  })

  describe('Layout and Styling', () => {
    it('should have full height layout with proper styling', () => {
      render(<PrivacyPolicyPage />)
      
      const container = document.querySelector('.min-h-screen')
      expect(container).toBeInTheDocument()
      expect(container).toHaveClass('bg-background', 'p-8')
    })

    it('should center content with max width', () => {
      render(<PrivacyPolicyPage />)
      
      const contentContainer = document.querySelector('.max-w-4xl')
      expect(contentContainer).toBeInTheDocument()
      expect(contentContainer).toHaveClass('mx-auto')
    })

    it('should have proper footer section with border', () => {
      render(<PrivacyPolicyPage />)
      
      const footer = screen.getByRole('button', { name: /close window/i }).closest('div.mt-8')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('pt-6', 'border-t', 'text-center')
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<PrivacyPolicyPage />)
      
      const heading = screen.getByRole('heading', { name: /privacy policy/i })
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-foreground', 'mb-6')
    })

    it('should have accessible close button', () => {
      render(<PrivacyPolicyPage />)
      
      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toBeInTheDocument()
      expect(closeButton).toHaveAccessibleName()
    })
  })
})