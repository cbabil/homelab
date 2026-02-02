/**
 * Applications Page Component
 *
 * Manage deployed/installed applications.
 * Shows installed apps in a table with a side panel for details.
 */

import { useState, useMemo, useEffect, useRef } from 'react'
import { RefreshCw, Package } from 'lucide-react'
import {
  Box,
  Alert,
  Typography,
  CircularProgress
} from '@mui/material'
import { SearchInput } from '@/components/ui/SearchInput'
import { Button } from '@/components/ui/Button'
import { useTranslation } from 'react-i18next'
import { PageHeader } from '@/components/layout/PageHeader'
import { useInstalledApps, InstalledAppInfo } from '@/hooks/useInstalledApps'
import { useMCP } from '@/providers/MCPProvider'
import { useNotifications } from '@/providers/NotificationProvider'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { InstalledAppsTable } from './InstalledAppsTable'
import { AppDetailsPanel } from './AppDetailsPanel'

export function ApplicationsPage() {
  const { t } = useTranslation()
  const { client, isConnected } = useMCP()
  const { addNotification } = useNotifications()
  const { apps, isLoading, isRefreshingStatus, error, refresh, refreshLiveStatus } = useInstalledApps()

  const [searchQuery, setSearchQuery] = useState('')
  const [selectedApp, setSelectedApp] = useState<InstalledAppInfo | null>(null)

  // Filter apps by search query
  const filteredApps = useMemo(() => {
    if (!searchQuery.trim()) return apps

    const query = searchQuery.toLowerCase()
    return apps.filter(
      (app) =>
        app.appName.toLowerCase().includes(query) ||
        app.serverName.toLowerCase().includes(query) ||
        app.appDescription?.toLowerCase().includes(query)
    )
  }, [apps, searchQuery])

  // Handle app actions
  const handleStart = async (app: InstalledAppInfo) => {
    if (!isConnected) return

    try {
      const response = await client.callTool('start_app', {
        server_id: app.serverId,
        app_id: app.appId
      })

      if (response.success) {
        addNotification({ type: 'success', title: t('applications.actions.start'), message: `${app.appName} ${t('applications.status.starting')}` })
        await refresh()
        refreshLiveStatus()
      } else {
        addNotification({ type: 'error', title: t('common.error'), message: response.message || t('applications.actions.start') })
      }
    } catch (_err) {
      addNotification({ type: 'error', title: t('common.error'), message: t('applications.actions.start') })
    }
  }

  const handleStop = async (app: InstalledAppInfo) => {
    if (!isConnected) return

    try {
      const response = await client.callTool('stop_app', {
        server_id: app.serverId,
        app_id: app.appId
      })

      if (response.success) {
        addNotification({ type: 'success', title: t('applications.actions.stop'), message: `${app.appName} ${t('applications.status.stopping')}` })
        await refresh()
        refreshLiveStatus()
      } else {
        addNotification({ type: 'error', title: t('common.error'), message: response.message || t('applications.actions.stop') })
      }
    } catch (_err) {
      addNotification({ type: 'error', title: t('common.error'), message: t('applications.actions.stop') })
    }
  }

  const handleRestart = async (app: InstalledAppInfo) => {
    await handleStop(app)
    // Small delay before starting
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await handleStart(app)
  }

  const handleUninstall = async (app: InstalledAppInfo) => {
    if (!isConnected) return

    try {
      const response = await client.callTool('delete_app', {
        server_id: app.serverId,
        app_id: app.appId
      })

      if (response.success) {
        addNotification({ type: 'success', title: t('common.success'), message: `${app.appName} ${t('applications.deleteApplication')}` })
        setSelectedApp(null)
        refresh()
      } else {
        addNotification({ type: 'error', title: t('common.error'), message: response.message || t('applications.deleteApplication') })
      }
    } catch (_err) {
      addNotification({ type: 'error', title: t('common.error'), message: t('applications.deleteApplication') })
    }
  }

  const handleRefresh = async () => {
    await refresh()
    await refreshLiveStatus()
  }

  // Settings for auto-refresh
  const { settings } = useSettingsContext()
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-refresh applications based on settings.ui.refreshRate
  useEffect(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }

    const refreshRate = settings?.ui?.refreshRate
    if (!refreshRate || refreshRate <= 0 || !isConnected) return

    refreshIntervalRef.current = setInterval(handleRefresh, refreshRate * 1000)

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
    }
  }, [settings?.ui?.refreshRate, isConnected])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <PageHeader
        title={t('applications.title')}
        actions={
          <>
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder={t('applications.searchPlaceholder')}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading || isRefreshingStatus}
              leftIcon={<RefreshCw style={{ width: 12, height: 12 }} className={isLoading || isRefreshingStatus ? 'animate-spin' : ''} />}
              sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
            >
              {t('common.refresh')}
            </Button>
          </>
        }
      />

      {/* App count */}
      <Typography variant="body2" color="text.secondary" fontWeight={600} sx={{ mb: 2 }}>
        {searchQuery
          ? t('applications.appCountFiltered', { filtered: filteredApps.length, total: apps.length })
          : t('applications.appCount', { count: apps.length })}
      </Typography>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {/* Error */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Loading */}
        {isLoading && apps.length === 0 && (
          <Box sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <CircularProgress size={32} />
          </Box>
        )}

        {/* Empty State */}
        {!isLoading && apps.length === 0 && !error && (
          <Box sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center'
          }}>
            <Box sx={{ mb: 2, color: 'text.secondary' }}>
              <Package size={64} style={{ opacity: 0.5 }} />
            </Box>
            <Typography variant="h6" sx={{ mb: 1 }}>{t('applications.noApplications')}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t('applications.noApplicationsDescription')}
            </Typography>
          </Box>
        )}

        {/* Apps Table */}
        {apps.length > 0 && (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <InstalledAppsTable
              apps={filteredApps}
              onSelect={setSelectedApp}
              selectedId={selectedApp?.id}
              onStart={handleStart}
              onStop={handleStop}
              onRestart={handleRestart}
              onUninstall={handleUninstall}
            />
          </Box>
        )}
      </Box>

      {/* Side Panel */}
      <AppDetailsPanel
        app={selectedApp}
        onClose={() => setSelectedApp(null)}
      />
    </Box>
  )
}
