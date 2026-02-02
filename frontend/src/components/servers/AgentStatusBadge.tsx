/**
 * Agent Status Badge Component
 *
 * Displays agent connection status with visual indicators.
 */

import { Stack, Typography, Box, Tooltip, CircularProgress } from '@mui/material'
import { RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { AgentInfo } from '@/types/server'
import { AgentIcon } from './ServerIcons'

interface AgentStatusBadgeProps {
  agentInfo: AgentInfo | null
  isLoading?: boolean
  onInstall?: () => void
  onUninstall?: () => void
  onRefresh?: () => void
  compact?: boolean
}

const statusConfig = {
  connected: {
    labelKey: 'agent.status.connected',
    color: '#10b981',
    useAgentIcon: true,
  },
  disconnected: {
    labelKey: 'agent.status.disconnected',
    color: '#f59e0b',
    useAgentIcon: true,
  },
  pending: {
    labelKey: 'agent.status.pending',
    color: '#6b7280',
    useAgentIcon: true,
  },
  updating: {
    labelKey: 'agent.status.updating',
    color: '#3b82f6',
    useAgentIcon: false,
    icon: RefreshCw,
  },
}

export function AgentStatusBadge({
  agentInfo,
  isLoading,
  onInstall,
  onUninstall,
  onRefresh,
  compact = false,
}: AgentStatusBadgeProps) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <CircularProgress size={12} />
        {!compact && (
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
            {t('common.loading')}
          </Typography>
        )}
      </Stack>
    )
  }

  // No agent installed - style matches Docker column
  if (!agentInfo) {
    return (
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <AgentIcon style={{ width: 14, height: 14, color: 'rgba(128,128,128,0.4)' }} />
        {onInstall && (
          <Box
            component="button"
            onClick={(e) => {
              e.stopPropagation()
              onInstall()
            }}
            sx={{
              fontSize: 11,
              color: 'primary.main',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              p: 0,
              textDecoration: 'none',
              '&:hover': { opacity: 0.8 }
            }}
          >
            {t('servers.install')}
          </Box>
        )}
      </Stack>
    )
  }

  const status = statusConfig[agentInfo.status] || statusConfig.disconnected

  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="caption" display="block">
            {t(status.labelKey)}
          </Typography>
          {agentInfo.version && (
            <Typography variant="caption" display="block">
              {t('agent.version')}: {agentInfo.version}
            </Typography>
          )}
          {agentInfo.last_seen && (
            <Typography variant="caption" display="block">
              {t('agent.lastSeen')}: {new Date(agentInfo.last_seen).toLocaleString()}
            </Typography>
          )}
          {onUninstall && (
            <Box
              component="button"
              onClick={(e) => {
                e.stopPropagation()
                onUninstall()
              }}
              sx={{
                mt: 1,
                fontSize: 11,
                color: 'error.light',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                p: 0,
                '&:hover': { textDecoration: 'underline' }
              }}
            >
              {t('agent.actions.uninstallAgent')}
            </Box>
          )}
        </Box>
      }
    >
      <Stack
        direction="row"
        spacing={0.5}
        alignItems="center"
        onClick={(e) => {
          e.stopPropagation()
          onRefresh?.()
        }}
        sx={{
          cursor: onRefresh ? 'pointer' : 'default',
          '&:hover': onRefresh ? { opacity: 0.8 } : {},
        }}
      >
        {status.useAgentIcon ? (
          <AgentIcon style={{ width: 14, height: 14, color: status.color }} />
        ) : (
          <RefreshCw
            size={14}
            color={status.color}
            style={{ animation: 'spin 1s linear infinite' }}
          />
        )}
        {!compact && (
          <Typography
            variant="caption"
            sx={{ fontSize: 11, color: status.color, fontWeight: 500 }}
          >
            {agentInfo.version || (agentInfo.is_connected ? t('agent.live') : t('agent.offline'))}
          </Typography>
        )}
      </Stack>
    </Tooltip>
  )
}
