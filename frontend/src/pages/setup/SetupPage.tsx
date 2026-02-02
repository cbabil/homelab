/**
 * Setup Page Component
 *
 * Initial admin setup page shown when no admin user exists.
 * Creates the first admin account during initial system setup.
 */

import React, { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Alert from '@mui/material/Alert'
import IconButton from '@mui/material/IconButton'
import { AlertCircle, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useMCP } from '@/providers/MCPProvider'
import { CopyrightFooter } from '@/components/ui/CopyrightFooter'
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'
import { useSystemSetup } from '@/hooks/useSystemSetup'
import {
  validateUsername,
  validatePassword,
  calculatePasswordStrength
} from '@/utils/registrationValidation'
import type { PasswordStrength } from '@/types/auth'
import { SetupLoadingState } from './SetupLoadingState'
import { SetupSuccessMessage } from './SetupSuccessMessage'
import { SetupPasswordStrength } from './SetupPasswordStrength'

interface FormField {
  value: string
  error: string
  isValid: boolean
}

interface PasswordField extends FormField {
  strength?: PasswordStrength
}

interface SetupFormState {
  username: FormField
  password: PasswordField
  confirmPassword: FormField
  isSubmitting: boolean
  submitError: string
  submitSuccess: boolean
}

const initialFormState: SetupFormState = {
  username: { value: '', error: '', isValid: false },
  password: { value: '', error: '', isValid: false },
  confirmPassword: { value: '', error: '', isValid: false },
  isSubmitting: false,
  submitError: '',
  submitSuccess: false
}

interface CreateInitialAdminResponse {
  username: string
}

interface AddRepoResponse {
  success: boolean
  data?: { id: string }
  message?: string
  error?: string
}

// Official marketplace configuration
const OFFICIAL_MARKETPLACE = {
  name: 'Tomo Marketplace',
  url: 'https://github.com/cbabil/tomo-marketplace',
  repoType: 'official',
  branch: 'master'
}

export function SetupPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { client, isConnected } = useMCP()
  const { needsSetup, isLoading } = useSystemSetup()
  const [formState, setFormState] = useState<SetupFormState>(initialFormState)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // If system doesn't need setup, redirect to login
  if (!isLoading && !needsSetup) {
    return <Navigate to="/login" replace />
  }

  // Show loading state while checking setup status
  if (isLoading || !isConnected) {
    return <SetupLoadingState />
  }

  const handleInputChange = (field: keyof Pick<SetupFormState, 'username' | 'password' | 'confirmPassword'>, value: string) => {
    let validation: { isValid: boolean; error?: string; strength?: PasswordStrength } = { isValid: true }

    switch (field) {
      case 'username':
        validation = validateUsername(value)
        break
      case 'password':
        validation = validatePassword(value)
        break
      case 'confirmPassword': {
        const confirmValidation = formState.password.value === value
          ? { isValid: true }
          : { isValid: false, error: t('setup.passwordsDoNotMatch') }
        validation = confirmValidation
        break
      }
    }

    setFormState(prev => ({
      ...prev,
      [field]: {
        value,
        error: validation.error || '',
        isValid: validation.isValid,
        ...(field === 'password' && validation.strength ? { strength: validation.strength } : {})
      },
      submitError: ''
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Final validation
    const usernameValidation = validateUsername(formState.username.value)
    const passwordValidation = validatePassword(formState.password.value)
    const confirmValidation = formState.password.value === formState.confirmPassword.value

    if (!usernameValidation.isValid || !passwordValidation.isValid || !confirmValidation) {
      setFormState(prev => ({
        ...prev,
        username: { ...prev.username, error: usernameValidation.error || '', isValid: usernameValidation.isValid },
        password: {
          ...prev.password,
          error: passwordValidation.error || '',
          isValid: passwordValidation.isValid,
          strength: passwordValidation.strength
        },
        confirmPassword: {
          ...prev.confirmPassword,
          error: confirmValidation ? '' : t('setup.passwordsDoNotMatch'),
          isValid: confirmValidation
        }
      }))
      return
    }

    setFormState(prev => ({ ...prev, isSubmitting: true, submitError: '' }))

    try {
      const result = await client.callTool<CreateInitialAdminResponse>('create_initial_admin', {
        params: {
          username: formState.username.value.trim(),
          password: formState.password.value
        }
      })

      // MCP client wraps response: result.success = transport OK, result.data = tool response
      // Tool response: { success: boolean, message: string, data?: {...} }
      const toolResponse = result.data as { success?: boolean; message?: string; error?: string } | undefined

      if (result.success && toolResponse?.success) {
        // Try to connect and sync the official marketplace (non-blocking)
        try {
          const addRepoResult = await client.callTool<AddRepoResponse>('add_repo', {
            name: OFFICIAL_MARKETPLACE.name,
            url: OFFICIAL_MARKETPLACE.url,
            repo_type: OFFICIAL_MARKETPLACE.repoType,
            branch: OFFICIAL_MARKETPLACE.branch
          })

          const repoResponse = addRepoResult.data as AddRepoResponse | undefined
          if (addRepoResult.success && repoResponse?.success && repoResponse?.data?.id) {
            // Sync the repository in the background
            client.callTool('sync_repo', { repo_id: repoResponse.data.id }).catch(() => {
              // Ignore sync errors - marketplace connection is best-effort
            })
          }
        } catch {
          // Ignore marketplace connection errors - this is best-effort
          // User can manually add the marketplace later from Settings
        }

        setFormState(prev => ({ ...prev, isSubmitting: false, submitSuccess: true }))
        // Redirect to login after short delay
        setTimeout(() => {
          navigate('/login', {
            state: { message: t('setup.setupCompleteMessage') }
          })
        }, 1500)
      } else {
        setFormState(prev => ({
          ...prev,
          isSubmitting: false,
          submitError: toolResponse?.message || toolResponse?.error || result.message || t('setup.failedToCreateAdmin')
        }))
      }
    } catch (err) {
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        submitError: err instanceof Error ? err.message : t('setup.failedToCreateAdmin')
      }))
    }
  }

  const isFormValid = formState.username.isValid &&
    formState.password.isValid &&
    formState.confirmPassword.isValid

  const passwordStrength = formState.password.strength || calculatePasswordStrength(formState.password.value)

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
      <Box sx={{ width: '100%', maxWidth: 480 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box
            component="img"
            src={TomoLogo}
            alt="Tomo Logo"
            sx={{ width: 80, height: 80, mx: 'auto', mb: 2 }}
          />
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {t('setup.title')}
          </Typography>
          <Typography color="text.secondary">
            {t('setup.subtitle')}
          </Typography>
        </Box>

        {/* Setup Form */}
        <Card elevation={8} sx={{ borderRadius: 3, backdropFilter: 'blur(10px)', bgcolor: 'rgba(255, 255, 255, 0.95)' }}>
          <CardContent sx={{ p: 3 }}>
            {formState.submitSuccess ? (
              <SetupSuccessMessage />
            ) : (
              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Global Error Message */}
              {formState.submitError && (
                <Alert severity="error" icon={<AlertCircle size={20} />}>
                  {formState.submitError}
                </Alert>
              )}

              {/* Username Field */}
              <TextField
                id="username"
                label={t('setup.adminUsername')}
                type="text"
                value={formState.username.value}
                onChange={(e) => handleInputChange('username', e.target.value)}
                placeholder={t('setup.adminUsername')}
                autoComplete="username"
                disabled={formState.isSubmitting}
                fullWidth
                error={!!formState.username.error}
                helperText={formState.username.error}
              />

              {/* Password Field */}
              <Box>
                <TextField
                  id="password"
                  label={t('setup.adminPassword')}
                  type={showPassword ? 'text' : 'password'}
                  value={formState.password.value}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  placeholder={t('setup.adminPassword')}
                  autoComplete="new-password"
                  disabled={formState.isSubmitting}
                  fullWidth
                  error={!!formState.password.error}
                  helperText={formState.password.error}
                  InputProps={{
                    endAdornment: (
                      <IconButton
                        size="small"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <Eye size={20} /> : <EyeOff size={20} />}
                      </IconButton>
                    )
                  }}
                />

                {/* Password Strength Indicator */}
                {formState.password.value && (
                  <SetupPasswordStrength passwordStrength={passwordStrength} />
                )}
              </Box>

              {/* Confirm Password Field */}
              <TextField
                id="confirmPassword"
                label={t('setup.confirmAdminPassword')}
                type={showConfirmPassword ? 'text' : 'password'}
                value={formState.confirmPassword.value}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                placeholder={t('setup.confirmAdminPassword')}
                autoComplete="new-password"
                disabled={formState.isSubmitting}
                fullWidth
                error={!!formState.confirmPassword.error}
                helperText={formState.confirmPassword.error}
                InputProps={{
                  endAdornment: (
                    <IconButton
                      size="small"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <Eye size={20} /> : <EyeOff size={20} />}
                    </IconButton>
                  )
                }}
              />

              {/* Submit Button */}
              <Button
                type="submit"
                fullWidth
                variant="primary"
                size="lg"
                disabled={!isFormValid || formState.isSubmitting}
                loading={formState.isSubmitting}
              >
                {formState.isSubmitting ? t('common.loading') : t('setup.createAdmin')}
              </Button>
            </Box>
          )}
        </CardContent>
        </Card>

        {/* Footer */}
        <Box sx={{ mt: 3 }}>
          <CopyrightFooter />
        </Box>
      </Box>
    </Box>
  )
}
