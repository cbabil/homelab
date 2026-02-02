/**
 * Dashboard Stats Component
 *
 * Displays key metrics in a clean, modern card layout.
 */

import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Server, Package, Play, AlertCircle } from 'lucide-react'
import { Box, Card, Typography, Stack, Grid } from '@mui/material'
import { DashboardSummary } from '@/types/mcp'
import { AgentInfo } from '@/types/server'
import { AgentIcon } from '@/components/servers/ServerIcons'

interface DashboardStatsProps {
  data: DashboardSummary | null
  agentStatuses?: Map<string, AgentInfo | null>
}

interface QuickLink {
  label: string
  onClick: () => void
}

interface StatCardProps {
  title: string
  value: number
  subtitle: string
  icon: React.ReactNode
  accentColor: string
  onClick?: () => void
  links?: QuickLink[]
}

function StatCard({ title, value, subtitle, icon, accentColor, onClick, links }: StatCardProps) {
  return (
    <Card
      sx={{
        position: 'relative',
        p: 2,
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Accent line */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 4,
          background: accentColor
        }}
      />

      <Box
        onClick={onClick}
        sx={{
          cursor: onClick ? 'pointer' : 'default',
          '&:hover .stat-value': onClick ? { color: 'primary.main' } : {}
        }}
      >
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary" fontWeight={500} sx={{ mb: 0.25 }}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700} className="stat-value" sx={{ mb: 0.25, letterSpacing: '-0.02em', transition: 'color 0.15s' }}>
              {value}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
              {subtitle}
            </Typography>
          </Box>
          {icon}
        </Stack>
      </Box>

      {links && links.length > 0 && (
        <Stack direction="row" spacing={1.5} sx={{ mt: 'auto', pt: 1.5 }}>
          {links.map((link, index) => (
            <Typography
              key={index}
              component="button"
              onClick={(e) => { e.stopPropagation(); link.onClick(); }}
              sx={{
                fontSize: 10,
                color: 'primary.main',
                background: 'none',
                border: 'none',
                p: 0,
                cursor: 'pointer',
                '&:hover': { textDecoration: 'underline' }
              }}
            >
              {link.label}
            </Typography>
          ))}
        </Stack>
      )}
    </Card>
  )
}

export function DashboardStats({ data, agentStatuses }: DashboardStatsProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const onlineServers = data?.online_servers ?? 0
  const offlineServers = data?.offline_servers ?? 0
  const totalServers = data?.total_servers ?? 0
  const runningApps = data?.running_apps ?? 0
  const stoppedApps = data?.stopped_apps ?? 0
  const errorApps = data?.error_apps ?? 0
  const totalApps = data?.total_apps ?? 0
  const issues = stoppedApps + errorApps

  // Calculate agent health counts
  const agentCounts = useMemo(() => {
    const counts = { healthy: 0, degraded: 0, offline: 0, total: 0 }
    if (!agentStatuses) return counts

    agentStatuses.forEach((agent) => {
      if (!agent) return
      counts.total++
      if (agent.status === 'connected' && agent.is_connected) {
        counts.healthy++
      } else if (agent.status === 'disconnected' || !agent.is_connected) {
        counts.offline++
      } else {
        counts.degraded++
      }
    })
    return counts
  }, [agentStatuses])

  const agentIssues = agentCounts.degraded + agentCounts.offline

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 6, md: 4, xl: 2.4 }}>
        <StatCard
          title={t('nav.servers')}
          value={totalServers}
          subtitle={totalServers > 0 ? `${onlineServers} online, ${offlineServers} offline` : t('dashboard.noServers')}
          icon={<Server className="w-5 h-5" style={{ color: '#3b82f6' }} />}
          accentColor="linear-gradient(to right, #3b82f6, #60a5fa)"
          onClick={() => navigate('/servers')}
          links={[
            { label: t('common.viewAll'), onClick: () => navigate('/servers') },
            { label: t('common.add'), onClick: () => navigate('/servers?action=add') }
          ]}
        />
      </Grid>

      <Grid size={{ xs: 6, md: 4, xl: 2.4 }}>
        <StatCard
          title={t('nav.applications')}
          value={totalApps}
          subtitle={totalApps > 0 ? `${runningApps} running, ${stoppedApps} stopped` : t('applications.noApplications')}
          icon={<Package className="w-5 h-5" style={{ color: '#8b5cf6' }} />}
          accentColor="linear-gradient(to right, #8b5cf6, #a78bfa)"
          onClick={() => navigate('/applications')}
          links={[
            { label: t('common.viewAll'), onClick: () => navigate('/applications') },
            { label: t('nav.marketplace'), onClick: () => navigate('/marketplace') }
          ]}
        />
      </Grid>

      <Grid size={{ xs: 6, md: 4, xl: 2.4 }}>
        <StatCard
          title={t('dashboard.running')}
          value={runningApps}
          subtitle={runningApps > 0 ? t('dashboard.allSystemsOperational', 'All systems operational') : t('dashboard.noRunningApps', 'No running applications')}
          icon={<Play className="w-5 h-5" style={{ color: '#10b981' }} />}
          accentColor="linear-gradient(to right, #10b981, #34d399)"
          onClick={() => navigate('/applications?status=running')}
          links={[
            { label: t('common.viewAll'), onClick: () => navigate('/applications?status=running') }
          ]}
        />
      </Grid>

      <Grid size={{ xs: 6, md: 4, xl: 2.4 }}>
        <StatCard
          title={t('dashboard.issues', 'Issues')}
          value={issues}
          subtitle={
            errorApps > 0
              ? `${errorApps} error, ${stoppedApps} stopped`
              : issues > 0
                ? `${stoppedApps} stopped`
                : t('dashboard.allClear', 'All clear')
          }
          icon={<AlertCircle className="w-5 h-5" style={{ color: issues > 0 ? '#f59e0b' : '#10b981' }} />}
          accentColor={issues > 0 ? 'linear-gradient(to right, #f59e0b, #fbbf24)' : 'linear-gradient(to right, #10b981, #34d399)'}
          onClick={() => navigate('/applications?status=issues')}
          links={issues > 0 ? [
            { label: t('dashboard.viewIssues', 'View issues'), onClick: () => navigate('/applications?status=issues') }
          ] : undefined}
        />
      </Grid>

      <Grid size={{ xs: 6, md: 4, xl: 2.4 }}>
        <StatCard
          title={t('dashboard.agentHealth')}
          value={agentCounts.total}
          subtitle={
            agentCounts.total === 0
              ? t('dashboard.noAgentsInstalled')
              : agentIssues > 0
                ? `${agentCounts.healthy} healthy, ${agentIssues} issues`
                : t('dashboard.allSystemsOperational')
          }
          icon={<AgentIcon style={{ width: 20, height: 20, color: agentIssues > 0 ? '#f59e0b' : '#6366f1' }} />}
          accentColor={agentIssues > 0 ? 'linear-gradient(to right, #f59e0b, #fbbf24)' : 'linear-gradient(to right, #6366f1, #818cf8)'}
          onClick={() => navigate('/servers')}
          links={agentCounts.total > 0 ? [
            { label: t('common.viewAll'), onClick: () => navigate('/servers') },
            { label: t('audit.viewAll'), onClick: () => navigate('/settings?tab=security') }
          ] : undefined}
        />
      </Grid>
    </Grid>
  )
}
