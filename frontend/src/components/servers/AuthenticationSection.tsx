/**
 * Authentication Section Component
 *
 * Handles authentication method selection and credential input.
 * Fixed-height container prevents modal resize when switching auth types.
 */

import { useState } from 'react'
import { Box, Stack, ToggleButton, ToggleButtonGroup } from '@mui/material'
import { Key, Lock } from 'lucide-react'
import { AuthType } from '@/types/server'
import { PasswordInput } from './PasswordInput'
import { PrivateKeyFileInput } from './PrivateKeyFileInput'

interface AuthenticationSectionProps {
  authType: AuthType
  credentials: {
    password?: string
    private_key?: string
    passphrase?: string
  }
  onAuthTypeChange: (authType: AuthType) => void
  onCredentialChange: (field: string, value: string) => void
  isEditMode?: boolean
  disabled?: boolean
}

export function AuthenticationSection({
  authType,
  credentials,
  onAuthTypeChange,
  onCredentialChange,
  isEditMode = false,
  disabled = false
}: AuthenticationSectionProps) {
  const [isUpdatingKey, setIsUpdatingKey] = useState(false)
  const hasExistingKey = credentials.private_key === '***EXISTING_KEY***'

  const handleUpdateKey = () => {
    setIsUpdatingKey(true)
    onCredentialChange('private_key', '')
  }

  return (
    <Stack spacing={2}>
      {/* Auth Type Toggle */}
      <ToggleButtonGroup
        value={authType}
        exclusive
        onChange={(_, value) => value && onAuthTypeChange(value)}
        fullWidth
        size="small"
        disabled={disabled}
      >
        <ToggleButton value="password" sx={{ gap: 1 }}>
          <Lock size={16} />
          Password
        </ToggleButton>
        <ToggleButton value="key" sx={{ gap: 1 }}>
          <Key size={16} />
          Private Key
        </ToggleButton>
      </ToggleButtonGroup>

      {/* Credential Fields - Fixed height container to prevent modal resize */}
      <Box sx={{ height: 180 }}>
        {authType === 'password' ? (
          <PasswordInput
            label="Password"
            value={credentials.password || ''}
            onChange={(value) => onCredentialChange('password', value)}
            placeholder="Enter password"
            required
            disabled={disabled}
          />
        ) : (
          <Stack spacing={2}>
            {isEditMode && hasExistingKey && !isUpdatingKey ? (
              <PrivateKeyFileInput
                value={credentials.private_key || ''}
                onChange={(content) => onCredentialChange('private_key', content)}
                required
                showExistingKey
                onUpdateKey={handleUpdateKey}
                disabled={disabled}
              />
            ) : (
              <PrivateKeyFileInput
                value={credentials.private_key || ''}
                onChange={(content) => onCredentialChange('private_key', content)}
                required
                disabled={disabled}
              />
            )}

            <PasswordInput
              label="Passphrase (optional)"
              value={credentials.passphrase || ''}
              onChange={(value) => onCredentialChange('passphrase', value)}
              placeholder="Key passphrase if encrypted"
              disabled={disabled}
            />
          </Stack>
        )}
      </Box>
    </Stack>
  )
}
