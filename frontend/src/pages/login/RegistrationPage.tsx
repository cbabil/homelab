/**
 * Registration Page Component
 *
 * User registration page with comprehensive form validation, password strength,
 * and security features. Follows LoginPage patterns for consistency.
 */

import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { useAuth } from '@/providers/AuthProvider'
import { CopyrightFooter } from '@/components/ui/CopyrightFooter'
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'
import { RegistrationFormState } from '@/types/auth'
import { RegistrationForm } from '@/components/auth/RegistrationForm'
import { createFormHandlers } from '@/utils/registrationFormHandlers'

// Type for location state passed from protected routes
interface LocationState {
  from?: {
    pathname: string
  }
}

export function RegistrationPage() {
  const { t } = useTranslation()
  const { register, isAuthenticated, error } = useAuth()
  const location = useLocation()

  // Redirect to intended destination after registration
  const state = location.state as LocationState | null
  const from = state?.from?.pathname || '/'

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formState, setFormState] = useState<RegistrationFormState>({
    username: {
      value: '',
      error: '',
      isValid: false
    },
    email: {
      value: '',
      error: '',
      isValid: false
    },
    password: {
      value: '',
      error: '',
      isValid: false,
      strength: undefined
    },
    confirmPassword: {
      value: '',
      error: '',
      isValid: false
    },
    acceptTerms: {
      value: false,
      error: '',
      isValid: false
    },
    isSubmitting: false,
    submitError: ''
  })

  // If already authenticated, redirect to intended destination
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  // Create form handlers using utility
  const formHandlers = createFormHandlers(formState, setFormState, register)

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: (theme) =>
          theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 448 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box
            component="img"
            src={TomoLogo}
            alt="Tomo Logo"
            sx={{
              width: 80,
              height: 80,
              mx: 'auto',
              mb: 2,
            }}
          />
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {t('auth.createAccount')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('auth.joinTomo')}
          </Typography>
        </Box>

        {/* Registration Form */}
        <RegistrationForm
          formState={formState}
          formHandlers={formHandlers}
          showPassword={showPassword}
          showConfirmPassword={showConfirmPassword}
          onTogglePassword={() => setShowPassword(!showPassword)}
          onToggleConfirmPassword={() => setShowConfirmPassword(!showConfirmPassword)}
          error={error}
        />

        {/* Footer */}
        <Box sx={{ mt: 3 }}>
          <CopyrightFooter />
        </Box>
      </Box>
    </Box>
  )
}