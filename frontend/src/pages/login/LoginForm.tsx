/**
 * Login Form Component (Simplified)
 * 
 * Simplified login form using custom hook for state management.
 * Maintains 100-line limit per CLAUDE.md rules.
 */

import React from 'react'
import { Button } from '@/components/ui/Button'
import { useLoginForm } from './useLoginForm'
import { LoginFormFields } from './LoginFormFields'
import { LoginFormMessages } from './LoginFormMessages'

interface LoginFormProps {
  onSuccess?: () => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const {
    formState,
    showPassword,
    error,
    isFormValid,
    handleInputChange,
    handleRememberMeChange,
    handleSubmit,
    togglePassword
  } = useLoginForm()

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <LoginFormMessages
        submitError={formState.submitError}
        authError={error}
      />

      <LoginFormFields
        formState={formState}
        showPassword={showPassword}
        onInputChange={handleInputChange}
        onTogglePassword={togglePassword}
      />

      {/* Remember Me - handled separately since it needs state update */}
      <div className="flex items-center justify-between">
        <label className="checkbox-item">
          <input
            type="checkbox"
            className="checkbox-input"
            checked={formState.rememberMe}
            onChange={(e) => handleRememberMeChange(e.target.checked)}
            disabled={formState.isSubmitting}
          />
          <span className="checkbox-label">Remember me</span>
        </label>
        
        <button
          type="button"
          className="text-sm text-primary hover:text-primary/80 transition-colors"
          disabled={formState.isSubmitting}
        >
          Forgot password?
        </button>
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={formState.isSubmitting}
        disabled={!isFormValid || formState.isSubmitting}
      >
        {formState.isSubmitting ? 'Signing in...' : 'Sign In'}
      </Button>
    </form>
  )
}