/**
 * Servers Table Column Definitions
 *
 * Column configurations for the ServersTable DataTable.
 */

import { Wifi, Settings, Trash2, Terminal, Unplug, RefreshCw, Bot } from 'lucide-react'
import { Box, Stack, Typography, IconButton, Tooltip } from '@mui/material'
import { ColumnDef } from '@/components/ui/DataTable'
import { LinuxIcon, DockerIcon, AgentIcon } from './ServerIcons'
import type { ServerConnection, AgentInfo } from '@/types/server'
import type { TFunction } from 'i18next'

const statusColors: Record<string, string> = {
  connected: '#10b981',
  disconnected: '#f59e0b',
  error: '#ef4444',
  preparing: '#3b82f6'
}

interface ColumnOptions {
  t: TFunction
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
  onInstallDocker: (serverId: string) => void
  installingDocker: string | null
  agentStatuses?: Map<string, AgentInfo | null>
  onInstallAgent?: (serverId: string) => void
  onUninstallAgent?: (serverId: string) => void
  installingAgent: string | null
}

function renderDocker(server: ServerConnection, options: ColumnOptions) {
  const { t, onInstallDocker, installingDocker } = options

  if (server.status !== 'connected') {
    return <Typography variant="body2" color="text.secondary">—</Typography>
  }

  const dockerNotInstalled = !server.system_info?.docker_version ||
    server.system_info.docker_version.toLowerCase() === 'not installed'

  if (dockerNotInstalled) {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <DockerIcon style={{ width: 14, height: 14, color: 'rgba(128,128,128,0.4)' }} />
        <Box
          component="button"
          onClick={(e) => { e.stopPropagation(); onInstallDocker(server.id) }}
          disabled={installingDocker === server.id}
          sx={{
            fontSize: 11, color: 'primary.main', background: 'none', border: 'none',
            cursor: 'pointer', p: 0, textDecoration: 'none',
            '&:hover': { opacity: 0.8 },
            '&:disabled': { opacity: 0.5 }
          }}
        >
          {installingDocker === server.id ? t('servers.installing') : t('servers.install')}
        </Box>
      </Stack>
    )
  }

  return (
    <Stack direction="row" alignItems="center" spacing={0.5}>
      <DockerIcon style={{ width: 14, height: 14, color: '#3b82f6' }} />
      <Typography variant="body2" sx={{ fontSize: 11, color: '#3b82f6' }}>
        {server.system_info?.docker_version}
      </Typography>
    </Stack>
  )
}

function renderAgent(server: ServerConnection, options: ColumnOptions) {
  const { t, agentStatuses, onInstallAgent, installingAgent } = options

  if (server.status !== 'connected') {
    return <Typography variant="body2" color="text.secondary">—</Typography>
  }

  // Check if Docker is installed (required for agent)
  const dockerInstalled = server.system_info?.docker_version &&
    server.system_info.docker_version.toLowerCase() !== 'not installed'

  // Docker not installed - show hint that Docker is required
  if (!dockerInstalled) {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <AgentIcon style={{ width: 14, height: 14, color: 'rgba(128,128,128,0.4)' }} />
        <Typography variant="body2" sx={{ fontSize: 10, color: 'text.disabled' }}>
          {t('agent.requiresDocker')}
        </Typography>
      </Stack>
    )
  }

  // Check actual agent container status from SSH (source of truth)
  const agentContainerRunning = server.system_info?.agent_status === 'running'
  const agentInfo = agentStatuses?.get(server.id) ?? null

  // Agent container not running on server - show install button (ignore stale DB records)
  if (!agentContainerRunning) {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <AgentIcon style={{ width: 14, height: 14, color: 'rgba(128,128,128,0.4)' }} />
        <Box
          component="button"
          onClick={(e) => { e.stopPropagation(); onInstallAgent?.(server.id) }}
          disabled={installingAgent === server.id}
          sx={{
            fontSize: 11, color: 'primary.main', background: 'none', border: 'none',
            cursor: 'pointer', p: 0, textDecoration: 'none',
            '&:hover': { opacity: 0.8 },
            '&:disabled': { opacity: 0.5 }
          }}
        >
          {installingAgent === server.id ? t('servers.installing') : t('servers.install')}
        </Box>
      </Stack>
    )
  }

  // Container running but no DB record or hasn't connected yet - show pending
  if (!agentInfo || (!agentInfo.version && !agentInfo.is_connected)) {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <AgentIcon style={{ width: 14, height: 14, color: '#f59e0b' }} />
        <Typography variant="body2" sx={{ fontSize: 11, color: '#f59e0b' }}>
          {t('agent.status.pending')}
        </Typography>
      </Stack>
    )
  }

  // Agent installed and has connected - show status with version
  const statusColor = agentInfo.is_connected ? '#10b981' : '#f59e0b'
  const statusText = agentInfo.version || (agentInfo.is_connected ? t('agent.live') : t('agent.offline'))

  return (
    <Stack direction="row" alignItems="center" spacing={0.5}>
      <AgentIcon style={{ width: 14, height: 14, color: statusColor }} />
      <Typography variant="body2" sx={{ fontSize: 11, color: statusColor }}>{statusText}</Typography>
    </Stack>
  )
}

