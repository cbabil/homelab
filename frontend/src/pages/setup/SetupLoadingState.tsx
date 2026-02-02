/**
 * Setup Loading State Component
 *
 * Displays a loading spinner while checking system setup status.
 */

import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function SetupLoadingState() {
  const { t } = useTranslation()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: (theme) =>
          theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <Box sx={{ textAlign: 'center' }}>
        <Loader2 size={32} style={{ marginBottom: 16, color: 'hsl(var(--primary))' }} className="animate-spin" />
        <Typography color="text.secondary">{t('common.loading')}</Typography>
      </Box>
    </Box>
  )
}
