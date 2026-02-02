/**
 * Password Input Component
 *
 * Password input field with show/hide functionality.
 * Uses MUI TextField for consistency with other form fields.
 */

import { useState } from 'react'
import { TextField, InputAdornment, IconButton } from '@mui/material'
import { VisibilityOutlined, VisibilityOffOutlined } from '@mui/icons-material'

interface PasswordInputProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
  required?: boolean
  disabled?: boolean
}

export function PasswordInput({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false)

  return (
    <TextField
      label={label}
      type={showPassword ? 'text' : 'password'}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      fullWidth
      size="small"
      slotProps={{
        input: {
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword(!showPassword)}
                edge="end"
                size="small"
              >
                {showPassword ? <VisibilityOutlined fontSize="small" /> : <VisibilityOffOutlined fontSize="small" />}
              </IconButton>
            </InputAdornment>
          ),
        },
      }}
    />
  )
}