function renderStatus(server: ServerConnection, t: TFunction) {
  if (server.status === 'connected') {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <Wifi size={14} color="#10b981" />
        <Typography variant="body2" sx={{ color: '#10b981', fontWeight: 500, fontSize: 12 }}>
          {t('servers.statusLabels.connected')}
        </Typography>
      </Stack>
    )
  }
  return (
    <Stack direction="row" alignItems="center" spacing={0.75}>
      <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: statusColors[server.status] || statusColors.disconnected }} />
      <Typography variant="body2" color="text.secondary" sx={{ fontSize: 12 }}>
        {t(`servers.statusLabels.${server.status === 'disconnected' ? 'offline' : server.status}`)}
      </Typography>
    </Stack>
  )
}

const actionIconSx = {
  p: 0.5,
  bgcolor: 'transparent',
  '&:hover': { bgcolor: 'transparent' },
  '&:focus': { bgcolor: 'transparent' },
  '&:focus-visible': { bgcolor: 'transparent', outline: 'none' },
  '&:active': { bgcolor: 'transparent' },
  '& .MuiTouchRipple-root': { display: 'none' },
}

function renderActions(server: ServerConnection, options: ColumnOptions) {
  const { t, onEdit, onDelete, onConnect, onDisconnect, agentStatuses, onUninstallAgent } = options
  const agentInfo = agentStatuses?.get(server.id) ?? null
  const agentContainerRunning = server.system_info?.agent_status === 'running'
  // Show uninstall if agent record exists OR container is running on server
  const hasAgent = agentInfo !== null || agentContainerRunning

  return (
    <Stack direction="row" spacing={0.5} justifyContent="center">
      {server.status === 'connected' ? (
        onDisconnect && (
          <Tooltip title={t('servers.actions.disconnectFromServer')}>
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDisconnect(server.id) }}
              sx={{ ...actionIconSx, color: 'text.secondary', '&:hover': { bgcolor: 'transparent', color: 'warning.main' } }}>
              <Unplug size={14} />
            </IconButton>
          </Tooltip>
        )
      ) : server.status === 'error' ? (
        <Tooltip title={t('servers.retry')}>
          <IconButton size="small" onClick={(e) => { e.stopPropagation(); onConnect(server.id) }}
            sx={{ ...actionIconSx, color: 'text.secondary', '&:hover': { bgcolor: 'transparent', color: 'primary.main' } }}>
            <RefreshCw size={14} />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title={t('servers.actions.connectToServer')}>
          <IconButton size="small" onClick={(e) => { e.stopPropagation(); onConnect(server.id) }}
            sx={{ ...actionIconSx, color: 'text.secondary', '&:hover': { bgcolor: 'transparent', color: 'success.main' } }}>
            <Terminal size={14} />
          </IconButton>
        </Tooltip>
      )}
      {hasAgent && onUninstallAgent && (
        <Tooltip title={t('agent.actions.uninstallAgent')}>
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); onUninstallAgent(server.id) }}
            sx={{ ...actionIconSx, color: 'text.secondary', '&:hover': { bgcolor: 'transparent', color: 'warning.main' } }}
          >
            <Bot size={14} />
          </IconButton>
        </Tooltip>
      )}
      <Tooltip title={t('servers.actions.editServer')}>
        <IconButton size="small" onClick={(e) => { e.stopPropagation(); onEdit(server) }}
          sx={{ ...actionIconSx, color: 'text.secondary', '&:hover': { bgcolor: 'transparent', color: 'primary.main' } }}>
          <Settings size={14} />
        </IconButton>
      </Tooltip>
      <Tooltip title={t('servers.actions.deleteServer')}>
        <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDelete(server.id) }}
          sx={{ ...actionIconSx, color: 'error.main', '&:hover': { bgcolor: 'transparent', opacity: 0.8 } }}>
          <Trash2 size={14} />
        </IconButton>
      </Tooltip>
    </Stack>
  )
}

