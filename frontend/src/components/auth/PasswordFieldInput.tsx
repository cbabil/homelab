/**
 * Single Password Input Component
 * 
 * Reusable password input with toggle visibility functionality.
 */

import { Eye, EyeOff, Lock } from 'lucide-react'
import { cn } from '@/utils/cn'

interface PasswordFieldInputProps {
  id: string
  label: string
  value: string
  placeholder: string
  showPassword: boolean
  error?: string
  isValid: boolean
  isSubmitting: boolean
  autoComplete: string
  onChange: (value: string) => void
  onToggleVisibility: () => void
}

export function PasswordFieldInput({
  id,
  label,
  value,
  placeholder,
  showPassword,
  error,
  isValid,
  isSubmitting,
  autoComplete,
  onChange,
  onToggleVisibility
}: PasswordFieldInputProps) {
  return (
    <div className="form-group">
      <label htmlFor={id} className="form-label">
        {label}
      </label>
      <div className="input-password-wrapper">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className="h-4 w-4 text-muted-foreground" />
          </div>
          <input
            id={id}
            type={showPassword ? 'text' : 'password'}
            autoComplete={autoComplete}
            required
            className={cn(
              'input-base input-password pl-10',
              error && 'input-error',
              isValid && value && 'form-field-valid'
            )}
            placeholder={placeholder}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={isSubmitting}
          />
          <button
            type="button"
            className="input-password-toggle"
            onClick={onToggleVisibility}
            disabled={isSubmitting}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Eye className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>
      {error && (
        <div className="form-error-message">
          {error}
        </div>
      )}
    </div>
  )
}