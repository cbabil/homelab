/**
 * Server Card Component
 *
 * Displays individual server information with status and actions.
 * Clean, modern design matching dashboard card patterns.
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw, Wifi } from 'lucide-react'
import { Box, Stack, Typography } from '@mui/material'
import { LinuxIcon, DockerIcon } from './ServerIcons'
import { ServerConnection, AgentInfo } from '@/types/server'
import { Button } from '@/components/ui/Button'
import { ServerCardActions } from './ServerCardActions'
import { AgentStatusBadge } from './AgentStatusBadge'

interface ServerCardProps {
  server: ServerConnection
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
  onInstallDocker?: (serverId: string) => Promise<void>
  isSelected?: boolean
  onSelect?: (serverId: string) => void
  agentInfo?: AgentInfo | null
  isAgentLoading?: boolean
  onInstallAgent?: () => void
  onUninstallAgent?: () => void
  onRefreshAgent?: () => void
}

interface ServerStatusInfoProps {
  server: ServerConnection
  statusLabelKey: string
  agentInfo?: AgentInfo | null
  isAgentLoading?: boolean
  onInstallAgent?: () => void
  onUninstallAgent?: () => void
  onRefreshAgent?: () => void
  onConnect: (serverId: string) => void
  onInstallDocker?: () => void
  isInstalling: boolean
}

const statusConfig = {
  connected: {
    labelKey: 'servers.statusLabels.online',
    color: '#10b981',
    accentColor: 'linear-gradient(to right, #10b981, #34d399)'
  },
  disconnected: {
    labelKey: 'servers.statusLabels.offline',
    color: '#f59e0b',
    accentColor: 'linear-gradient(to right, #f59e0b, #fbbf24)'
  },
  error: {
    labelKey: 'servers.statusLabels.error',
    color: '#ef4444',
    accentColor: 'linear-gradient(to right, #ef4444, #f87171)'
  },
  preparing: {
    labelKey: 'servers.statusLabels.preparing',
    color: '#3b82f6',
    accentColor: 'linear-gradient(to right, #3b82f6, #60a5fa)'
  }
}

function ServerStatusInfo({
  server, statusLabelKey, agentInfo, isAgentLoading, onInstallAgent,
  onUninstallAgent, onRefreshAgent, onConnect, onInstallDocker, isInstalling
}: ServerStatusInfoProps) {
  const { t } = useTranslation()
  const dockerNotInstalled = !server.system_info?.docker_version ||
    server.system_info.docker_version.toLowerCase() === 'not installed'

  const handleInstallClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onInstallDocker && !isInstalling) await onInstallDocker()
  }

  if (server.status === 'connected' && server.system_info) {
    return (
      <Stack spacing={1}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Stack direction="row" spacing={0.5} alignItems="center">
            <LinuxIcon style={{ width: 14, height: 14, color: '#d97706' }} />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
              {server.system_info.os?.split(' ')[0] || 'Linux'}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <DockerIcon style={{ width: 14, height: 14, color: !dockerNotInstalled ? '#3b82f6' : 'rgba(128,128,128,0.4)' }} />
            {dockerNotInstalled ? (
              <Box
                component="button"
                onClick={handleInstallClick}
                disabled={isInstalling}
                sx={{ fontSize: 10, color: 'primary.main', background: 'none', border: 'none', cursor: 'pointer', p: 0 }}
              >
                {isInstalling ? t('servers.installing') : t('servers.install')}
              </Box>
            ) : (
              <Typography variant="caption" sx={{ fontSize: 10, color: '#3b82f6' }}>
                {server.system_info.docker_version}
              </Typography>
            )}
          </Stack>
          <AgentStatusBadge
            agentInfo={agentInfo ?? null}
            isLoading={isAgentLoading}
            onInstall={onInstallAgent}
            onUninstall={onUninstallAgent}
            onRefresh={onRefreshAgent}
            compact
          />
        </Stack>
      </Stack>
    )
  }

  if (server.status === 'error') {
    return (
      <Stack spacing={1}>
        <Typography variant="caption" color="error.main" sx={{ fontSize: 10 }}>
          {server.error_message || t('servers.connectionFailed')}
        </Typography>
        <Button
          onClick={(e) => { e.stopPropagation(); onConnect(server.id) }}
          variant="outline"
          size="sm"
          leftIcon={<RefreshCw style={{ width: 10, height: 10 }} />}
          sx={{ fontSize: '0.65rem', py: 0.25, px: 1, minHeight: 22, alignSelf: 'flex-start' }}
        >
          {t('servers.retry')}
        </Button>
      </Stack>
    )
  }

  return (
    <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
      {t(statusLabelKey)}
    </Typography>
  )
}

export function ServerCard({
  server, onEdit, onDelete, onConnect, onDisconnect, onInstallDocker,
  isSelected, onSelect, agentInfo, isAgentLoading, onInstallAgent, onUninstallAgent, onRefreshAgent,
}: ServerCardProps) {
  const { t } = useTranslation()
  const [isInstalling, setIsInstalling] = useState(false)
  const status = statusConfig[server.status]

  const handleInstallDocker = async () => {
    if (!onInstallDocker || isInstalling) return
    setIsInstalling(true)
    try {
      await onInstallDocker(server.id)
    } catch (error) {
      console.error('Docker install error:', error)
    } finally {
      setIsInstalling(false)
    }
  }

  const handleCardClick = () => onSelect?.(server.id)

  return (
    <Box
      onClick={handleCardClick}
      sx={{
        position: 'relative', p: 2, width: 260, borderRadius: 2, bgcolor: 'background.paper',
        border: 1, borderColor: isSelected ? 'primary.main' : 'divider',
        cursor: onSelect ? 'pointer' : 'default', transition: 'all 0.15s',
        '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5, pr: 1 }}>
        <Typography variant="body2" fontWeight={600} noWrap sx={{ flexShrink: 1, minWidth: 0 }}>
          {server.name}
        </Typography>
        {server.status === 'connected' ? (
          <Stack direction="row" alignItems="center" spacing={0.5} sx={{ flexShrink: 0 }}>
            <Wifi size={14} color="#10b981" />
            <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 500, fontSize: 11 }}>
              {t('servers.statusLabels.connected')}
            </Typography>
          </Stack>
        ) : (
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: status.color, flexShrink: 0 }} />
        )}
      </Stack>

      <Typography variant="caption" color="text.secondary" noWrap sx={{ display: 'block', mb: 1.5 }}>
        {server.username}@{server.host}:{server.port}
      </Typography>

      <ServerStatusInfo
        server={server}
        statusLabelKey={status.labelKey}
        agentInfo={agentInfo}
        isAgentLoading={isAgentLoading}
        onInstallAgent={onInstallAgent}
        onUninstallAgent={onUninstallAgent}
        onRefreshAgent={onRefreshAgent}
        onConnect={onConnect}
        onInstallDocker={onInstallDocker ? handleInstallDocker : undefined}
        isInstalling={isInstalling}
      />

      <Box onClick={(e) => e.stopPropagation()} sx={{ position: 'absolute', bottom: 8, right: 8 }}>
        <ServerCardActions
          server={server}
          onEdit={onEdit}
          onDelete={onDelete}
          onConnect={onConnect}
          onDisconnect={onDisconnect}
        />
      </Box>
    </Box>
  )
}