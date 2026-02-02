/**
 * Registration Validation Tests
 *
 * Tests for username, email, and password validation.
 */

import { describe, it, expect } from 'vitest'
import {
  validateUsername,
  validateEmail,
  validatePassword,
  calculatePasswordStrength
} from '../registrationValidation'

describe('validateUsername', () => {
  it('rejects empty username', () => {
    const result = validateUsername('')
    expect(result.isValid).toBe(false)
    expect(result.error).toContain('required')
  })

  it('rejects username shorter than minimum', () => {
    const result = validateUsername('ab')
    expect(result.isValid).toBe(false)
    expect(result.error).toContain('3')
  })

  it('accepts valid username', () => {
    const result = validateUsername('john_doe123')
    expect(result.isValid).toBe(true)
  })

  it('rejects username with special characters', () => {
    const result = validateUsername('john@doe')
    expect(result.isValid).toBe(false)
  })
})

describe('validateEmail', () => {
  it('rejects empty email', () => {
    const result = validateEmail('')
    expect(result.isValid).toBe(false)
    expect(result.error).toContain('required')
  })

  it('rejects invalid email format', () => {
    const result = validateEmail('notanemail')
    expect(result.isValid).toBe(false)
    expect(result.error).toContain('valid email')
  })

  it('accepts valid email', () => {
    const result = validateEmail('test@example.com')
    expect(result.isValid).toBe(true)
  })
})

describe('calculatePasswordStrength (legacy mode)', () => {
  it('returns low score for weak password', () => {
    const result = calculatePasswordStrength('password')
    expect(result.score).toBeLessThan(3)
    expect(result.requirements.minLength).toBe(false)
  })

  it('returns high score for strong password', () => {
    const result = calculatePasswordStrength('MySecure123!Pass')
    expect(result.score).toBe(5)
    expect(result.requirements.minLength).toBe(true)
    expect(result.requirements.hasUppercase).toBe(true)
    expect(result.requirements.hasLowercase).toBe(true)
    expect(result.requirements.hasNumber).toBe(true)
    expect(result.requirements.hasSpecialChar).toBe(true)
  })

  it('detects missing uppercase', () => {
    const result = calculatePasswordStrength('mysecure123!pass')
    expect(result.requirements.hasUppercase).toBe(false)
  })

  it('detects missing number', () => {
    const result = calculatePasswordStrength('MySecurePass!')
    expect(result.requirements.hasNumber).toBe(false)
  })

  it('detects missing special character', () => {
    const result = calculatePasswordStrength('MySecure123Pass')
    expect(result.requirements.hasSpecialChar).toBe(false)
  })
})

describe('validatePassword', () => {
  it('rejects password without uppercase', () => {
    const result = validatePassword('mysecure123!pass')
    expect(result.isValid).toBe(false)
  })

  it('rejects password without number', () => {
    const result = validatePassword('MySecurePass!abc')
    expect(result.isValid).toBe(false)
  })

  it('rejects password without special character', () => {
    const result = validatePassword('MySecure123Pass')
    expect(result.isValid).toBe(false)
  })

  it('accepts password meeting all complexity requirements', () => {
    const result = validatePassword('MySecure123!Pass')
    expect(result.isValid).toBe(true)
  })
})
