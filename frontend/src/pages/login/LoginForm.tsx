/**
 * Login Form Component (Simplified)
 *
 * Simplified login form using MUI components and custom hook for state management.
 */

import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import FormControlLabel from '@mui/material/FormControlLabel'
import Checkbox from '@mui/material/Checkbox'
import CheckBoxOutlineBlankOutlinedIcon from '@mui/icons-material/CheckBoxOutlineBlankOutlined'
import CheckBoxOutlinedIcon from '@mui/icons-material/CheckBoxOutlined'
import Link from '@mui/material/Link'
import { Button } from '@/components/ui/Button'
import { useLoginForm } from './useLoginForm'
import { LoginFormFields } from './LoginFormFields'
import { LoginFormMessages } from './LoginFormMessages'

export function LoginForm() {
  const { t } = useTranslation()
  const {
    formState,
    showPassword,
    isFormValid,
    handleInputChange,
    handleRememberMeChange,
    handleSubmit,
    togglePassword
  } = useLoginForm()

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      <LoginFormMessages
        submitError={formState.submitError}
      />

      <LoginFormFields
        formState={formState}
        showPassword={showPassword}
        onInputChange={handleInputChange}
        onTogglePassword={togglePassword}
      />

      {/* Remember Me & Forgot Password */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={formState.rememberMe}
              onChange={(e) => handleRememberMeChange(e.target.checked)}
              size="small"
              icon={<CheckBoxOutlineBlankOutlinedIcon />}
              checkedIcon={<CheckBoxOutlinedIcon />}
            />
          }
          label={t('auth.rememberMe')}
          sx={{
            '& .MuiFormControlLabel-label': { fontSize: '0.875rem' },
            cursor: 'pointer'
          }}
        />

        <Link
          component={RouterLink}
          to="/forgot-password"
          variant="body2"
          underline="none"
          sx={{ cursor: 'pointer' }}
        >
          {t('auth.forgotPassword')}
        </Link>
      </Box>

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        disabled={!isFormValid || formState.isSubmitting}
        loading={formState.isSubmitting}
        sx={{ mt: 1 }}
      >
        {t('auth.signIn')}
      </Button>
    </Box>
  )
}