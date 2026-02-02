/**
 * App Details Panel Component
 *
 * Side panel that slides in from the right to show installed app details.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Box } from '@mui/material'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { useDataServices } from '@/hooks/useDataServices'
import { LogEntry as LogEntryType } from '@/types/logs'
import { TabId, LOG_ROW_HEIGHT, MIN_LOGS_PER_PAGE } from './appDetailsPanelUtils'
import { AppDetailsPanelHeader } from './AppDetailsPanelHeader'
import { AppDetailsOverviewTab } from './AppDetailsOverviewTab'
import { AppDetailsSettingsTab } from './AppDetailsSettingsTab'
import { AppDetailsLogsTab } from './AppDetailsLogsTab'

interface AppDetailsPanelProps {
  app: InstalledAppInfo | null
  onClose: () => void
}

export function AppDetailsPanel({ app, onClose }: AppDetailsPanelProps) {
  const { settings } = useSettingsContext()
  const { logs: logsService, isConnected } = useDataServices()
  const userTimezone = settings?.ui.timezone || 'UTC'
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [allLogs, setAllLogs] = useState<LogEntryType[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsError, setLogsError] = useState<string | null>(null)
  const [logsPage, setLogsPage] = useState(1)
  const [logsPerPage, setLogsPerPage] = useState(MIN_LOGS_PER_PAGE)
  const logsContainerRef = useRef<HTMLDivElement>(null)

  // Filter logs for this specific app
  const appLogs = useMemo(() => {
    if (!app || allLogs.length === 0) return []

    const appName = app.appName.toLowerCase()
    const appId = app.appId?.toLowerCase() || ''
    const containerName = app.containerName.toLowerCase()

    return allLogs.filter((log) => {
      const source = log.source.toLowerCase()
      if (source.includes(appName) || source.includes(containerName)) return true

      const message = log.message.toLowerCase()
      if (message.includes(appName) || message.includes(containerName)) return true
      if (appId && message.includes(appId)) return true

      if (log.metadata?.app_id === app.appId) return true
      if (log.metadata?.container_name === app.containerName) return true

      if (
        log.tags?.some(
          (tag) => tag.toLowerCase().includes(appName) || tag.toLowerCase().includes(containerName)
        )
      )
        return true

      return false
    })
  }, [app, allLogs])

  // Pagination calculations
  const totalLogsPages = Math.ceil(appLogs.length / logsPerPage)
  const paginatedLogs = useMemo(() => {
    const start = (logsPage - 1) * logsPerPage
    return appLogs.slice(start, start + logsPerPage)
  }, [appLogs, logsPage, logsPerPage])

  // Reset page when app changes
  useEffect(() => {
    setLogsPage(1)
  }, [app?.id])

  // Calculate logs per page based on available space
  useEffect(() => {
    const calculateLogsPerPage = () => {
      if (!logsContainerRef.current) return

      const containerHeight = logsContainerRef.current.clientHeight
      const availableHeight = containerHeight - 100
      const calculatedRows = Math.floor(availableHeight / LOG_ROW_HEIGHT)
      setLogsPerPage(Math.max(MIN_LOGS_PER_PAGE, calculatedRows))
    }

    calculateLogsPerPage()
    window.addEventListener('resize', calculateLogsPerPage)
    return () => window.removeEventListener('resize', calculateLogsPerPage)
  }, [activeTab])

  const fetchLogs = useCallback(async () => {
    if (!app || !isConnected) return

    setLogsLoading(true)
    setLogsError(null)

    try {
      const result = await logsService.getAll({ limit: 200 })

      if (result.success && result.data) {
        setAllLogs(result.data)
      } else {
        setLogsError(result.error || 'Failed to fetch logs')
        setAllLogs([])
      }
    } catch (err) {
      setLogsError(err instanceof Error ? err.message : 'Failed to fetch logs')
      setAllLogs([])
    } finally {
      setLogsLoading(false)
    }
  }, [app, logsService, isConnected])

  // Fetch logs when switching to logs tab and auto-refresh every 30 seconds
  useEffect(() => {
    if (activeTab === 'logs' && app) {
      fetchLogs()

      const interval = setInterval(() => {
        fetchLogs()
      }, 30000)

      return () => clearInterval(interval)
    }
  }, [activeTab, app, fetchLogs])

  if (!app) return null

  return createPortal(
    <>
      {/* Backdrop */}
      <Box
        sx={{
          position: 'fixed',
          inset: 0,
          bgcolor: 'rgba(0, 0, 0, 0.2)',
          zIndex: 40
        }}
        onClick={onClose}
      />

      {/* Panel */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          bottom: 0,
          right: 0,
          width: 480,
          bgcolor: 'background.paper',
          borderLeft: 1,
          borderColor: 'divider',
          boxShadow: 24,
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInFromRight 200ms ease-out',
          '@keyframes slideInFromRight': {
            from: { transform: 'translateX(100%)' },
            to: { transform: 'translateX(0)' }
          }
        }}
      >
        <AppDetailsPanelHeader
          app={app}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onClose={onClose}
        />

        {/* Content */}
        <Box sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {activeTab === 'overview' && (
            <AppDetailsOverviewTab app={app} userTimezone={userTimezone} />
          )}

          {activeTab === 'settings' && <AppDetailsSettingsTab app={app} />}

          {activeTab === 'logs' && (
            <AppDetailsLogsTab
              logs={appLogs}
              paginatedLogs={paginatedLogs}
              logsLoading={logsLoading}
              logsError={logsError}
              logsPage={logsPage}
              totalLogsPages={totalLogsPages}
              userTimezone={userTimezone}
              onPageChange={setLogsPage}
              logsContainerRef={logsContainerRef}
            />
          )}
        </Box>
      </Box>
    </>,
    document.body
  )
}
