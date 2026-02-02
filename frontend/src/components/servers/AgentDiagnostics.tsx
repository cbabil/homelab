/**
 * Agent Diagnostics Component
 *
 * Displays detailed agent connection diagnostics including health status,
 * ping latency, available execution methods, and version information.
 */

import React, { useState, useCallback } from 'react'
import { Box, Typography, Stack, CircularProgress, Chip, IconButton, Tooltip, Paper } from '@mui/material'
import { RefreshCw, Wifi, WifiOff, Clock, Zap, Terminal, AlertCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAgentStatus } from '@/hooks/useAgentStatus'
import { useCommandExecution } from '@/hooks/useCommandExecution'
import type { AgentHealthInfo, AgentVersionInfo, ExecutionMethodsInfo } from '@/types/server'

interface AgentDiagnosticsProps {
  serverId: string
  serverName: string
  compact?: boolean
}

function DiagnosticRow({ label, value, icon }: { label: string; value: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" py={0.5}>
      <Stack direction="row" alignItems="center" spacing={1}>
        {icon && <Box sx={{ color: 'text.secondary' }}>{icon}</Box>}
        <Typography variant="body2" color="text.secondary">{label}</Typography>
      </Stack>
      <Box>{value}</Box>
    </Stack>
  )
}

const getHealthColor = (status?: string) => {
  if (status === 'healthy') return 'success'
  if (status === 'degraded') return 'warning'
  if (status === 'offline') return 'error'
  return 'default'
}

const getMethodIcon = (method: string) => {
  if (method === 'agent') return <Zap size={14} />
  if (method === 'ssh') return <Terminal size={14} />
  return <AlertCircle size={14} />
}

export function AgentDiagnostics({ serverId, serverName, compact = false }: AgentDiagnosticsProps) {
  const { t } = useTranslation()
  const { checkAgentHealth, pingAgent, checkAgentVersion } = useAgentStatus()
  const { getExecutionMethods } = useCommandExecution()

  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState<AgentHealthInfo | null>(null)
  const [version, setVersion] = useState<AgentVersionInfo | null>(null)
  const [methods, setMethods] = useState<ExecutionMethodsInfo | null>(null)
  const [pingLatency, setPingLatency] = useState<number | null>(null)

  const runDiagnostics = useCallback(async () => {
    setIsLoading(true)
    try {
      const [healthResult, versionResult, methodsResult, pingResult] = await Promise.all([
        checkAgentHealth(serverId), checkAgentVersion(serverId), getExecutionMethods(serverId), pingAgent(serverId, 5),
      ])
      setHealth(healthResult)
      setVersion(versionResult)
      setMethods(methodsResult)
      setPingLatency(pingResult?.latency_ms ?? null)
    } finally {
      setIsLoading(false)
    }
  }, [serverId, checkAgentHealth, checkAgentVersion, getExecutionMethods, pingAgent])

  if (compact) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <Tooltip title={t('agent.actions.checkHealth')}>
          <IconButton size="small" onClick={runDiagnostics} disabled={isLoading}>
            {isLoading ? <CircularProgress size={16} /> : <RefreshCw size={16} />}
          </IconButton>
        </Tooltip>
        {health && <Chip size="small" label={t(`agent.health.${health.health}`)} color={getHealthColor(health.health)} icon={health.is_connected ? <Wifi size={12} /> : <WifiOff size={12} />} />}
        {pingLatency !== null && <Typography variant="caption" color="text.secondary">{pingLatency}ms</Typography>}
      </Stack>
    )
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="subtitle2" fontWeight={600}>{t('agent.diagnostics.title')} - {serverName}</Typography>
        <Tooltip title={t('agent.diagnostics.runDiagnostics')}>
          <IconButton size="small" onClick={runDiagnostics} disabled={isLoading}>
            {isLoading ? <CircularProgress size={18} /> : <RefreshCw size={18} />}
          </IconButton>
        </Tooltip>
      </Stack>
      {!health && !isLoading && <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>{t('agent.diagnostics.clickToRun')}</Typography>}
      {health && (
        <Stack spacing={1} divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
          <Box>
            <Typography variant="caption" color="text.secondary" fontWeight={600}>{t('agent.diagnostics.connectionStatus')}</Typography>
            <DiagnosticRow label={t('agent.health.title')} icon={health.is_connected ? <Wifi size={14} /> : <WifiOff size={14} />} value={<Chip size="small" label={t(`agent.health.${health.health}`)} color={getHealthColor(health.health)} />} />
            <DiagnosticRow label={t('agent.diagnostics.connected')} value={<Typography variant="body2">{health.is_connected ? t('common.yes') : t('common.no')}</Typography>} />
            {pingLatency !== null && <DiagnosticRow label={t('agent.diagnostics.latency')} icon={<Clock size={14} />} value={<Typography variant="body2">{pingLatency}ms</Typography>} />}
            {health.last_seen && <DiagnosticRow label={t('agent.lastSeen')} value={<Typography variant="body2">{new Date(health.last_seen).toLocaleString()}</Typography>} />}
          </Box>
          {version && (
            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>{t('agent.diagnostics.versionInfo')}</Typography>
              <DiagnosticRow label={t('agent.version.current', { version: '' })} value={<Typography variant="body2">{version.current_version}</Typography>} />
              <DiagnosticRow label={t('agent.version.latest', { version: '' })} value={<Typography variant="body2">{version.latest_version}</Typography>} />
              <DiagnosticRow label={t('agent.version.updateAvailable')} value={<Chip size="small" label={version.update_available ? t('common.yes') : t('common.no')} color={version.update_available ? 'warning' : 'default'} />} />
            </Box>
          )}
          {methods && (
            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>{t('agent.diagnostics.executionMethods')}</Typography>
              <DiagnosticRow label={t('agent.diagnostics.availableMethods')} value={<Stack direction="row" spacing={0.5}>{methods.methods.map((m) => <Chip key={m} size="small" label={m.toUpperCase()} icon={getMethodIcon(m)} color={m === methods.preferred_method ? 'primary' : 'default'} />)}</Stack>} />
              <DiagnosticRow label={t('agent.diagnostics.preferredMethod')} value={<Typography variant="body2">{methods.preferred_method?.toUpperCase() || '-'}</Typography>} />
            </Box>
          )}
        </Stack>
      )}
    </Paper>
  )
}
