/**
 * Authentication Section Component
 * 
 * Handles authentication method selection and credential input for server connections.
 */

import { AuthType } from '@/types/server'
import { AuthTypeSelector } from './AuthTypeSelector'
import { PasswordInput } from './PasswordInput'
import { PrivateKeyFileInput } from './PrivateKeyFileInput'
import { ReadOnlyPrivateKeyDisplay } from './ReadOnlyPrivateKeyDisplay'

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
}

export function AuthenticationSection({
  authType,
  credentials,
  onAuthTypeChange,
  onCredentialChange,
  isEditMode = false
}: AuthenticationSectionProps) {
  return (
    <>
      <AuthTypeSelector
        authType={authType}
        onAuthTypeChange={onAuthTypeChange}
      />

      {authType === 'password' && (
        <PasswordInput
          label="Password"
          value={credentials.password || ''}
          onChange={(value) => onCredentialChange('password', value)}
          placeholder="Enter password"
          required
        />
      )}

      {authType === 'key' && (
        <>
          {isEditMode && credentials.private_key === '***EXISTING_KEY***' ? (
            <ReadOnlyPrivateKeyDisplay />
          ) : (
            <PrivateKeyFileInput
              value={credentials.private_key || ''}
              onChange={(content) => onCredentialChange('private_key', content)}
              required
            />
          )}
          
          <PasswordInput
            label="Passphrase (optional)"
            value={credentials.passphrase || ''}
            onChange={(value) => onCredentialChange('passphrase', value)}
            placeholder="Key passphrase"
          />
        </>
      )}
    </>
  )
}