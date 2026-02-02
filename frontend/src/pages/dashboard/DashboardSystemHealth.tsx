/**
 * Dashboard System Health Component
 *
 * System health status panel showing overall health information.
 */

import { Activity } from 'lucide-react'
import { Box, Card, Typography, Stack } from '@mui/material'
import { HealthStatus } from '@/types/mcp'

interface DashboardSystemHealthProps {
  healthStatus: HealthStatus | null
}

export function DashboardSystemHealth({ healthStatus }: DashboardSystemHealthProps) {
  return (
    <Card sx={{ p: 2.5 }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 3 }}>
        <Activity className="w-4 h-4" style={{ color: '#10b981' }} />
        <Typography variant="body2" fontWeight={600}>
          System Health
        </Typography>
      </Stack>

      <Stack spacing={2}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ p: 1.5, borderRadius: 1, bgcolor: 'action.hover' }}
        >
          <Typography variant="body2" fontWeight={500}>
            Overall Status
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: healthStatus?.status === 'healthy' ? 'success.main' : 'error.main'
              }}
            />
            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
              {healthStatus?.status || 'Unknown'}
            </Typography>
          </Stack>
        </Stack>

        <Typography variant="body2" color="text.secondary">
          All systems are running normally. Last health check completed successfully.
        </Typography>
      </Stack>
    </Card>
  )
}