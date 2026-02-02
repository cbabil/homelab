/**
 * Notification Settings Component
 *
 * System alerts and notification preferences configuration.
 * Single card with vertical sections separated by dividers.
 */

import { useTranslation } from 'react-i18next'
import { Stack, Box, Typography } from '@mui/material'
import { Toggle, SettingRow } from './components'

interface NotificationSettingsProps {
  serverAlerts: boolean
  resourceAlerts: boolean
  updateAlerts: boolean
  onServerAlertsChange: (checked: boolean) => void
  onResourceAlertsChange: (checked: boolean) => void
  onUpdateAlertsChange: (checked: boolean) => void
}

export function NotificationSettings({
  serverAlerts,
  resourceAlerts,
  updateAlerts,
  onServerAlertsChange,
  onResourceAlertsChange,
  onUpdateAlertsChange
}: NotificationSettingsProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', p: 2, flex: 1 }}>
      {/* System Alerts */}
      <Box>
        <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>
          {t('settings.notificationSettings.systemAlerts')}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('settings.notificationSettings.systemAlertsDescription')}
        </Typography>
        <Stack spacing={0.5}>
          <SettingRow label={t('settings.notificationSettings.serverAlerts')}>
            <Toggle checked={serverAlerts} onChange={onServerAlertsChange} aria-label={t('settings.notificationSettings.serverAlerts')} />
          </SettingRow>
          <SettingRow label={t('settings.notificationSettings.resourceAlerts')}>
            <Toggle checked={resourceAlerts} onChange={onResourceAlertsChange} aria-label={t('settings.notificationSettings.resourceAlerts')} />
          </SettingRow>
          <SettingRow label={t('settings.notificationSettings.updateAlerts')}>
            <Toggle checked={updateAlerts} onChange={onUpdateAlertsChange} aria-label={t('settings.notificationSettings.updateAlerts')} />
          </SettingRow>
        </Stack>
      </Box>
    </Box>
  )
}