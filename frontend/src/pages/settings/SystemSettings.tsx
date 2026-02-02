/**
 * System Settings Component
 *
 * System-level settings including data retention, backup/restore, and version info.
 * Single card with vertical sections separated by dividers.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Stack, Box, Typography, Divider } from '@mui/material'
import { DataRetentionSettings } from './components/DataRetentionSettings'
import { BackupSection } from '@/components/settings/BackupSection'
import { useMCP } from '@/providers/MCPProvider'

interface ComponentVersions {
  backend: string
  frontend: string
  api: string
}

interface VersionResponse {
  success: boolean
  data?: {
    backend: string
    frontend: string
    api: string
  }
}

export function SystemSettings() {
  const { t } = useTranslation()
  const { client, isConnected } = useMCP()
  const [versions, setVersions] = useState<ComponentVersions | null>(null)
  const [versionsLoading, setVersionsLoading] = useState(true)

  // Fetch component versions when connected
  useEffect(() => {
    if (!isConnected) {
      setVersionsLoading(false)
      return
    }

    const fetchVersions = async () => {
      try {
        const response = await client.callTool<VersionResponse>(
          'get_component_versions',
          {}
        )
        const result = response.data as VersionResponse | undefined

        if (response.success && result?.success && result?.data) {
          setVersions({
            backend: result.data.backend,
            frontend: result.data.frontend,
            api: result.data.api
          })
        }
      } catch (err) {
        console.error('Failed to fetch versions:', err)
      } finally {
        setVersionsLoading(false)
      }
    }
    fetchVersions()
  }, [client, isConnected])

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', p: 2, flex: 1 }}>
      {/* Data Retention Section */}
      <DataRetentionSettings />

      <Divider sx={{ my: 4 }} />

      {/* Backup & Restore Section */}
      <BackupSection />

      <Divider sx={{ my: 4 }} />

      {/* Version Information */}
      <Box>
        <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>
          {t('settings.versionInfo.title')}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('settings.versionInfo.description')}
        </Typography>
        <Stack spacing={0.25} sx={{ mt: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', minWidth: 60 }}>
              {t('settings.versionInfo.backend')}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
              {versionsLoading ? '...' : (versions?.backend || 'N/A')}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', minWidth: 60 }}>
              {t('settings.versionInfo.frontend')}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
              {versionsLoading ? '...' : (versions?.frontend || 'N/A')}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', minWidth: 60 }}>
              {t('settings.versionInfo.api')}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
              {versionsLoading ? '...' : (versions?.api || 'N/A')}
            </Typography>
          </Stack>
        </Stack>
      </Box>
    </Box>
  )
}
