/**
 * Security Settings Component
 *
 * Security configuration for session, account locking, and password policy.
 * Single card with vertical sections separated by dividers.
 */

import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { TextField, CircularProgress, Stack, Box, Typography, Select, MenuItem, FormControl, SelectChangeEvent, Divider } from '@mui/material'
import { SettingRow } from './components'
import { PasswordPolicySection, PasswordPolicySettings } from './PasswordPolicySection'
import { useSettingsSaving } from './SettingsSavingContext'
import { useMCP } from '@/providers/MCPProvider'
import { useToast } from '@/components/ui/Toast'
import { AUTH_STORAGE_KEYS } from '@/types/auth'
import { useSecuritySettings } from '@/hooks/useSecuritySettings'
import { AgentAuditTable } from '@/components/audit'
import { useAgentAudit } from '@/hooks/useAgentAudit'
import { useServers } from '@/hooks/useServers'

interface SecuritySettingsResponse {
  success: boolean
  data?: {
    settings: Record<string, {
      value: number | string | boolean
      category: string
      source: string
    }>
  }
  message?: string
}

interface SettingsUpdateResponse {
  success: boolean
  message?: string
}

interface SecuritySettingsState extends PasswordPolicySettings {
  maxLoginAttempts: number
  lockoutDuration: number
  passwordMaxLength: number
  allowUnicodePasswords: boolean
}

const DEFAULT_SETTINGS: SecuritySettingsState = {
  maxLoginAttempts: 5,
  lockoutDuration: 900,
  passwordMinLength: 8,
  passwordMaxLength: 128,
  passwordRequireSpecial: true,
  passwordRequireNumbers: true,
  passwordRequireUppercase: true,
  passwordExpirationDays: 90,
  enableBlocklistCheck: true,
  enableHibpCheck: false,
  allowUnicodePasswords: true
}

const sessionTimeoutOptions = [
  { label: '30 minutes', value: '30m' },
  { label: '1 hour', value: '1h' },
  { label: '4 hours', value: '4h' },
  { label: '8 hours', value: '8h' },
  { label: '24 hours', value: '24h' }
]

const selectStyles = {
  height: 32,
  minWidth: 144,
  fontSize: '0.75rem',
  borderRadius: 1,
  bgcolor: 'transparent',
  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' },
  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.4)' },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: 'primary.main', borderWidth: 1 },
  '& .MuiSelect-select': { py: 0.5, px: 1 }
}

const menuProps = { PaperProps: { sx: { '& .MuiMenuItem-root': { fontSize: '0.75rem' } } } }