export function getColumns(options: ColumnOptions): ColumnDef<ServerConnection>[] {
  const { t } = options
  return [
    {
      id: 'name',
      header: t('servers.columns.name'),
      width: '20%',
      sortable: true,
      render: (server) => <Typography variant="body2" fontWeight={500} noWrap>{server.name}</Typography>
    },
    {
      id: 'host',
      header: t('servers.columns.host'),
      width: '25%',
      sortable: true,
      render: (server) => (
        <Typography variant="body2" color="text.secondary" noWrap sx={{ fontFamily: 'monospace', fontSize: 11 }}>
          {server.username}@{server.host}:{server.port}
        </Typography>
      )
    },
    {
      id: 'os',
      header: t('servers.columns.os'),
      width: '12%',
      sortable: true,
      render: (server) => {
        if (server.status !== 'connected' || !server.system_info?.os) {
          return <Typography variant="body2" color="text.secondary">—</Typography>
        }
        return (
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <LinuxIcon style={{ width: 14, height: 14, color: '#d97706' }} />
            <Typography variant="body2" color="text.secondary" noWrap sx={{ fontSize: 12 }}>
              {server.system_info.os.split(' ')[0]}
            </Typography>
          </Stack>
        )
      }
    },
    { id: 'docker', header: t('servers.columns.docker'), width: '12%', sortable: true, render: (s) => renderDocker(s, options) },
    { id: 'agent', header: t('agent.title'), width: '10%', render: (s) => renderAgent(s, options) },
    { id: 'status', header: t('servers.columns.status'), width: 120, sortable: true, render: (s) => renderStatus(s, t) },
    { id: 'actions', header: t('common.actions'), width: 120, align: 'center', render: (s) => renderActions(s, options) }
  ]
}

export function sortFn(a: ServerConnection, b: ServerConnection, field: string, direction: 'asc' | 'desc') {
  let comparison = 0
  switch (field) {
    case 'status': comparison = a.status.localeCompare(b.status); break
    case 'name': comparison = a.name.localeCompare(b.name); break
    case 'host': comparison = `${a.host}:${a.port}`.localeCompare(`${b.host}:${b.port}`); break
    case 'os': comparison = (a.system_info?.os || '').localeCompare(b.system_info?.os || ''); break
    case 'docker': comparison = (a.system_info?.docker_version || '').localeCompare(b.system_info?.docker_version || ''); break
  }
  return direction === 'asc' ? comparison : -comparison
}
