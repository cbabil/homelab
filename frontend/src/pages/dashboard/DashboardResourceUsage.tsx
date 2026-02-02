/**
 * Dashboard Resource Usage Component
 *
 * Displays system resource metrics with modern circular progress indicators.
 */

import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Cpu, MemoryStick, HardDrive, Server } from 'lucide-react'
import { Box, Card, Typography, Stack } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { DashboardSummary } from '@/types/mcp'

interface DashboardResourceUsageProps {
  data: DashboardSummary | null
}

interface ResourceGaugeProps {
  label: string
  value: number
  icon: React.ReactNode
  color: string
  statusLabels: { critical: string; high: string; normal: string }
}

function ResourceGauge({ label, value, icon, color, statusLabels }: ResourceGaugeProps) {
  const percentage = Math.min(Math.max(value, 0), 100)
  const circumference = 2 * Math.PI * 24
  const strokeDashoffset = circumference - (percentage / 100) * circumference
  const status = percentage >= 90 ? 'critical' : percentage >= 70 ? 'warning' : 'healthy'

  return (
    <Stack direction="row" spacing={1.5} alignItems="center">
      <Box sx={{ position: 'relative', width: 56, height: 56 }}>
        <svg
          style={{ width: 56, height: 56, transform: 'rotate(-90deg)' }}
          viewBox="0 0 56 56"
        >
          <circle
            cx="28"
            cy="28"
            r="24"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            style={{ color: 'var(--mui-palette-action-hover)' }}
          />
          <circle
            cx="28"
            cy="28"
            r="24"
            fill="none"
            stroke={color}
            strokeWidth="4"
            strokeLinecap="round"
            style={{
              strokeDasharray: circumference,
              strokeDashoffset,
              transition: 'stroke-dashoffset 0.5s ease'
            }}
          />
        </svg>
        <Box sx={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Typography variant="body2" fontWeight={700}>
            {percentage.toFixed(0)}%
          </Typography>
        </Box>
      </Box>
      <Stack spacing={0}>
        <Stack direction="row" spacing={0.5} alignItems="center">
          {icon}
          <Typography variant="body2" fontWeight={500}>
            {label}
          </Typography>
        </Stack>
        <Typography
          variant="caption"
          sx={{
            color: status === 'critical' ? 'error.main' :
                   status === 'warning' ? 'warning.main' :
                   'success.main'
          }}
        >
          {status === 'critical' ? statusLabels.critical : status === 'warning' ? statusLabels.high : statusLabels.normal}
        </Typography>
      </Stack>
    </Stack>
  )
}

export function DashboardResourceUsage({ data }: DashboardResourceUsageProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const hasData = data && (data.avg_cpu_percent > 0 || data.avg_memory_percent > 0 || data.avg_disk_percent > 0)

  const statusLabels = {
    critical: t('dashboard.resourceStatus.critical'),
    high: t('dashboard.resourceStatus.high'),
    normal: t('dashboard.resourceStatus.normal')
  }

  return (
    <Card sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Cpu className="w-4 h-4" style={{ color: '#10b981' }} />
          <Typography variant="body2" fontWeight={600}>
            {t('dashboard.resourceUsage')}
          </Typography>
        </Stack>
        <Typography variant="caption" color="text.secondary">
          {t('dashboard.averageAcrossServers')}
        </Typography>
      </Stack>

      {hasData ? (
        <Stack direction="row" spacing={6} justifyContent="space-around" alignItems="center" sx={{ flex: 1 }}>
          <ResourceGauge
            label={t('dashboard.cpu')}
            value={data?.avg_cpu_percent ?? 0}
            icon={<Cpu className="w-4 h-4" style={{ color: '#3b82f6' }} />}
            color="#3b82f6"
            statusLabels={statusLabels}
          />
          <ResourceGauge
            label={t('dashboard.memory')}
            value={data?.avg_memory_percent ?? 0}
            icon={<MemoryStick className="w-4 h-4" style={{ color: '#8b5cf6' }} />}
            color="#8b5cf6"
            statusLabels={statusLabels}
          />
          <ResourceGauge
            label={t('dashboard.disk')}
            value={data?.avg_disk_percent ?? 0}
            icon={<HardDrive className="w-4 h-4" style={{ color: '#f59e0b' }} />}
            color="#f59e0b"
            statusLabels={statusLabels}
          />
        </Stack>
      ) : (
        <Stack alignItems="center" justifyContent="center" sx={{ flex: 1, textAlign: 'center' }}>
          <Server className="w-8 h-8" style={{ color: 'var(--mui-palette-text-secondary)', marginBottom: 12 }} />
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('dashboard.noMetricsAvailable')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('dashboard.connectServersToView')}
          </Typography>
          <Button
            onClick={() => navigate('/servers')}
            variant="primary"
            size="sm"
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {t('dashboard.manageServers')}
          </Button>
        </Stack>
      )}
    </Card>
  )
}
