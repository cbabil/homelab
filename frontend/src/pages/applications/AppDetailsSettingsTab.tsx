/**
 * App Details Settings Tab Component
 *
 * Settings tab content showing container, storage, and environment details.
 */

import { useTranslation } from 'react-i18next'
import { Box, Typography } from '@mui/material'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'

interface AppDetailsSettingsTabProps {
  app: InstalledAppInfo
}

export function AppDetailsSettingsTab({ app }: AppDetailsSettingsTabProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ overflowY: 'auto', flex: 1, minHeight: 0 }}>
      {/* Container Section */}
      <Typography variant="caption" fontWeight={500}>
        {t('applications.container.title')}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.25 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.container.name')}
        </Typography>
        <Typography
          variant="caption"
          sx={{
            fontFamily: 'monospace',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            maxWidth: 280
          }}
        >
          {app.containerName}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.25 }}>
        <Typography variant="caption" color="text.secondary">
          {t('applications.container.networks')}
        </Typography>
        <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
          {app.networks.length > 0 ? app.networks.join(', ') : '-'}
        </Typography>
      </Box>
      {Object.keys(app.ports).length > 0 && (
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.25 }}
        >
          <Typography variant="caption" color="text.secondary">
            {t('applications.container.ports')}
          </Typography>
          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
            {Object.entries(app.ports)
              .map(([containerPort, hostPort]) => `${containerPort} -> ${hostPort}`)
              .join(', ')}
          </Typography>
        </Box>
      )}

      {/* Storage Section */}
      {(app.namedVolumes.length > 0 || app.bindMounts.length > 0) && (
        <>
          <Typography variant="caption" fontWeight={500} sx={{ mt: 3, display: 'block' }}>
            {t('applications.storage')}
          </Typography>
          {app.namedVolumes.map((vol) => (
            <Box
              key={vol.name}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.5
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 180
                }}
              >
                {vol.name}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 200
                }}
              >
                {vol.destination}
              </Typography>
            </Box>
          ))}
          {app.bindMounts.map((mount) => (
            <Box
              key={mount.source}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.5
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 180
                }}
              >
                {mount.source}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 200
                }}
              >
                {mount.destination}
              </Typography>
            </Box>
          ))}
        </>
      )}

      {/* Environment Section */}
      {Object.keys(app.env).length > 0 && (
        <>
          <Typography variant="caption" fontWeight={500} sx={{ mt: 3, display: 'block' }}>
            {t('applications.environment')}
          </Typography>
          {Object.entries(app.env).map(([key, value]) => (
            <Box
              key={key}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                py: 0.25
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {key}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  fontFamily: 'monospace',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 200
                }}
              >
                {value}
              </Typography>
            </Box>
          ))}
        </>
      )}
    </Box>
  )
}
