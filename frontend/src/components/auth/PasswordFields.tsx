/**
 * Password Fields Component
 * 
 * Password and confirm password fields with strength indicator
 * for registration form.
 */

import { Button } from '@/components/ui/Button'
import { PasswordStrengthIndicator } from './PasswordStrengthIndicator'
import { PasswordFieldInput } from './PasswordFieldInput'
import { TermsCheckbox } from './TermsCheckbox'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

interface PasswordFieldsProps {
  formState: RegistrationFormState
  formHandlers: FormHandlers
  showPassword: boolean
  showConfirmPassword: boolean
  onTogglePassword: () => void
  onToggleConfirmPassword: () => void
}

export function PasswordFields({
  formState,
  formHandlers,
  showPassword,
  showConfirmPassword,
  onTogglePassword,
  onToggleConfirmPassword
}: PasswordFieldsProps) {
  return (
    <>
      {/* Password Field */}
      <PasswordFieldInput
        id="reg-password"
        label="Password"
        value={formState.password.value}
        placeholder="Create password"
        showPassword={showPassword}
        error={formState.password.error}
        isValid={formState.password.isValid}
        isSubmitting={formState.isSubmitting}
        autoComplete="new-password"
        onChange={(value) => formHandlers.handleInputChange('password', value)}
        onToggleVisibility={onTogglePassword}
      />

      {formState.password.strength && (
        <div className="-mt-2 mb-4">
          <PasswordStrengthIndicator 
            strength={formState.password.strength} 
            password={formState.password.value} 
          />
        </div>
      )}

      {/* Confirm Password Field */}
      <PasswordFieldInput
        id="reg-confirm-password"
        label="Confirm Password"
        value={formState.confirmPassword.value}
        placeholder="Confirm password"
        showPassword={showConfirmPassword}
        error={formState.confirmPassword.error}
        isValid={formState.confirmPassword.isValid}
        isSubmitting={formState.isSubmitting}
        autoComplete="new-password"
        onChange={(value) => formHandlers.handleInputChange('confirmPassword', value)}
        onToggleVisibility={onToggleConfirmPassword}
      />

      {/* Terms Acceptance */}
      <TermsCheckbox
        checked={formState.acceptTerms.value}
        error={formState.acceptTerms.error}
        isSubmitting={formState.isSubmitting}
        onChange={formHandlers.handleTermsChange}
      />

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={formState.isSubmitting}
        disabled={!formHandlers.isFormValid || formState.isSubmitting}
      >
        {formState.isSubmitting ? 'Creating Account...' : 'Create Account'}
      </Button>
    </>
  )
}