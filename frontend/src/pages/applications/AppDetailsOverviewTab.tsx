/**
 * App Details Overview Tab Component
 *
 * Overview tab content showing app status, server info, and timestamps.
 */

import { useTranslation } from 'react-i18next'
import { AlertCircle, ExternalLink } from 'lucide-react'
import { Box, Chip, Typography, Link, Alert, Stack } from '@mui/material'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'
import { formatLogTimestamp } from '@/utils/timezone'
import { getStatusChipColor, getAccessUrl, STATUS_TRANSLATION_KEYS } from './appDetailsPanelUtils'

interface AppDetailsOverviewTabProps {
  app: InstalledAppInfo
  userTimezone: string
}

export function AppDetailsOverviewTab({ app, userTimezone }: AppDetailsOverviewTabProps) {
  const { t } = useTranslation()
  const accessUrl = getAccessUrl(app)

  return (
    <Stack spacing={1} sx={{ overflowY: 'auto', flex: 1, minHeight: 0 }}>
      {/* Error Message */}
      {app.errorMessage && (
        <Alert severity="error" icon={<AlertCircle size={16} />} sx={{ mb: 1.5 }}>
          <Typography variant="caption">{app.errorMessage}</Typography>
        </Alert>
      )}

      {/* Details Section */}
      <Typography variant="caption" fontWeight={500}>
        {t('applications.details.title')}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.columns.status')}
        </Typography>
        <Chip
          size="small"
          color={getStatusChipColor(app.status)}
          label={t(STATUS_TRANSLATION_KEYS[app.status] || `applications.status.${app.status}`)}
        />
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.columns.server')}
        </Typography>
        <Typography variant="caption">{app.serverName}</Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.details.host')}
        </Typography>
        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
          {app.serverHost}
        </Typography>
      </Box>

      {accessUrl && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}
        >
          <Typography variant="caption" color="text.secondary">
            {t('applications.columns.access')}
          </Typography>
          <Link
            href={accessUrl}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              fontSize: '0.75rem',
              textDecoration: 'none',
              '&:hover': { textDecoration: 'underline' }
            }}
          >
            <ExternalLink size={12} />
            {t('applications.actions.openApp')}
          </Link>
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.columns.installed')}
        </Typography>
        <Typography variant="caption">{formatLogTimestamp(app.installedAt, userTimezone)}</Typography>
      </Box>

      {app.startedAt && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5 }}
        >
          <Typography variant="caption" color="text.secondary">
            {t('applications.details.lastStarted')}
          </Typography>
          <Typography variant="caption">{formatLogTimestamp(app.startedAt, userTimezone)}</Typography>
        </Box>
      )}

      {/* App Info Section */}
      {(app.appDescription || app.appCategory || app.appSource) && (
        <Stack spacing={1} sx={{ mt: 'auto', pt: 2 }}>
          <Typography variant="caption" fontWeight={500}>
            {t('applications.details.about')}
          </Typography>
          {app.appDescription && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.5
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {t('applications.details.description')}
              </Typography>
              <Typography variant="caption" sx={{ textAlign: 'right', maxWidth: 280 }}>
                {app.appDescription}
              </Typography>
            </Box>
          )}

          {app.appCategory && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.5
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {t('applications.columns.category')}
              </Typography>
              <Typography variant="caption">{app.appCategory}</Typography>
            </Box>
          )}

          {app.appSource && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.5
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {t('applications.columns.marketplace')}
              </Typography>
              <Typography variant="caption">{app.appSource}</Typography>
            </Box>
          )}
        </Stack>
      )}
    </Stack>
  )
}
