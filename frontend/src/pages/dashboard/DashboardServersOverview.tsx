/**
 * Dashboard Servers Overview Component
 *
 * Shows a compact view of server status with quick access.
 */

import { useNavigate } from 'react-router-dom'
import { Server, HardDrive, Plus, ChevronRight } from 'lucide-react'
import { Box, Card, Typography, Stack } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { ServerConnection } from '@/types/server'

interface DashboardServersOverviewProps {
  servers: ServerConnection[]
}

function ServerRow({ server }: { server: ServerConnection }) {
  const navigate = useNavigate()
  const isOnline = server.status === 'connected'

  return (
    <Box
      onClick={() => navigate('/servers')}
      component="button"
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        py: 1,
        textAlign: 'left',
        width: '100%',
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        '&:hover': {
          '& .server-name': { color: 'primary.main' },
          '& .chevron-icon': { opacity: 1 }
        }
      }}
    >
      {/* Status dot */}
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          bgcolor: isOnline ? '#10b981' : 'grey.500',
          flexShrink: 0
        }}
      />
      {/* Server info */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" fontWeight={500} noWrap className="server-name" sx={{ transition: 'color 0.15s' }}>
          {server.name}
        </Typography>
        <Typography variant="caption" color="text.secondary" noWrap>
          {server.host}
        </Typography>
      </Box>
      {/* Docker icon */}
      {server.docker_installed && (
        <HardDrive className="w-3.5 h-3.5" style={{ color: '#3b82f6', flexShrink: 0 }} />
      )}
      {/* Chevron */}
      <ChevronRight className="w-4 h-4 chevron-icon" style={{ color: 'var(--mui-palette-text-secondary)', opacity: 0, transition: 'opacity 0.15s', flexShrink: 0 }} />
    </Box>
  )
}

export function DashboardServersOverview({ servers }: DashboardServersOverviewProps) {
  const navigate = useNavigate()
  const displayServers = servers.slice(0, 4)
  const hasMore = servers.length > 4
  const onlineCount = servers.filter(s => s.status === 'connected').length

  return (
    <Card sx={{ p: 2.5, height: '100%' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Server className="w-4 h-4" style={{ color: '#3b82f6' }} />
          <Box>
            <Typography variant="body2" fontWeight={600}>
              Servers
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {onlineCount} of {servers.length} online
            </Typography>
          </Box>
        </Stack>
        <Button
          onClick={() => navigate('/servers')}
          variant="ghost"
          size="sm"
          sx={{ fontSize: 12, color: 'text.secondary', '&:hover': { color: 'text.primary' } }}
        >
          View all
        </Button>
      </Stack>

      {servers.length > 0 ? (
        <Stack spacing={0} divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
          {displayServers.map((server) => (
            <ServerRow key={server.id} server={server} />
          ))}
          {hasMore && (
            <Button
              onClick={() => navigate('/servers')}
              variant="ghost"
              size="sm"
              sx={{
                width: '100%',
                p: 1,
                fontSize: 12,
                color: 'text.secondary',
                textAlign: 'center',
                '&:hover': {
                  color: 'text.primary',
                  bgcolor: 'action.hover'
                }
              }}
            >
              +{servers.length - 4} more servers
            </Button>
          )}
        </Stack>
      ) : (
        <Stack alignItems="center" justifyContent="center" sx={{ py: 4, textAlign: 'center' }}>
          <Server className="w-8 h-8" style={{ color: 'var(--mui-palette-text-secondary)', marginBottom: 12 }} />
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            No servers configured
          </Typography>
          <Button
            onClick={() => navigate('/servers')}
            variant="primary"
            size="sm"
            sx={{ fontSize: 12, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 0.75 }}
          >
            <Plus className="w-3.5 h-3.5" />
            Add Server
          </Button>
        </Stack>
      )}
    </Card>
  )
}
