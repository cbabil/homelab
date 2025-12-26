/**
 * Login Form Hook
 * 
 * Custom hook for managing login form state and submission.
 * Extracted to maintain 100-line limit per CLAUDE.md rules.
 */

import { useState } from 'react'
import { useAuth } from '@/providers/AuthProvider'
import { LoginCredentials, LoginFormState } from '@/types/auth'
import { validateLoginField } from './loginValidation'

export function useLoginForm() {
  const { login, error } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [formState, setFormState] = useState<LoginFormState>({
    username: { value: '', error: '', isValid: false },
    password: { value: '', error: '', isValid: false },
    rememberMe: false,
    isSubmitting: false,
    submitError: ''
  })

  // Handle form field changes
  const handleInputChange = (field: 'username' | 'password', value: string) => {
    const validation = validateLoginField(field, value)

    setFormState(prev => ({
      ...prev,
      [field]: {
        value,
        error: validation.error || '',
        isValid: validation.isValid
      },
      submitError: '' // Clear submit error when user types
    }))
  }

  // Handle remember me toggle
  const handleRememberMeChange = (checked: boolean) => {
    setFormState(prev => ({ ...prev, rememberMe: checked }))
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Final validation
    const usernameValidation = validateLoginField('username', formState.username.value)
    const passwordValidation = validateLoginField('password', formState.password.value)
    
    if (!usernameValidation.isValid || !passwordValidation.isValid) {
      setFormState(prev => ({
        ...prev,
        username: {
          ...prev.username,
          error: usernameValidation.error || '',
          isValid: usernameValidation.isValid
        },
        password: {
          ...prev.password,
          error: passwordValidation.error || '',
          isValid: passwordValidation.isValid
        }
      }))
      return
    }

    setFormState(prev => ({ ...prev, isSubmitting: true, submitError: '' }))

    try {
      const credentials: LoginCredentials = {
        username: formState.username.value.trim(),
        password: formState.password.value,
        rememberMe: formState.rememberMe
      }

      await login(credentials)
      setFormState(prev => ({ ...prev, isSubmitting: false, submitError: '' }))
    } catch (err) {
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        submitError: 'Invalid username or password'
      }))
    }
  }

  const isFormValid = formState.username.isValid && formState.password.isValid

  return {
    formState,
    showPassword,
    error,
    isFormValid,
    handleInputChange,
    handleRememberMeChange,
    handleSubmit,
    togglePassword: () => setShowPassword(!showPassword)
  }
}