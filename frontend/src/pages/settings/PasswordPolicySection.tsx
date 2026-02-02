/**
 * Password Policy Section Component
 *
 * Password configuration for security settings.
 * Supports both modern (SP 800-63B-4) and legacy complexity modes.
 */

import { useTranslation } from 'react-i18next'
import { TextField, Stack, Box, Typography, Select, MenuItem, FormControl, SelectChangeEvent } from '@mui/material'
import { SettingRow, Toggle } from './components'

// Common select styles
const selectStyles = {
  height: 32,
  minWidth: 144,
  fontSize: '0.75rem',
  borderRadius: 1,
  bgcolor: 'transparent',
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.23)'
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.4)'
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'primary.main',
    borderWidth: 1
  },
  '& .MuiSelect-select': {
    py: 0.5,
    px: 1
  }
}

const menuProps = {
  PaperProps: {
    sx: {
      '& .MuiMenuItem-root': {
        fontSize: '0.75rem'
      }
    }
  }
}

export interface PasswordPolicySettings {
  passwordMinLength: number
  passwordRequireSpecial: boolean
  passwordRequireNumbers: boolean
  passwordRequireUppercase: boolean
  passwordExpirationDays: number
  enableBlocklistCheck: boolean
  enableHibpCheck: boolean
}

interface PasswordPolicySectionProps {
  settings: PasswordPolicySettings
  onSettingChange: <K extends keyof PasswordPolicySettings>(key: K, value: PasswordPolicySettings[K]) => void
}

export function PasswordPolicySection({
  settings,
  onSettingChange
}: PasswordPolicySectionProps) {
  const { t } = useTranslation()

  const handleExpirationChange = (event: SelectChangeEvent) => {
    onSettingChange('passwordExpirationDays', parseInt(event.target.value))
  }

  return (
    <Box>
      <Typography sx={{ fontSize: '0.85rem', fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
        {t('settings.securitySettings.passwordPolicy')}
      </Typography>
      <Stack spacing={0}>
        {/* Minimum Length */}
        <SettingRow label={t('settings.securitySettings.minLength')}>
          <TextField
            type="number"
            size="small"
            value={settings.passwordMinLength}
            onChange={(e) => onSettingChange('passwordMinLength', Math.max(8, Math.min(128, parseInt(e.target.value) || 8)))}
            inputProps={{ min: 8, max: 128 }}
            sx={{ width: 60, '& .MuiInputBase-root': { height: 32 }, '& .MuiInputBase-input': { py: 0.5, px: 1, fontSize: '0.75rem' } }}
          />
        </SettingRow>

        {/* Blocklist Check */}
        <SettingRow label={t('settings.securitySettings.blocklistCheck')}>
          <Toggle
            checked={settings.enableBlocklistCheck}
            onChange={(checked) => onSettingChange('enableBlocklistCheck', checked)}
            aria-label={t('settings.securitySettings.blocklistCheck')}
          />
        </SettingRow>

        {/* HIBP Check */}
        <SettingRow label={t('settings.securitySettings.hibpCheck')}>
          <Toggle
            checked={settings.enableHibpCheck}
            onChange={(checked) => onSettingChange('enableHibpCheck', checked)}
            aria-label={t('settings.securitySettings.hibpCheck')}
          />
        </SettingRow>

        {/* Complexity Requirements */}
        <SettingRow label={t('settings.securitySettings.requireUppercase')}>
          <Toggle
            checked={settings.passwordRequireUppercase}
            onChange={(checked) => onSettingChange('passwordRequireUppercase', checked)}
            aria-label={t('settings.securitySettings.requireUppercase')}
          />
        </SettingRow>
        <SettingRow label={t('settings.securitySettings.requireNumbers')}>
          <Toggle
            checked={settings.passwordRequireNumbers}
            onChange={(checked) => onSettingChange('passwordRequireNumbers', checked)}
            aria-label={t('settings.securitySettings.requireNumbers')}
          />
        </SettingRow>
        <SettingRow label={t('settings.securitySettings.requireSpecial')}>
          <Toggle
            checked={settings.passwordRequireSpecial}
            onChange={(checked) => onSettingChange('passwordRequireSpecial', checked)}
            aria-label={t('settings.securitySettings.requireSpecial')}
          />
        </SettingRow>
        <SettingRow label={t('settings.securitySettings.passwordExpiration')}>
          <FormControl size="small">
            <Select
              value={String(settings.passwordExpirationDays)}
              onChange={handleExpirationChange}
              size="small"
              sx={selectStyles}
              MenuProps={menuProps}
            >
              <MenuItem value={0}>{t('settings.durations.never')}</MenuItem>
              <MenuItem value={30}>30 days</MenuItem>
              <MenuItem value={90}>90 days</MenuItem>
              <MenuItem value={180}>180 days</MenuItem>
              <MenuItem value={365}>1 year</MenuItem>
            </Select>
          </FormControl>
        </SettingRow>
      </Stack>
    </Box>
  )
}
