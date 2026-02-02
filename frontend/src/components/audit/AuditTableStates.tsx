/**
 * Audit Table State Components
 *
 * Loading, empty, and error state components for the audit table.
 */

import { useTranslation } from 'react-i18next'
import { Box, Typography, CircularProgress } from '@mui/material'
import { AlertCircle, FileText } from 'lucide-react'

/**
 * Loading state component
 */
export function AuditLoadingState() {
  const { t } = useTranslation()
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
      <CircularProgress size={32} />
      <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
        {t('common.loading')}
      </Typography>
    </Box>
  )
}

/**
 * Empty state component
 */
export function AuditEmptyState() {
  const { t } = useTranslation()
  return (
    <Box sx={{ textAlign: 'center', py: 8 }}>
      <FileText size={48} style={{ opacity: 0.4, marginBottom: 16 }} />
      <Typography variant="h6" sx={{ mb: 1 }}>{t('audit.empty.title')}</Typography>
      <Typography variant="body2" color="text.secondary">{t('audit.empty.message')}</Typography>
    </Box>
  )
}

/**
 * Error state component
 */
export function AuditErrorState({ error }: { error: string }) {
  const { t } = useTranslation()
  return (
    <Box sx={{ textAlign: 'center', py: 8 }}>
      <AlertCircle size={48} style={{ opacity: 0.6, color: '#ef4444', marginBottom: 16 }} />
      <Typography variant="h6" color="error" sx={{ mb: 1 }}>{t('audit.error.title')}</Typography>
      <Typography variant="body2" color="text.secondary">{error}</Typography>
    </Box>
  )
}
