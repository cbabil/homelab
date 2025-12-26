/**
 * Terms Acceptance Checkbox Component
 * 
 * Terms of service and privacy policy acceptance checkbox
 * for registration form with modal popups.
 */


interface TermsCheckboxProps {
  checked: boolean
  error?: string
  isSubmitting: boolean
  onChange: (accepted: boolean) => void
}

export function TermsCheckbox({
  checked,
  error,
  isSubmitting,
  onChange
}: TermsCheckboxProps) {
  
  const openTermsPopup = () => {
    window.open('/terms-of-service', 'termsPopup', 'width=600,height=800,scrollbars=yes,resizable=yes')
  }

  const openPrivacyPopup = () => {
    window.open('/privacy-policy', 'privacyPopup', 'width=600,height=800,scrollbars=yes,resizable=yes')
  }

  return (
    <>
      <div className="flex items-start gap-3">
        <input
          id="reg-accept-terms"
          type="checkbox"
          className="checkbox-input mt-0.5"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={isSubmitting}
        />
        <label htmlFor="reg-accept-terms" className="text-sm text-foreground cursor-pointer">
          I accept the{' '}
          <button
            type="button"
            onClick={openTermsPopup}
            className="text-primary hover:text-primary/80 underline"
            disabled={isSubmitting}
          >
            Terms of Service
          </button>{' '}
          and{' '}
          <button
            type="button"
            onClick={openPrivacyPopup}
            className="text-primary hover:text-primary/80 underline"
            disabled={isSubmitting}
          >
            Privacy Policy
          </button>
        </label>
      </div>
      {error && (
        <div className="form-error-message -mt-2">
          {error}
        </div>
      )}
    </>
  )
}