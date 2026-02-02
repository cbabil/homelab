/**
 * Dashboard Status Cards Component
 *
 * Status cards displaying system metrics and health information.
 */

import React from 'react'
import { CheckCircle, AlertCircle, Activity, Package, Clock } from 'lucide-react'
import { Box, Card, Typography, Stack, Grid } from '@mui/material'
import { HealthStatus } from '@/types/mcp'

interface DashboardStatusCardsProps {
  healthStatus: HealthStatus | null
}

interface StatusCardData {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  color: string
  accentColor: string
}

export function DashboardStatusCards({ healthStatus }: DashboardStatusCardsProps) {
  const statusCards: StatusCardData[] = [
    {
      title: 'System Status',
      value: healthStatus?.status || 'Unknown',
      icon: healthStatus?.status === 'healthy' ? CheckCircle : AlertCircle,
      color: healthStatus?.status === 'healthy' ? '#10b981' : '#ef4444',
      accentColor: healthStatus?.status === 'healthy' ? 'linear-gradient(to right, #10b981, #34d399)' : 'linear-gradient(to right, #ef4444, #f87171)'
    },
    {
      title: 'Version',
      value: healthStatus?.version || 'N/A',
      icon: Activity,
      color: '#3b82f6',
      accentColor: 'linear-gradient(to right, #3b82f6, #60a5fa)'
    },
    {
      title: 'Components',
      value: healthStatus?.components ? Object.keys(healthStatus.components).length.toString() : '0',
      icon: Package,
      color: '#8b5cf6',
      accentColor: 'linear-gradient(to right, #8b5cf6, #a78bfa)'
    },
    {
      title: 'Last Updated',
      value: healthStatus?.timestamp ? new Date(healthStatus.timestamp).toLocaleTimeString() : 'N/A',
      icon: Clock,
      color: '#f59e0b',
      accentColor: 'linear-gradient(to right, #f59e0b, #fbbf24)'
    }
  ]

  return (
    <Grid container spacing={3}>
      {statusCards.map((card) => (
        <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={card.title}>
          <Card
            sx={{
              position: 'relative',
              p: 2.5,
              overflow: 'hidden',
              transition: 'all 0.2s',
              '&:hover': {
                boxShadow: 4,
                transform: 'translateY(-2px)'
              }
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
                background: card.accentColor
              }}
            />

            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary" fontWeight={500} sx={{ mb: 0.5 }}>
                  {card.title}
                </Typography>
                <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5, letterSpacing: '-0.02em', textTransform: 'capitalize' }}>
                  {card.value}
                </Typography>
              </Box>
              <card.icon className="w-5 h-5" style={{ color: card.color }} />
            </Stack>
          </Card>
        </Grid>
      ))}
    </Grid>
  )
}