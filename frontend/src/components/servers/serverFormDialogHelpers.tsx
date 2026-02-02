/**
 * Server Form Dialog Helpers
 *
 * Extracted helper components for ServerFormDialog
 * to keep the main component focused and under 120 lines.
 */

import { ChangeEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Stack, TextField, Typography } from '@mui/material'
import { ServerConnectionInput } from '@/types/server'
import { AuthenticationSection } from './AuthenticationSection'
import { useAnimatedDots } from './serverFormUtils'

interface ServerBasicFieldsProps {
  formData: ServerConnectionInput
  onInputChange: (field: keyof ServerConnectionInput, value: string | number) => void
  onHostChange: (e: ChangeEvent<HTMLInputElement>) => void
  disabled: boolean
}

export function ServerBasicFields({
  formData, onInputChange, onHostChange, disabled,
}: ServerBasicFieldsProps) {
  return (
    <Stack spacing={1.5}>
      <TextField
        label="Name" value={formData.name} placeholder="My Server"
        onChange={(e) => onInputChange('name', e.target.value)}
        required fullWidth size="small" disabled={disabled}
      />
      <Stack direction="row" spacing={1.5}>
        <TextField
          label="Host" value={formData.host} placeholder="192.168.1.100"
          onChange={onHostChange}
          required fullWidth size="small" sx={{ flex: 2 }} disabled={disabled}
        />
        <TextField
          label="Port" type="number" value={formData.port}
          onChange={(e) => onInputChange('port', parseInt(e.target.value))}
          required size="small" sx={{ flex: 1, minWidth: 80 }} disabled={disabled}
          slotProps={{ htmlInput: { min: 1, max: 65535 } }}
        />
      </Stack>
      <TextField
        label="Username" value={formData.username} placeholder="root"
        onChange={(e) => onInputChange('username', e.target.value)}
        required fullWidth size="small" disabled={disabled}
      />
    </Stack>
  )
}

interface ServerFormContentProps {
  formData: ServerConnectionInput
  onInputChange: (field: keyof ServerConnectionInput, value: string | number) => void
  onHostChange: (e: ChangeEvent<HTMLInputElement>) => void
  onAuthTypeChange: (type: 'password' | 'key') => void
  onCredentialChange: (field: string, value: string) => void
  isEditMode: boolean
  isProcessing: boolean
  submitError: string | null
}

export function ServerFormContent({
  formData, onInputChange, onHostChange, onAuthTypeChange, onCredentialChange,
  isEditMode, isProcessing, submitError,
}: ServerFormContentProps) {
  const { t } = useTranslation()
  const dots = useAnimatedDots(isProcessing)

  return (
    <Stack spacing={2.5} sx={{ mt: 2 }}>
      <ServerBasicFields
        formData={formData} onInputChange={onInputChange}
        onHostChange={onHostChange} disabled={isProcessing}
      />
      <AuthenticationSection
        authType={formData.auth_type} credentials={formData.credentials}
        onAuthTypeChange={onAuthTypeChange} onCredentialChange={onCredentialChange}
        isEditMode={isEditMode} disabled={isProcessing}
      />
      <Typography
        variant="caption" color={submitError ? 'error' : 'text.secondary'}
        sx={{ minHeight: 16, textAlign: 'center' }}
      >
        {submitError || (isProcessing && (
          <>{t('servers.form.testingConnection')}
            <span style={{ display: 'inline-block', width: 16, textAlign: 'left' }}>{dots}</span>
          </>
        )) || ' '}
      </Typography>
    </Stack>
  )
}
