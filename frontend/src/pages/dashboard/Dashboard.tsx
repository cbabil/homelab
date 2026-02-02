/**
 * Dashboard Page Component
 *
 * Modern dashboard with real-time data from the backend.
 */

import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw } from 'lucide-react'
import { Box, Stack, Card, Grid, CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/layout/PageHeader'
import { Skeleton, SkeletonStat } from '@/components/ui/Skeleton'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { useAgentStatus } from '@/hooks/useAgentStatus'
import { useDashboardData } from './useDashboardData'
import { DashboardStats } from './DashboardStats'
import { DashboardResourceUsage } from './DashboardResourceUsage'
import { DashboardRecentActivity } from './DashboardRecentActivity'

export function Dashboard() {
  const {
    dashboardData,
    healthStatus,
    loading,
    refreshing,
    isConnected,
    refresh,
    servers
  } = useDashboardData()

  // Agent status management
  const {
    agentStatuses,
    refreshAllAgentStatuses
  } = useAgentStatus()

  // Settings for auto-refresh
  const { settings } = useSettingsContext()
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Fetch agent statuses when servers change
  useEffect(() => {
    if (servers.length > 0) {
      const serverIds = servers.map((s) => s.id)
      refreshAllAgentStatuses(serverIds)
    }
  }, [servers.length, refreshAllAgentStatuses])

  // Auto-refresh dashboard based on settings.ui.refreshRate
  useEffect(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }

    const refreshRate = settings?.ui?.refreshRate
    if (!refreshRate || refreshRate <= 0 || !isConnected) return

    const refreshAll = () => {
      refresh()
      if (servers.length > 0) {
        refreshAllAgentStatuses(servers.map((s) => s.id))
      }
    }

    refreshIntervalRef.current = setInterval(refreshAll, refreshRate * 1000)

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
    }
  }, [settings?.ui?.refreshRate, isConnected, refresh, servers, refreshAllAgentStatuses])

  if (!isConnected) {
    return <DashboardConnecting />
  }

  if (loading) {
    return <DashboardLoadingSkeleton />
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 3 }}>
      <DashboardHeader
        healthStatus={healthStatus}
        refreshing={refreshing}
        onRefresh={refresh}
      />

      <DashboardStats data={dashboardData} agentStatuses={agentStatuses} />

      <Grid container spacing={2} sx={{ flex: 1, minHeight: 0 }}>
        <Grid size={{ xs: 12, lg: 6 }} sx={{ display: 'flex' }}>
          <DashboardResourceUsage data={dashboardData} />
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }} sx={{ display: 'flex', minHeight: 0 }}>
          <DashboardRecentActivity
            activities={dashboardData?.recent_activities || []}
            servers={servers.map(s => ({ id: s.id, name: s.name }))}
          />
        </Grid>
      </Grid>
    </Box>
  )
}

function DashboardConnecting() {
  const { t } = useTranslation()
  return (
    <Box sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      bgcolor: 'background.default'
    }}>
      <Card sx={{ p: 4, textAlign: 'center', maxWidth: 480 }}>
        <Box sx={{ mx: 'auto', mb: 2 }}>
          <CircularProgress size={48} />
        </Box>
        <Box component="h2" sx={{ fontSize: 20, fontWeight: 600, mb: 1 }}>
          {t('dashboard.connecting', 'Connecting to Server')}
        </Box>
        <Box component="p" sx={{ fontSize: 14, color: 'text.secondary' }}>
          {t('dashboard.checkNotifications', 'Check notifications for connection status updates.')}
        </Box>
      </Card>
    </Box>
  )
}

interface DashboardHeaderProps {
  healthStatus: { status: string } | null
  refreshing: boolean
  onRefresh: () => void
}

function DashboardHeader({
  healthStatus,
  refreshing,
  onRefresh
}: DashboardHeaderProps) {
  const { t } = useTranslation()

  return (
    <PageHeader
      title={t('dashboard.title')}
      actions={
        <Stack direction="row" spacing={1} alignItems="center">
          <Button
            onClick={onRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw style={{ width: 12, height: 12 }} className={refreshing ? 'animate-spin' : ''} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('common.refresh')}
          </Button>

          {healthStatus && (
            <Box
              sx={{
                px: 1.5,
                py: 0.25,
                minHeight: 26,
                display: 'flex',
                alignItems: 'center',
                borderRadius: 1,
                border: 1,
                borderColor: healthStatus.status === 'healthy' ? 'success.main' : 'error.main',
                color: healthStatus.status === 'healthy' ? 'success.main' : 'error.main',
                fontSize: '0.7rem',
                fontWeight: 500
              }}
            >
              {healthStatus.status === 'healthy' ? t('dashboard.healthy', 'Healthy') : t('dashboard.unhealthy', 'Unhealthy')}
            </Box>
          )}
        </Stack>
      }
    />
  )
}

function DashboardLoadingSkeleton() {
  return (
    <Stack spacing={3}>
      {/* Header skeleton */}
      <Box>
        <Skeleton sx={{ height: 28, width: 144, mb: 1 }} />
        <Skeleton sx={{ height: 16, width: 256 }} />
      </Box>

      {/* Stats skeleton */}
      <Grid container spacing={2}>
        {[1, 2, 3, 4].map((i) => (
          <Grid size={{ xs: 6, lg: 3 }} key={i}>
            <SkeletonStat />
          </Grid>
        ))}
      </Grid>

      {/* Main content skeleton */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card sx={{ p: 2.5 }}>
            <Skeleton sx={{ height: 20, width: 128, mb: 3 }} />
            <Stack direction="row" spacing={4} justifyContent="space-around">
              {[1, 2, 3].map((i) => (
                <Stack key={i} alignItems="center">
                  <Skeleton sx={{ width: 96, height: 96, borderRadius: '50%', mb: 1.5 }} />
                  <Skeleton sx={{ height: 16, width: 48 }} />
                </Stack>
              ))}
            </Stack>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card sx={{ p: 2.5 }}>
            <Skeleton sx={{ height: 20, width: 80, mb: 2 }} />
            <Stack spacing={1.5}>
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} sx={{ height: 56, borderRadius: 1 }} />
              ))}
            </Stack>
          </Card>
        </Grid>
      </Grid>

      {/* Activity skeleton */}
      <Card sx={{ p: 2.5 }}>
        <Skeleton sx={{ height: 20, width: 128, mb: 2.5 }} />
        <Stack spacing={1.5}>
          {[1, 2, 3, 4].map((i) => (
            <Stack key={i} direction="row" spacing={1.5} alignItems="center">
              <Skeleton sx={{ width: 32, height: 32, borderRadius: 1 }} />
              <Box sx={{ flex: 1 }}>
                <Skeleton sx={{ height: 16, width: 192, mb: 0.5 }} />
                <Skeleton sx={{ height: 12, width: 96 }} />
              </Box>
            </Stack>
          ))}
        </Stack>
      </Card>
    </Stack>
  )
}
