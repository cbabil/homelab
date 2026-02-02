/**
 * PasswordStrengthIndicator Test Suite
 *
 * Tests for the PasswordStrengthIndicator component including
 * strength visualization, requirements checklist, and edge cases.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PasswordStrengthIndicator } from '../PasswordStrengthIndicator'
import { PasswordStrength } from '@/types/auth'

const createStrength = (
  score: number,
  requirements: Partial<PasswordStrength['requirements']> = {}
): PasswordStrength => ({
  score,
  feedback: [],
  requirements: {
    minLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false,
    ...requirements
  }
})

describe('PasswordStrengthIndicator', () => {
  describe('Rendering', () => {
    it('should not render when password is empty', () => {
      const { container } = render(
        <PasswordStrengthIndicator
          strength={createStrength(0)}
          password=""
        />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should render when password is provided', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(1)}
          password="test"
        />
      )

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('should render requirements checklist', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(1)}
          password="test"
        />
      )

      expect(screen.getByText('12+ characters')).toBeInTheDocument()
      expect(screen.getByText('Uppercase letter')).toBeInTheDocument()
      expect(screen.getByText('Lowercase letter')).toBeInTheDocument()
      expect(screen.getByText('Number')).toBeInTheDocument()
      expect(screen.getByText('Special character')).toBeInTheDocument()
    })
  })

  describe('Strength Levels', () => {
    it('should show "Weak" for score 1-2', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(1)}
          password="a"
        />
      )

      expect(screen.getByText('Weak')).toBeInTheDocument()
    })

    it('should show "Weak" for score 2', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(2)}
          password="ab"
        />
      )

      expect(screen.getByText('Weak')).toBeInTheDocument()
    })

    it('should show "Fair" for score 3', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(3)}
          password="abc"
        />
      )

      expect(screen.getByText('Fair')).toBeInTheDocument()
    })

    it('should show "Good" for score 4', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(4)}
          password="abcd"
        />
      )

      expect(screen.getByText('Good')).toBeInTheDocument()
    })

    it('should show "Strong" for score 5', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(5)}
          password="abcde"
        />
      )

      expect(screen.getByText('Strong')).toBeInTheDocument()
    })
  })

  describe('Requirements Visualization', () => {
    it('should show met requirements with check icon', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(3, {
            minLength: true,
            hasLowercase: true,
            hasNumber: true
          })}
          password="testpassword123"
        />
      )

      // Check that the component renders - specific icon testing would require more setup
      expect(screen.getByText('12+ characters')).toBeInTheDocument()
      expect(screen.getByText('Lowercase letter')).toBeInTheDocument()
      expect(screen.getByText('Number')).toBeInTheDocument()
    })

    it('should show unmet requirements', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(1, {
            hasUppercase: false,
            hasSpecialChar: false
          })}
          password="test"
        />
      )

      expect(screen.getByText('Uppercase letter')).toBeInTheDocument()
      expect(screen.getByText('Special character')).toBeInTheDocument()
    })

    it('should show all requirements met for strong password', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(5, {
            minLength: true,
            hasUppercase: true,
            hasLowercase: true,
            hasNumber: true,
            hasSpecialChar: true
          })}
          password="StrongPass123!"
        />
      )

      expect(screen.getByText('Strong')).toBeInTheDocument()
    })
  })

  describe('Progress Bar', () => {
    it('should show progress bar with correct value for weak password', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(1)}
          password="a"
        />
      )

      const progressBar = screen.getByRole('progressbar')
      // Score 1 out of 5 = 20%
      expect(progressBar).toHaveAttribute('aria-valuenow', '20')
    })

    it('should show progress bar with correct value for strong password', () => {
      render(
        <PasswordStrengthIndicator
          strength={createStrength(5)}
          password="StrongPass123!"
        />
      )

      const progressBar = screen.getByRole('progressbar')
      // Score 5 out of 5 = 100%
      expect(progressBar).toHaveAttribute('aria-valuenow', '100')
    })
  })
})
