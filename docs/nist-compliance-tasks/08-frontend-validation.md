# Task 08: Update Frontend Validation

## Overview

Update the frontend password validation utilities to support NIST SP 800-63B-4 compliance mode.

## File to Modify

`frontend/src/utils/registrationValidation.ts`

## Requirements

1. Add NIST password strength calculation
2. Add pattern detection functions
3. Add basic client-side blocklist check
4. Keep legacy validation for backward compatibility

## New Implementation

```typescript
/**
 * Registration Validation Utilities
 *
 * Comprehensive validation functions for user registration,
 * following security best practices and NIST SP 800-63B-4 guidelines.
 */

import { DEFAULT_REGISTRATION_VALIDATION, PasswordStrength, NISTPasswordStrength } from '@/types/auth'

export interface ValidationResult {
  isValid: boolean
  error?: string
}

// ============================================================================
// NIST Mode Validation Functions
// ============================================================================

/** Common passwords for client-side quick check (subset of backend list) */
const COMMON_PASSWORDS_SUBSET = new Set([
  'password', 'password1', 'password123', '123456', '12345678', '123456789',
  'qwerty', 'abc123', 'monkey', 'letmein', 'dragon', 'baseball', 'iloveyou',
  'trustno1', 'sunshine', 'master', 'welcome', 'shadow', 'ashley', 'football',
  'jesus', 'michael', 'ninja', 'mustang', 'qazwsx', 'admin', 'administrator'
])

/**
 * Check for sequential character patterns
 */
export const hasSequentialPattern = (password: string): boolean => {
  const sequences = [
    '0123456789',
    '9876543210',
    'abcdefghijklmnopqrstuvwxyz',
    'zyxwvutsrqponmlkjihgfedcba',
    'qwertyuiop',
    'asdfghjkl',
    'zxcvbnm'
  ]

  const lower = password.toLowerCase()
  for (const seq of sequences) {
    for (let i = 0; i <= seq.length - 4; i++) {
      if (lower.includes(seq.substring(i, i + 4))) {
        return true
      }
    }
  }
  return false
}

/**
 * Check for repetitive character patterns
 */
export const hasRepetitivePattern = (password: string): boolean => {
  return /(.)\1{3,}/.test(password)
}

/**
 * Basic client-side blocklist check (quick check before server validation)
 */
export const checkBasicBlocklist = (
  password: string,
  username: string = ''
): { isBlocked: boolean; reason?: string } => {
  const lower = password.toLowerCase()

  // Check common passwords
  if (COMMON_PASSWORDS_SUBSET.has(lower)) {
    return { isBlocked: true, reason: 'Password is too common' }
  }

  // Check if password contains username
  if (username && username.length >= 3 && lower.includes(username.toLowerCase())) {
    return { isBlocked: true, reason: 'Password contains your username' }
  }

  // Check context-specific words
  const contextWords = ['tomo', 'admin', 'administrator', 'password']
  for (const word of contextWords) {
    if (lower.includes(word)) {
      return { isBlocked: true, reason: `Password contains common word: ${word}` }
    }
  }

  return { isBlocked: false }
}

/**
 * Calculate NIST-compliant password strength
 */
export const calculateNISTPasswordStrength = (
  password: string,
  username: string = '',
  minLength: number = 15
): NISTPasswordStrength => {
  const feedback: string[] = []
  let isValid = true

  // Length check (NIST: 15 minimum for password-only auth)
  if (password.length < minLength) {
    feedback.push(`Password must be at least ${minLength} characters`)
    isValid = false
  }

  // Sequential pattern check
  if (hasSequentialPattern(password)) {
    feedback.push('Avoid sequential characters (1234, abcd)')
    isValid = false
  }

  // Repetitive pattern check
  if (hasRepetitivePattern(password)) {
    feedback.push('Avoid repetitive characters (aaaa)')
    isValid = false
  }

  // Basic blocklist check
  const blocklist = checkBasicBlocklist(password, username)
  if (blocklist.isBlocked) {
    feedback.push(blocklist.reason || 'Password is too common')
    isValid = false
  }

  // Score based on length (NIST encourages longer passwords)
  let score: number
  if (password.length < minLength) {
    score = 1
  } else if (password.length < 20) {
    score = 2
  } else if (password.length < 25) {
    score = 3
  } else if (password.length < 30) {
    score = 4
  } else {
    score = 5
  }

  return {
    score,
    isValid,
    feedback,
    blocklist
  }
}

/**
 * Validate password with NIST rules
 */
export const validatePasswordNIST = (
  value: string,
  username: string = '',
  minLength: number = 15,
  maxLength: number = 128
): ValidationResult & { strength: NISTPasswordStrength } => {
  const strength = calculateNISTPasswordStrength(value, username, minLength)

  if (!value.trim()) {
    return {
      isValid: false,
      error: 'Password is required',
      strength
    }
  }

  if (value.length > maxLength) {
    return {
      isValid: false,
      error: `Password must be less than ${maxLength} characters`,
      strength
    }
  }

  if (!strength.isValid) {
    return {
      isValid: false,
      error: strength.feedback[0] || 'Password does not meet requirements',
      strength
    }
  }

  return { isValid: true, strength }
}

// ============================================================================
// Legacy Mode Validation Functions (unchanged)
// ============================================================================

/**
 * Validate username field with comprehensive checks
 */
export const validateUsername = (value: string): ValidationResult => {
  const rules = DEFAULT_REGISTRATION_VALIDATION.username

  if (rules.required && !value.trim()) {
    return { isValid: false, error: 'Username is required' }
  }

  if (value.length < rules.minLength) {
    return {
      isValid: false,
      error: `Username must be at least ${rules.minLength} characters`
    }
  }

  if (value.length > rules.maxLength) {
    return {
      isValid: false,
      error: `Username must be less than ${rules.maxLength} characters`
    }
  }

  if (rules.pattern && !rules.pattern.test(value)) {
    return {
      isValid: false,
      error: 'Username can only contain letters, numbers, hyphens, and underscores'
    }
  }

  return { isValid: true }
}

/**
 * Validate email field with security considerations
 */
export const validateEmail = (value: string): ValidationResult => {
  const rules = DEFAULT_REGISTRATION_VALIDATION.email

  if (rules.required && !value.trim()) {
    return { isValid: false, error: 'Email is required' }
  }

  const sanitized = value.trim().toLowerCase()

  if (sanitized.length > rules.maxLength) {
    return {
      isValid: false,
      error: `Email must be less than ${rules.maxLength} characters`
    }
  }

  if (!rules.pattern.test(sanitized)) {
    return { isValid: false, error: 'Please enter a valid email address' }
  }

  return { isValid: true }
}

/**
 * Calculate password strength for registration (Legacy mode)
 */
export const calculatePasswordStrength = (password: string): PasswordStrength => {
  const requirements = {
    minLength: password.length >= 12,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecialChar: /[!@#$%^&*(),.?"':{}|<>]/.test(password)
  }

  const score = Object.values(requirements).filter(Boolean).length

  const feedback: string[] = []
  if (!requirements.minLength) feedback.push('At least 12 characters')
  if (!requirements.hasUppercase) feedback.push('One uppercase letter')
  if (!requirements.hasLowercase) feedback.push('One lowercase letter')
  if (!requirements.hasNumber) feedback.push('One number')
  if (!requirements.hasSpecialChar) feedback.push('One special character')

  return {
    score,
    requirements,
    feedback
  }
}

/**
 * Validate password with strength requirements (Legacy mode)
 */
export const validatePassword = (value: string): ValidationResult & { strength: PasswordStrength } => {
  const rules = DEFAULT_REGISTRATION_VALIDATION.password
  const strength = calculatePasswordStrength(value)

  if (rules.required && !value.trim()) {
    return {
      isValid: false,
      error: 'Password is required',
      strength
    }
  }

  if (value.length < rules.minLength) {
    return {
      isValid: false,
      error: `Password must be at least ${rules.minLength} characters`,
      strength
    }
  }

  if (value.length > rules.maxLength) {
    return {
      isValid: false,
      error: `Password must be less than ${rules.maxLength} characters`,
      strength
    }
  }

  // All complexity requirements must be met (legacy mode)
  if (strength.score < 5) {
    return {
      isValid: false,
      error: 'Password must meet all requirements',
      strength
    }
  }

  return { isValid: true, strength }
}
```

## Update Types

Add to `frontend/src/types/auth.ts`:

```typescript
export interface NISTPasswordStrength {
  /** Score from 1-5 based on length */
  score: number
  /** Whether password is valid per NIST rules */
  isValid: boolean
  /** Feedback messages */
  feedback: string[]
  /** Blocklist check result */
  blocklist?: {
    isBlocked: boolean
    reason?: string
  }
}
```

## Usage in Registration Form

```typescript
// In registration form handler
const validatePasswordField = (value: string, username: string, nistMode: boolean) => {
  if (nistMode) {
    return validatePasswordNIST(value, username, 15, 128)
  } else {
    return validatePassword(value)
  }
}
```

## Dependencies

- Task 07: Password strength indicator types

## Acceptance Criteria

- [ ] `calculateNISTPasswordStrength()` function exists
- [ ] `validatePasswordNIST()` function exists
- [ ] Sequential pattern detection works (4+ char sequences)
- [ ] Repetitive pattern detection works (4+ same char)
- [ ] Basic blocklist check includes common passwords
- [ ] Username-in-password check works
- [ ] Legacy functions unchanged
- [ ] All new functions are exported
