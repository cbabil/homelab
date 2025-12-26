/**
 * Registration Form Component
 * 
 * Complete registration form with all fields, validation feedback,
 * and security features. Follows LoginPage UI patterns.
 */

import { Link } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { BasicFormFields } from './BasicFormFields'
import { PasswordFields } from './PasswordFields'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

interface RegistrationFormProps {
  formState: RegistrationFormState
  formHandlers: FormHandlers
  showPassword: boolean
  showConfirmPassword: boolean
  onTogglePassword: () => void
  onToggleConfirmPassword: () => void
  error?: string | null
}

export function RegistrationForm({
  formState,
  formHandlers,
  showPassword,
  showConfirmPassword,
  onTogglePassword,
  onToggleConfirmPassword,
  error
}: RegistrationFormProps) {
  return (
    <div className="bg-card/50 backdrop-blur border border-border/50 rounded-2xl p-6 shadow-xl">
      <form onSubmit={formHandlers.handleSubmit} className="space-y-4">
        {/* Global Error Message */}
        {(formState.submitError || error) && (
          <div className="form-feedback form-feedback-error">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{formState.submitError || error}</span>
            </div>
          </div>
        )}

        {/* Basic Form Fields */}
        <BasicFormFields
          formState={formState}
          formHandlers={formHandlers}
        />

        {/* Password Fields */}
        <PasswordFields
          formState={formState}
          formHandlers={formHandlers}
          showPassword={showPassword}
          showConfirmPassword={showConfirmPassword}
          onTogglePassword={onTogglePassword}
          onToggleConfirmPassword={onToggleConfirmPassword}
        />

        {/* Footer */}
        <div className="text-center mt-6">
          <Link 
            to="/login" 
            className="text-sm text-primary hover:text-primary/80 transition-colors"
          >
            Already have an account? Sign in
          </Link>
        </div>
      </form>
    </div>
  )
}