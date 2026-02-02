/**
 * Setup Success Message Component
 *
 * Displays a success message after admin account creation.
 */

import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { CheckCircle2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function SetupSuccessMessage() {
  const { t } = useTranslation()

  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <CheckCircle2 size={64} style={{ color: '#10b981', marginBottom: 16 }} />
      <Typography variant="h6" fontWeight={600} gutterBottom>
        {t('setup.setupComplete')}
      </Typography>
      <Typography color="text.secondary">{t('setup.redirectingToLogin')}</Typography>
    </Box>
  )
}