export function SecuritySettings() {
  const { t } = useTranslation()
  const { client, isConnected } = useMCP()
  const { addToast } = useToast()
  const { sessionTimeout, onSessionTimeoutChange } = useSecuritySettings()

  const [settings, setSettings] = useState<SecuritySettingsState>(DEFAULT_SETTINGS)
  const [isLoadingSettings, setIsLoadingSettings] = useState(false)
  const { setIsSaving } = useSettingsSaving()

  // Agent audit data
  const { entries: auditEntries, isLoading: auditLoading, error: auditError, filters: auditFilters, setFilters: setAuditFilters, refresh: refreshAudit } = useAgentAudit({ limit: 10 })
  const { servers } = useServers()

  const fetchSecuritySettings = useCallback(async () => {
    if (!isConnected) return
    const token = localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
    if (!token) return

    setIsLoadingSettings(true)
    try {
      const response = await client.callTool<SecuritySettingsResponse>('get_settings', {
        user_id: 'admin',
        setting_keys: [
          'security.max_login_attempts', 'security.account_lockout_duration',
          'security.password_min_length', 'security.password_max_length',
          'security.password_require_special_chars', 'security.password_require_numbers',
          'security.password_require_uppercase', 'security.force_password_change_days',
          'security.enable_blocklist_check', 'security.enable_hibp_check',
          'security.allow_unicode_passwords'
        ],
        include_system_defaults: true
      })

      const result = response.data as SecuritySettingsResponse | undefined
      if (response.success && result?.success && result?.data?.settings) {
        const s = result.data.settings
        const newSettings: SecuritySettingsState = {
          maxLoginAttempts: s['security.max_login_attempts']?.value as number ?? 5,
          lockoutDuration: s['security.account_lockout_duration']?.value as number ?? 900,
          passwordMinLength: s['security.password_min_length']?.value as number ?? 8,
          passwordMaxLength: s['security.password_max_length']?.value as number ?? 128,
          passwordRequireSpecial: s['security.password_require_special_chars']?.value as boolean ?? true,
          passwordRequireNumbers: s['security.password_require_numbers']?.value as boolean ?? true,
          passwordRequireUppercase: s['security.password_require_uppercase']?.value as boolean ?? true,
          passwordExpirationDays: s['security.force_password_change_days']?.value as number ?? 90,
          enableBlocklistCheck: s['security.enable_blocklist_check']?.value as boolean ?? true,
          enableHibpCheck: s['security.enable_hibp_check']?.value as boolean ?? false,
          allowUnicodePasswords: s['security.allow_unicode_passwords']?.value as boolean ?? true
        }
        setSettings(newSettings)
      }
    } catch (err) {
      console.error('Failed to fetch security settings:', err)
    } finally {
      setIsLoadingSettings(false)
    }
  }, [isConnected, client])

  useEffect(() => {
    if (isConnected) fetchSecuritySettings()
  }, [isConnected, fetchSecuritySettings])

  const saveSettings = useCallback(async (newSettings: SecuritySettingsState) => {
    const token = localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
    if (!token || !isConnected) return
    setIsSaving(true)
    try {
      await client.callTool<SettingsUpdateResponse>('update_settings', {
        user_id: 'admin',
        settings: {
          'security.max_login_attempts': newSettings.maxLoginAttempts,
          'security.account_lockout_duration': newSettings.lockoutDuration,
          'security.password_min_length': newSettings.passwordMinLength,
          'security.password_max_length': newSettings.passwordMaxLength,
          'security.password_require_special_chars': newSettings.passwordRequireSpecial,
          'security.password_require_numbers': newSettings.passwordRequireNumbers,
          'security.password_require_uppercase': newSettings.passwordRequireUppercase,
          'security.force_password_change_days': newSettings.passwordExpirationDays,
          'security.enable_blocklist_check': newSettings.enableBlocklistCheck,
          'security.enable_hibp_check': newSettings.enableHibpCheck,
          'security.allow_unicode_passwords': newSettings.allowUnicodePasswords
        },
        change_reason: 'Updated via Settings page'
      })
    } catch (err) {
      addToast({ type: 'error', title: t('settings.securitySettings.failedToSave'), message: err instanceof Error ? err.message : 'Unknown error' })
    } finally {
      setIsSaving(false)
    }
  }, [isConnected, client, addToast, t])

  const updateSetting = <K extends keyof SecuritySettingsState>(key: K, value: SecuritySettingsState[K]) => {
    setSettings(prev => {
      const newSettings = { ...prev, [key]: value }
      saveSettings(newSettings)
      return newSettings
    })
  }

  if (isLoadingSettings) {
    return (
      <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', p: 2, display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={32} />
      </Box>
    )
  }

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
      {/* Session */}
      <Box>
        <Typography sx={{ fontSize: '0.85rem', fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
          {t('settings.generalSettings.session')}
        </Typography>
        <SettingRow label={t('settings.generalSettings.sessionTimeout')}>
          <FormControl size="small">
            <Select value={sessionTimeout} onChange={(e: SelectChangeEvent) => onSessionTimeoutChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}>
              {sessionTimeoutOptions.map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
            </Select>
          </FormControl>
        </SettingRow>
      </Box>

      <Divider sx={{ my: 1.5 }} />

      {/* Account Locking */}
      <Box>
        <Typography sx={{ fontSize: '0.85rem', fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
          {t('settings.securitySettings.accountLocking')}
        </Typography>
        <Stack spacing={0}>
          <SettingRow label={t('settings.securitySettings.maxAttempts')}>
            <TextField type="number" size="small" value={settings.maxLoginAttempts} onChange={(e) => updateSetting('maxLoginAttempts', Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))} inputProps={{ min: 1, max: 20 }} sx={{ width: 60, '& .MuiInputBase-root': { height: 32 }, '& .MuiInputBase-input': { py: 0.5, px: 1, fontSize: '0.75rem' } }} />
          </SettingRow>
          <SettingRow label={t('settings.securitySettings.lockoutDuration')}>
            <FormControl size="small">
              <Select value={String(settings.lockoutDuration)} onChange={(e) => updateSetting('lockoutDuration', parseInt(e.target.value))} size="small" sx={selectStyles} MenuProps={menuProps}>
                <MenuItem value={300}>5 min</MenuItem>
                <MenuItem value={900}>15 min</MenuItem>
                <MenuItem value={1800}>30 min</MenuItem>
                <MenuItem value={3600}>1 hr</MenuItem>
                <MenuItem value={86400}>24 hr</MenuItem>
              </Select>
            </FormControl>
          </SettingRow>
        </Stack>
      </Box>

      <Divider sx={{ my: 1.5 }} />

      {/* Password Policy */}
      <PasswordPolicySection
        settings={settings}
        onSettingChange={updateSetting as <K extends keyof PasswordPolicySettings>(key: K, value: PasswordPolicySettings[K]) => void}
      />

      <Divider sx={{ my: 1.5 }} />

      {/* Agent Activity Audit */}
      <Box>
        <Typography sx={{ fontSize: '0.85rem', fontWeight: 600, color: 'primary.main', mb: 0.5 }}>
          {t('audit.agentActivity')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem', mb: 1 }}>
          {t('audit.agentActivityDescription')}
        </Typography>
        <AgentAuditTable
          entries={auditEntries}
          isLoading={auditLoading}
          error={auditError}
          filters={auditFilters}
          onFilterChange={setAuditFilters}
          onRefresh={refreshAudit}
          compact
          servers={servers}
        />
      </Box>
    </Box>
  )
}
