/**
 * Login Form Validation Utilities
 * 
 * Extracted from LoginPage to maintain 100-line limit per CLAUDE.md rules.
 * Handles validation logic for login form fields.
 */

import { DEFAULT_LOGIN_VALIDATION } from '@/types/auth'

export interface ValidationResult {
  isValid: boolean
  error?: string
}

/**
 * Validate username field
 */
export function validateUsername(value: string): ValidationResult {
  const rules = DEFAULT_LOGIN_VALIDATION.username
  
  if (rules.required && !value.trim()) {
    return { isValid: false, error: 'Username is required' }
  }
  
  if (rules.minLength && value.length < rules.minLength) {
    return { 
      isValid: false, 
      error: `Username must be at least ${rules.minLength} characters` 
    }
  }
  
  if (rules.pattern && !rules.pattern.test(value)) {
    return { isValid: false, error: 'Invalid username format' }
  }
  
  return { isValid: true }
}

/**
 * Validate password field (simplified for login - only check if not empty)
 */
export function validatePassword(value: string): ValidationResult {
  const rules = DEFAULT_LOGIN_VALIDATION.password
  
  if (rules.required && !value.trim()) {
    return { isValid: false, error: 'Password is required' }
  }
  
  return { isValid: true }
}

/**
 * Validate login form field by type
 */
export function validateLoginField(
  field: 'username' | 'password', 
  value: string
): ValidationResult {
  switch (field) {
    case 'username':
      return validateUsername(value)
    case 'password':
      return validatePassword(value)
    default:
      return { isValid: false, error: 'Unknown field type' }
  }
}

/**
 * Validate entire login form
 */
export function validateLoginForm(formData: {
  username: string
  password: string
}): {
  isValid: boolean
  errors: {
    username?: string
    password?: string
  }
} {
  const usernameValidation = validateUsername(formData.username)
  const passwordValidation = validatePassword(formData.password)
  
  return {
    isValid: usernameValidation.isValid && passwordValidation.isValid,
    errors: {
      ...(usernameValidation.error && { username: usernameValidation.error }),
      ...(passwordValidation.error && { password: passwordValidation.error })
    }
  }
}