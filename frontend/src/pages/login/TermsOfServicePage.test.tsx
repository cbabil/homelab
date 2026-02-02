/**
 * TermsOfServicePage Test Suite
 *
 * Tests for TermsOfServicePage component including rendering,
 * content display, and window close functionality.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { TermsOfServicePage } from './TermsOfServicePage'

// Mock window.close
const { mockWindowClose } = vi.hoisted(() => {
  const mockWindowClose = vi.fn()
  return { mockWindowClose }
})

Object.defineProperty(window, 'close', {
  writable: true,
  value: mockWindowClose
})

describe('TermsOfServicePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering and UI', () => {
    it('should render terms of service page correctly', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByRole('heading', { name: /terms of service/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /close window/i })).toBeInTheDocument()
    })

    it('should display last updated date', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByText(/last updated:/i)).toBeInTheDocument()
    })

    it('should display all main sections', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByRole('heading', { name: /1\. acceptance of terms/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /2\. service description/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /3\. user responsibilities/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /4\. data and privacy/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /5\. security considerations/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /6\. limitation of liability/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /7\. changes to terms/i })).toBeInTheDocument()
    })

    it('should have proper page structure with MUI Paper layout', () => {
      render(<TermsOfServicePage />)

      // MUI Paper component should be present
      const heading = screen.getByRole('heading', { name: /terms of service/i })
      expect(heading).toBeInTheDocument()
      // Check parent structure exists
      expect(heading.closest('.MuiPaper-root')).toBeInTheDocument()
    })
  })

  describe('Content Sections', () => {
    it('should display acceptance of terms content', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByText(/by accessing and using the tomo assistant application/i)).toBeInTheDocument()
    })

    it('should display service description content', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByText(/tomo assistant is a self-hosted application/i)).toBeInTheDocument()
    })

    it('should display user responsibilities list', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByText(/you are responsible for maintaining the confidentiality/i)).toBeInTheDocument()
      expect(screen.getByText(/you agree to use the service only for lawful purposes/i)).toBeInTheDocument()
      expect(screen.getByText(/you are responsible for securing your tomo infrastructure/i)).toBeInTheDocument()
      expect(screen.getByText(/you agree not to attempt to breach security measures/i)).toBeInTheDocument()
    })

    it('should display security considerations list', () => {
      render(<TermsOfServicePage />)

      expect(screen.getByText(/use strong, unique passwords/i)).toBeInTheDocument()
      expect(screen.getByText(/keep the application updated/i)).toBeInTheDocument()
      expect(screen.getByText(/monitor access logs/i)).toBeInTheDocument()
      expect(screen.getByText(/report security issues responsibly/i)).toBeInTheDocument()
    })
  })

  describe('Window Close Functionality', () => {
    it('should call window.close when close button is clicked', async () => {
      const user = userEvent.setup()
      render(<TermsOfServicePage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      await user.click(closeButton)

      expect(mockWindowClose).toHaveBeenCalledOnce()
    })

    it('should have MUI contained button styling', () => {
      render(<TermsOfServicePage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toHaveClass('MuiButton-contained')
    })
  })

  describe('Layout and Styling', () => {
    it('should render within MUI Box container', () => {
      render(<TermsOfServicePage />)

      const heading = screen.getByRole('heading', { name: /terms of service/i })
      expect(heading).toBeInTheDocument()
    })

    it('should use MUI Container for content width', () => {
      render(<TermsOfServicePage />)

      const container = document.querySelector('.MuiContainer-root')
      expect(container).toBeInTheDocument()
    })

    it('should use MUI Paper for card styling', () => {
      render(<TermsOfServicePage />)

      const paper = document.querySelector('.MuiPaper-root')
      expect(paper).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<TermsOfServicePage />)

      const mainHeading = screen.getByRole('heading', { name: /terms of service/i })
      expect(mainHeading).toBeInTheDocument()
      expect(mainHeading.tagName).toBe('H3')

      // Section headings are h5 in MUI
      const sectionHeadings = screen.getAllByRole('heading', { level: 5 })
      expect(sectionHeadings).toHaveLength(7)
    })

    it('should have accessible lists with proper structure', () => {
      render(<TermsOfServicePage />)

      const lists = screen.getAllByRole('list')
      expect(lists).toHaveLength(2) // User responsibilities and security considerations

      const listItems = screen.getAllByRole('listitem')
      expect(listItems.length).toBeGreaterThan(6) // At least 4 + 4 items
    })

    it('should have accessible close button', () => {
      render(<TermsOfServicePage />)

      const closeButton = screen.getByRole('button', { name: /close window/i })
      expect(closeButton).toBeInTheDocument()
      expect(closeButton).toHaveAccessibleName()
    })
  })
})
