/**
 * Login Form Fields Component
 * 
 * Individual form fields for the login form.
 * Extracted to maintain 100-line limit per CLAUDE.md rules.
 */

import React from 'react'
import { Eye, EyeOff, Lock, User } from 'lucide-react'
import { LoginFormState } from '@/types/auth'
import { cn } from '@/utils/cn'

interface LoginFormFieldsProps {
  formState: LoginFormState
  showPassword: boolean
  onInputChange: (field: 'username' | 'password', value: string) => void
  onTogglePassword: () => void
}

export function LoginFormFields({
  formState,
  showPassword,
  onInputChange,
  onTogglePassword
}: LoginFormFieldsProps) {
  return (
    <>
      {/* Username Field */}
      <div className="form-group">
        <label htmlFor="username" className="form-label">Username</label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <User className="h-4 w-4 text-muted-foreground" />
          </div>
          <input
            id="username"
            type="text"
            autoComplete="username"
            required
            className={cn(
              'input-base pl-10',
              formState.username.error && 'input-error',
              formState.username.isValid && formState.username.value && 'form-field-valid'
            )}
            placeholder="Enter your username"
            value={formState.username.value}
            onChange={(e) => onInputChange('username', e.target.value)}
            disabled={formState.isSubmitting}
          />
        </div>
        {formState.username.error && (
          <div className="form-error-message">{formState.username.error}</div>
        )}
      </div>

      {/* Password Field */}
      <div className="form-group">
        <label htmlFor="password" className="form-label">Password</label>
        <div className="input-password-wrapper">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              className={cn(
                'input-base input-password pl-10',
                formState.password.error && 'input-error',
                formState.password.isValid && formState.password.value && 'form-field-valid'
              )}
              placeholder="Enter your password"
              value={formState.password.value}
              onChange={(e) => onInputChange('password', e.target.value)}
              disabled={formState.isSubmitting}
            />
            <button
              type="button"
              className="input-password-toggle"
              onClick={onTogglePassword}
              disabled={formState.isSubmitting}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4 text-muted-foreground" />
              ) : (
                <Eye className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </div>
        </div>
        {formState.password.error && (
          <div className="form-error-message">{formState.password.error}</div>
        )}
      </div>

    </>
  )
}