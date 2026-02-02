/**
 * Registration Form Component
 *
 * Complete registration form with all fields, validation feedback,
 * and security features. Follows LoginPage UI patterns.
 */

import { Link as RouterLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Alert from '@mui/material/Alert'
import Typography from '@mui/material/Typography'
import Link from '@mui/material/Link'
import { ErrorOutline } from '@mui/icons-material'
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
  const { t } = useTranslation()

  return (
    <Card
      elevation={8}
      sx={{
        borderRadius: 3,
        bgcolor: 'background.paper',
        backdropFilter: 'blur(10px)',
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box component="form" onSubmit={formHandlers.handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Global Error Message */}
          {(formState.submitError || error) && (
            <Alert
              severity="error"
              icon={<ErrorOutline />}
              sx={{ mb: 1 }}
            >
              {formState.submitError || error}
            </Alert>
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
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              {t('auth.haveAccount')}{' '}
              <Link component={RouterLink} to="/login" underline="none" fontWeight={500}>
                {t('auth.signIn')}
              </Link>
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}