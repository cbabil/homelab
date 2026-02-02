/**
 * PrivacyPolicyContent Test Suite
 *
 * Tests for the PrivacyPolicyContent component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PrivacyPolicyContent } from '../PrivacyPolicyContent'

describe('PrivacyPolicyContent', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-03-15'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('should render last updated date', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
    })

    it('should render section 1 - Information We Collect', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('1. Information We Collect')).toBeInTheDocument()
    })

    it('should render section 2 - How We Use Your Information', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('2. How We Use Your Information')).toBeInTheDocument()
    })

    it('should render section 3 - Data Storage and Security', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('3. Data Storage and Security')).toBeInTheDocument()
    })

    it('should render section 4 - Data Sharing', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('4. Data Sharing')).toBeInTheDocument()
    })

    it('should render section 5 - Data Retention', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('5. Data Retention')).toBeInTheDocument()
    })

    it('should render section 6 - Your Rights', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('6. Your Rights')).toBeInTheDocument()
    })

    it('should render section 7 - Contact Information', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText('7. Contact Information')).toBeInTheDocument()
    })
  })

  describe('Content', () => {
    it('should mention self-hosted application', () => {
      render(<PrivacyPolicyContent />)

      // Multiple elements contain this text, so use getAllByText
      const elements = screen.getAllByText(/self-hosted/i)
      expect(elements.length).toBeGreaterThan(0)
    })

    it('should mention account information', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText(/Account Information:/)).toBeInTheDocument()
    })

    it('should mention server connections', () => {
      render(<PrivacyPolicyContent />)

      expect(screen.getByText(/Server Connections:/)).toBeInTheDocument()
    })

    it('should mention data not shared with third parties', () => {
      render(<PrivacyPolicyContent />)

      expect(
        screen.getByText(/We do not share your data with third parties/i)
      ).toBeInTheDocument()
    })

    it('should mention password hashing', () => {
      render(<PrivacyPolicyContent />)

      expect(
        screen.getByText(/Passwords are hashed using industry-standard algorithms/)
      ).toBeInTheDocument()
    })

    it('should mention JWT standards', () => {
      render(<PrivacyPolicyContent />)

      expect(
        screen.getByText(/Session tokens use secure JWT standards/)
      ).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should render sections as semantic sections', () => {
      const { container } = render(<PrivacyPolicyContent />)

      // Should have multiple sections
      const sections = container.querySelectorAll('section')
      expect(sections.length).toBe(7)
    })

    it('should have proper heading hierarchy', () => {
      render(<PrivacyPolicyContent />)

      const headings = screen.getAllByRole('heading', { level: 5 })
      expect(headings.length).toBe(7)
    })
  })
})
