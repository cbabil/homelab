/**
 * Login Form Fields Component
 *
 * Individual form fields for the login form using MUI components.
 */

import { useTranslation } from 'react-i18next'
import TextField from '@mui/material/TextField'
import InputAdornment from '@mui/material/InputAdornment'
import IconButton from '@mui/material/IconButton'
import { VisibilityOutlined, VisibilityOffOutlined, Person, Lock } from '@mui/icons-material'
import { LoginFormState } from '@/types/auth'

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
  const { t } = useTranslation()

  return (
    <>
      {/* Username Field */}
      <TextField
        id="username"
        label={t('auth.username')}
        type="text"
        autoComplete="username"
        required
        fullWidth
        placeholder={t('auth.username')}
        value={formState.username.value}
        onChange={(e) => onInputChange('username', e.target.value)}
        error={!!formState.username.error}
        helperText={formState.username.error}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <Person color="action" />
              </InputAdornment>
            ),
          },
        }}
        sx={{ mb: 2 }}
      />

      {/* Password Field */}
      <TextField
        id="password"
        label={t('auth.password')}
        type={showPassword ? 'text' : 'password'}
        autoComplete="current-password"
        required
        fullWidth
        placeholder={t('auth.password')}
        value={formState.password.value}
        onChange={(e) => onInputChange('password', e.target.value)}
        error={!!formState.password.error}
        helperText={formState.password.error}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <Lock color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label={showPassword ? t('auth.hidePassword', 'Hide password') : t('auth.showPassword', 'Show password')}
                  onClick={onTogglePassword}
                  edge="end"
                  disableRipple
                  sx={{
                    color: 'hsl(250 76% 72%)',
                    '&:hover': {
                      backgroundColor: 'transparent',
                      color: 'hsl(250 85% 80%)'
                    }
                  }}
                >
                  {showPassword ? <VisibilityOutlined /> : <VisibilityOffOutlined />}
                </IconButton>
              </InputAdornment>
            ),
          },
        }}
      />
    </>
  )
}