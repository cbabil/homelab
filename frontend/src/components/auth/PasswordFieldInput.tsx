/**
 * Single Password Input Component
 *
 * Reusable password input with toggle visibility functionality.
 */

import TextField from '@mui/material/TextField'
import InputAdornment from '@mui/material/InputAdornment'
import IconButton from '@mui/material/IconButton'
import { VisibilityOutlined, VisibilityOffOutlined, Lock } from '@mui/icons-material'

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
  isSubmitting,
  autoComplete,
  onChange,
  onToggleVisibility
}: PasswordFieldInputProps) {
  return (
    <TextField
      id={id}
      label={label}
      type={showPassword ? 'text' : 'password'}
      autoComplete={autoComplete}
      required
      fullWidth
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={isSubmitting}
      error={!!error}
      helperText={error}
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
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={onToggleVisibility}
                disabled={isSubmitting}
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
      sx={{ mb: 2 }}
    />
  )
}