/**
 * Settings Action Footer Component
 *
 * Footer with action buttons and save status information.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check, RotateCcw } from 'lucide-react'
import { Box, Stack, Typography } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { Button } from '@/components/ui/Button'

const styles: Record<string, SxProps<Theme>> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0
  },
  successMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: 1,
    fontSize: '0.875rem',
    color: 'success.main',
    bgcolor: 'success.light',
    border: 1,
    borderColor: 'success.main',
    borderRadius: 2,
    px: 1.5,
    py: 1
  },
  autoSaveMessage: {
    fontSize: '0.875rem',
    color: 'text.secondary',
    display: 'flex',
    alignItems: 'center',
    gap: 1
  }
}

export function SettingsActionFooter() {
  const { t } = useTranslation()
  const { resetSettings } = useSettingsContext()
  const [isResetting, setIsResetting] = useState(false)
  const [resetSuccess, setResetSuccess] = useState(false)

  const handleResetToDefaults = async () => {
    try {
      setIsResetting(true)
      const result = await resetSettings()

      if (result.success) {
        setResetSuccess(true)
        setTimeout(() => setResetSuccess(false), 2000)
      }
    } catch (error) {
      console.error('Failed to reset settings:', error)
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <Stack sx={styles.container}>
      <Stack direction="row" spacing={1}>
        <Button
          onClick={handleResetToDefaults}
          disabled={isResetting}
          variant="outline"
          size="sm"
          leftIcon={<RotateCcw style={{ width: 12, height: 12 }} className={isResetting ? 'animate-spin' : ''} />}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
        >
          {isResetting ? t('settings.resetting') : t('settings.resetToDefaults')}
        </Button>

        {resetSuccess && (
          <Box sx={styles.successMessage}>
            <Check className="w-4 h-4" />
            <Typography variant="body2">{t('settings.settingsResetSuccess')}</Typography>
          </Box>
        )}
      </Stack>

      <Typography sx={styles.autoSaveMessage}>
        <Check className="w-4 h-4 text-green-500" />
        {t('settings.changesAutoSaved')}
      </Typography>
    </Stack>
  )
}