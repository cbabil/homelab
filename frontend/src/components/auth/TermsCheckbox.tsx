/**
 * Terms Acceptance Checkbox Component
 *
 * Terms of service and privacy policy acceptance checkbox
 * for registration form with modal popups.
 */

import FormControl from '@mui/material/FormControl'
import FormControlLabel from '@mui/material/FormControlLabel'
import Checkbox from '@mui/material/Checkbox'
import FormHelperText from '@mui/material/FormHelperText'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'

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
    <FormControl error={!!error} sx={{ width: '100%' }}>
      <FormControlLabel
        control={
          <Checkbox
            id="reg-accept-terms"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            disabled={isSubmitting}
          />
        }
        label={
          <Typography variant="body2" component="span">
            I accept the{' '}
            <Button
              type="button"
              onClick={openTermsPopup}
              disabled={isSubmitting}
              sx={{
                p: 0,
                minWidth: 'auto',
                textDecoration: 'underline',
                verticalAlign: 'baseline',
                fontSize: 'inherit',
                textTransform: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                  bgcolor: 'transparent',
                },
              }}
            >
              Terms of Service
            </Button>{' '}
            and{' '}
            <Button
              type="button"
              onClick={openPrivacyPopup}
              disabled={isSubmitting}
              sx={{
                p: 0,
                minWidth: 'auto',
                textDecoration: 'underline',
                verticalAlign: 'baseline',
                fontSize: 'inherit',
                textTransform: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                  bgcolor: 'transparent',
                },
              }}
            >
              Privacy Policy
            </Button>
          </Typography>
        }
        sx={{
          alignItems: 'flex-start',
          ml: 0,
          mr: 0,
        }}
      />
      {error && (
        <FormHelperText sx={{ mt: 0 }}>{error}</FormHelperText>
      )}
    </FormControl>
  )
}