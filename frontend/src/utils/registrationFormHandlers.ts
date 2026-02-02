/**
 * Registration Form Handlers
 *
 * Form handling utilities for registration page,
 * following security best practices and validation patterns.
 */

import React from 'react'
import { RegistrationFormState, RegistrationCredentials } from '@/types/auth'
import {
  validateUsername,
  validateEmail,
  validatePassword
} from './registrationValidation'

export type FormField = 'username' | 'email' | 'password' | 'confirmPassword'

export interface FormHandlers {
  handleInputChange: (field: FormField, value: string) => void
  handleTermsChange: (accepted: boolean) => void
  handleSubmit: (e: React.FormEvent) => Promise<void>
  isFormValid: boolean
}

/**
 * Create form handlers for registration page
 */
export const createFormHandlers = (
  formState: RegistrationFormState,
  setFormState: React.Dispatch<React.SetStateAction<RegistrationFormState>>,
  register: (credentials: RegistrationCredentials) => Promise<void>
): FormHandlers => {

  // Handle form field changes with validation
  const handleInputChange = (field: FormField, value: string) => {
    let validation: ReturnType<typeof validateUsername> | ReturnType<typeof validateEmail> | ReturnType<typeof validatePassword> = { isValid: true }

    switch (field) {
      case 'username':
        validation = validateUsername(value)
        break
      case 'email':
        validation = validateEmail(value)
        break
      case 'password':
        validation = validatePassword(value)
        break
      case 'confirmPassword': {
        const confirmValidation = formState.password.value === value
          ? { isValid: true }
          : { isValid: false, error: 'Passwords do not match' }
        validation = confirmValidation
        break
      }
    }

    setFormState(prev => ({
      ...prev,
      [field]: {
        value,
        error: validation.error || '',
        isValid: validation.isValid,
        ...(field === 'password' && 'strength' in validation && validation.strength ? { strength: validation.strength } : {})
      },
      submitError: '' // Clear submit error when user types
    }))
  }

  // Handle terms acceptance
  const handleTermsChange = (accepted: boolean) => {
    setFormState(prev => ({
      ...prev,
      acceptTerms: {
        value: accepted,
        error: accepted ? '' : 'You must accept the terms of service',
        isValid: accepted
      },
      submitError: ''
    }))
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Final validation
    const usernameValidation = validateUsername(formState.username.value)
    const emailValidation = validateEmail(formState.email.value)
    const passwordValidation = validatePassword(formState.password.value)
    const confirmValidation = formState.password.value === formState.confirmPassword.value
    const termsValidation = formState.acceptTerms.value

    if (!usernameValidation.isValid || !emailValidation.isValid || !passwordValidation.isValid ||
        !confirmValidation || !termsValidation) {

      setFormState(prev => ({
        ...prev,
        username: { ...prev.username, error: usernameValidation.error || '', isValid: usernameValidation.isValid },
        email: { ...prev.email, error: emailValidation.error || '', isValid: emailValidation.isValid },
        password: {
          ...prev.password,
          error: passwordValidation.error || '',
          isValid: passwordValidation.isValid,
          strength: passwordValidation.strength
        },
        confirmPassword: {
          ...prev.confirmPassword,
          error: confirmValidation ? '' : 'Passwords do not match',
          isValid: confirmValidation
        },
        acceptTerms: {
          ...prev.acceptTerms,
          error: termsValidation ? '' : 'You must accept the terms of service',
          isValid: termsValidation
        }
      }))
      return
    }

    setFormState(prev => ({ ...prev, isSubmitting: true, submitError: '' }))

    try {
      const credentials: RegistrationCredentials = {
        username: formState.username.value.trim(),
        email: formState.email.value.trim(),
        password: formState.password.value,
        confirmPassword: formState.confirmPassword.value,
        acceptTerms: formState.acceptTerms.value
      }

      await register(credentials)
    } catch (_err) {
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        submitError: 'Registration failed. Please try again.'
      }))
    }
  }

  // Check if form is valid
  const isFormValid = formState.username.isValid &&
    formState.email.isValid &&
    formState.password.isValid &&
    formState.confirmPassword.isValid &&
    formState.acceptTerms.isValid

  return {
    handleInputChange,
    handleTermsChange,
    handleSubmit,
    isFormValid
  }
}