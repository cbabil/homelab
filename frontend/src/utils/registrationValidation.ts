/**
 * Registration Validation Utilities
 *
 * Comprehensive validation functions for user registration,
 * following security best practices and addressing OWASP requirements.
 */

import { DEFAULT_REGISTRATION_VALIDATION, PasswordStrength } from '@/types/auth'

export interface ValidationResult {
  isValid: boolean
  error?: string
}

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
 * Calculate password strength for registration
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
 * Validate password with strength requirements (legacy mode)
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

  // All complexity requirements must be met
  if (strength.score < 5) {
    return {
      isValid: false,
      error: 'Password must meet all requirements',
      strength
    }
  }

  return { isValid: true, strength }
}