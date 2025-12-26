/**
 * Basic Form Fields Component
 * 
 * Username and email fields for registration form.
 */

import { User, Mail } from 'lucide-react'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'
import { cn } from '@/utils/cn'

interface BasicFormFieldsProps {
  formState: RegistrationFormState
  formHandlers: FormHandlers
}

export function BasicFormFields({
  formState,
  formHandlers
}: BasicFormFieldsProps) {
  return (
    <>
      {/* Username Field */}
      <div className="form-group">
        <label htmlFor="reg-username" className="form-label">Username</label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <User className="h-4 w-4 text-muted-foreground" />
          </div>
          <input
            id="reg-username"
            type="text"
            autoComplete="username"
            required
            className={cn(
              'input-base pl-10',
              formState.username.error && 'input-error',
              formState.username.isValid && formState.username.value && 'form-field-valid'
            )}
            placeholder="Enter username"
            value={formState.username.value}
            onChange={(e) => formHandlers.handleInputChange('username', e.target.value)}
            disabled={formState.isSubmitting}
          />
        </div>
        {formState.username.error && (
          <div className="form-error-message">{formState.username.error}</div>
        )}
      </div>

      {/* Email Field */}
      <div className="form-group">
        <label htmlFor="reg-email" className="form-label">Email</label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail className="h-4 w-4 text-muted-foreground" />
          </div>
          <input
            id="reg-email"
            type="email"
            autoComplete="email"
            required
            className={cn(
              'input-base pl-10',
              formState.email.error && 'input-error',
              formState.email.isValid && formState.email.value && 'form-field-valid'
            )}
            placeholder="Enter email address"
            value={formState.email.value}
            onChange={(e) => formHandlers.handleInputChange('email', e.target.value)}
            disabled={formState.isSubmitting}
          />
        </div>
        {formState.email.error && (
          <div className="form-error-message">{formState.email.error}</div>
        )}
      </div>
    </>
  )
}