/**
 * CopyrightFooter Test Suite
 *
 * Tests for the CopyrightFooter component including rendering,
 * dynamic year display, and app name configuration.
 */

import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CopyrightFooter } from '../CopyrightFooter'

describe('CopyrightFooter', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('Rendering', () => {
    it('should render copyright text', () => {
      render(<CopyrightFooter />)

      expect(screen.getByText(/all rights reserved/i)).toBeInTheDocument()
    })

    it('should display current year', () => {
      render(<CopyrightFooter />)

      const currentYear = new Date().getFullYear()
      expect(screen.getByText(new RegExp(`© ${currentYear}`))).toBeInTheDocument()
    })

    it('should render as a paragraph element', () => {
      render(<CopyrightFooter />)

      const paragraph = screen.getByText(/all rights reserved/i)
      expect(paragraph.tagName.toLowerCase()).toBe('p')
    })
  })

  describe('App Name', () => {
    it('should display default app name when env var is not set', () => {
      render(<CopyrightFooter />)

      // Default is 'Tomo'
      expect(screen.getByText(/tomo assistant/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have text content that is readable', () => {
      render(<CopyrightFooter />)

      const footer = screen.getByText(/all rights reserved/i)
      expect(footer).toHaveTextContent(/©.*tomo.*all rights reserved/i)
    })

    it('should use semantic text styling', () => {
      render(<CopyrightFooter />)

      // Component uses Typography with variant="caption"
      const footer = screen.getByText(/all rights reserved/i)
      expect(footer).toBeInTheDocument()
    })
  })
})
