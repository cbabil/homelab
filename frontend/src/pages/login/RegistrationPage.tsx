/**
 * Registration Page Component
 * 
 * User registration page with comprehensive form validation, password strength,
 * and security features. Follows LoginPage patterns for consistency.
 */

import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { useAuth } from '@/providers/AuthProvider'
import { RegistrationFormState } from '@/types/auth'
import { RegistrationForm } from '@/components/auth/RegistrationForm'
import { createFormHandlers } from '@/utils/registrationFormHandlers'

export function RegistrationPage() {
  const { register, isAuthenticated, error } = useAuth()
  const location = useLocation()
  
  // Redirect to intended destination after registration
  const from = (location.state as any)?.from?.pathname || '/'

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formState, setFormState] = useState<RegistrationFormState>({
    username: {
      value: '',
      error: '',
      isValid: false
    },
    email: {
      value: '',
      error: '',
      isValid: false
    },
    password: {
      value: '',
      error: '',
      isValid: false,
      strength: undefined
    },
    confirmPassword: {
      value: '',
      error: '',
      isValid: false
    },
    acceptTerms: {
      value: false,
      error: '',
      isValid: false
    },
    isSubmitting: false,
    submitError: ''
  })

  // If already authenticated, redirect to intended destination
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  // Create form handlers using utility
  const formHandlers = createFormHandlers(formState, setFormState, register)

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Create Account
          </h1>
          <p className="text-muted-foreground">
            Join your Homelab Assistant
          </p>
        </div>
        
        {/* Registration Form */}
        <RegistrationForm
          formState={formState}
          formHandlers={formHandlers}
          showPassword={showPassword}
          showConfirmPassword={showConfirmPassword}
          onTogglePassword={() => setShowPassword(!showPassword)}
          onToggleConfirmPassword={() => setShowConfirmPassword(!showConfirmPassword)}
          error={error}
        />
      </div>
    </div>
  )
}