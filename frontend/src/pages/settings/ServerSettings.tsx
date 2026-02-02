/**
 * Server Settings Component
 *
 * SSH connection settings, MCP server configuration, Agent settings, and Docker status.
 * Single card with sub-tabs for each section.
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Box, Stack, Select, MenuItem, FormControl, Alert, Typography, Divider } from '@mui/material'
import { Toggle, SettingRow } from './components'
import { Button } from '@/components/ui/Button'

const selectStyles = {
  height: 32, minWidth: 80, fontSize: '0.75rem', borderRadius: 1, bgcolor: 'transparent',
  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.23)' },
  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255, 255, 255, 0.4)' },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: 'primary.main', borderWidth: 1 },
  '& .MuiSelect-select': { py: 0.5, px: 1 }
}
const menuProps = { PaperProps: { sx: { '& .MuiMenuItem-root': { fontSize: '0.75rem' } } } }

// SSH Settings Sub-component
function SSHSection({ connectionTimeout, retryCount, autoRetry, onConnectionTimeoutChange, onRetryCountChange, onAutoRetryChange }: {
  connectionTimeout: string; retryCount: string; autoRetry: boolean
  onConnectionTimeoutChange: (v: string) => void; onRetryCountChange: (v: string) => void; onAutoRetryChange: (v: boolean) => void
}) {
  const { t } = useTranslation()
  return (
    <Box>
      <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>{t('settings.serverSettings.connectionSettings')}</Typography>
      <Typography variant="caption" color="text.secondary">{t('settings.serverSettings.connectionSettingsDescription')}</Typography>
      <Stack spacing={0.5}>
        <SettingRow label={t('settings.serverSettings.timeout')}>
          <FormControl size="small">
            <Select value={connectionTimeout} onChange={(e) => onConnectionTimeoutChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}>
              <MenuItem value="10">10s</MenuItem><MenuItem value="30">30s</MenuItem><MenuItem value="60">1m</MenuItem>
            </Select>
          </FormControl>
        </SettingRow>
        <SettingRow label={t('settings.serverSettings.retryCount')}>
          <FormControl size="small">
            <Select value={retryCount} onChange={(e) => onRetryCountChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}>
              <MenuItem value="1">1</MenuItem><MenuItem value="2">2</MenuItem><MenuItem value="3">3</MenuItem><MenuItem value="5">5</MenuItem><MenuItem value="10">10</MenuItem>
            </Select>
          </FormControl>
        </SettingRow>
        <SettingRow label={t('settings.serverSettings.autoRetry')}>
          <Toggle checked={autoRetry} onChange={onAutoRetryChange} aria-label={t('settings.serverSettings.autoRetry')} />
        </SettingRow>
      </Stack>
    </Box>
  )
}

// MCP Settings Sub-component
function MCPSection({ mcpConfig, isEditingMcpConfig, mcpConfigText, mcpConfigError, mcpConnectionStatus, mcpConnectionError, onMcpConfigEdit, onMcpConfigSave, onMcpConfigCancel, onMcpConnect, onMcpDisconnect, onMcpConfigTextChange }: {
  mcpConfig: Record<string, unknown>; isEditingMcpConfig: boolean; mcpConfigText: string; mcpConfigError: string
  mcpConnectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'; mcpConnectionError: string
  onMcpConfigEdit: () => void; onMcpConfigSave: () => void; onMcpConfigCancel: () => void
  onMcpConnect: () => void; onMcpDisconnect: () => void; onMcpConfigTextChange: (v: string) => void
}) {
  const { t } = useTranslation()
  const statusDot = { width: 8, height: 8, borderRadius: '50%', bgcolor: mcpConnectionStatus === 'connected' ? 'success.main' : mcpConnectionStatus === 'connecting' ? 'warning.main' : mcpConnectionStatus === 'disconnected' ? 'grey.400' : 'error.main', ...(mcpConnectionStatus === 'connecting' && { animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite', '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } } }) }
  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>{t('settings.serverSettings.mcpServerConfiguration')}</Typography>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Box sx={statusDot} />
            <Typography variant="caption" color="text.secondary">
              {mcpConnectionStatus === 'connected' && t('settings.serverSettings.connected')}
              {mcpConnectionStatus === 'connecting' && t('settings.serverSettings.connecting')}
              {mcpConnectionStatus === 'disconnected' && t('settings.serverSettings.disconnected')}
              {mcpConnectionStatus === 'error' && t('settings.serverSettings.connectionError')}
            </Typography>
          </Stack>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1}>
          {mcpConnectionStatus === 'connected' ? (
            <Button variant="destructive" size="sm" onClick={onMcpDisconnect} sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}>{t('settings.serverSettings.disconnect')}</Button>
          ) : (
            <Button variant="outline" size="sm" onClick={onMcpConnect} loading={mcpConnectionStatus === 'connecting'} disabled={mcpConnectionStatus === 'connecting'} sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26, borderColor: mcpConnectionStatus === 'connecting' ? 'warning.main' : 'success.main', color: mcpConnectionStatus === 'connecting' ? 'warning.main' : 'success.main' }}>
              {mcpConnectionStatus === 'connecting' ? t('settings.serverSettings.connecting') : t('settings.serverSettings.connect')}
            </Button>
          )}
          <Button variant={isEditingMcpConfig ? 'outline' : 'primary'} size="sm" onClick={isEditingMcpConfig ? onMcpConfigSave : onMcpConfigEdit} sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26, ...(isEditingMcpConfig && { borderColor: 'info.main', color: 'info.main' }) }}>
            {isEditingMcpConfig ? t('settings.serverSettings.save') : t('settings.serverSettings.edit')}
          </Button>
        </Stack>
      </Stack>
      {mcpConfigError && <Alert severity="error" sx={{ mb: 1, p: 1, fontSize: '0.75rem' }}>{mcpConfigError}</Alert>}
      {mcpConnectionError && <Alert severity="error" sx={{ mb: 1, p: 1, fontSize: '0.75rem' }}><strong>{t('settings.serverSettings.connectionError')}:</strong> {mcpConnectionError}</Alert>}
      {isEditingMcpConfig ? (
        <Stack spacing={0.5}>
          <Box component="textarea" value={mcpConfigText} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onMcpConfigTextChange(e.target.value)} onBlur={onMcpConfigCancel} sx={{ width: '100%', height: '16rem', p: 1.5, fontSize: '0.75rem', fontFamily: 'monospace', border: 1, borderColor: mcpConfigError ? 'error.main' : 'divider', borderRadius: 1, bgcolor: mcpConfigError ? 'error.light' : 'background.default', resize: 'none', '&:focus': { outline: 'none', borderColor: mcpConfigError ? 'error.main' : 'primary.main' } }} placeholder={t('settings.serverSettings.configPlaceholder')} autoFocus />
          <Typography variant="caption" color="text.secondary">{t('settings.serverSettings.configDescription')}</Typography>
        </Stack>
      ) : (
        <Stack spacing={0.5}>
          <Box component="pre" sx={{ width: '100%', height: '16rem', p: 1.5, fontSize: '0.75rem', fontFamily: 'monospace', border: 1, borderColor: 'divider', borderRadius: 1, bgcolor: 'action.hover', overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            <Box component="code" sx={{ color: 'text.primary' }}>{JSON.stringify(mcpConfig, null, 2)}</Box>
          </Box>
          <Typography variant="caption" color="text.secondary">{t('settings.serverSettings.currentConfig')}</Typography>
        </Stack>
      )}
    </Box>
  )
}

// Agent Settings Sub-component
function AgentSection({ preferAgent, agentAutoUpdate, heartbeatInterval, heartbeatTimeout, commandTimeout, onPreferAgentChange, onAgentAutoUpdateChange, onHeartbeatIntervalChange, onHeartbeatTimeoutChange, onCommandTimeoutChange }: {
  preferAgent: boolean; agentAutoUpdate: boolean; heartbeatInterval: string; heartbeatTimeout: string; commandTimeout: string
  onPreferAgentChange: (v: boolean) => void; onAgentAutoUpdateChange: (v: boolean) => void; onHeartbeatIntervalChange: (v: string) => void; onHeartbeatTimeoutChange: (v: string) => void; onCommandTimeoutChange: (v: string) => void
}) {
  const { t } = useTranslation()
  return (
    <Box>
      <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>{t('settings.agent.connectionPreferences')}</Typography>
      <Stack spacing={0.5}>
        <SettingRow label={t('settings.agent.preferAgent')} description={t('settings.agent.preferAgentDescription')}><Toggle checked={preferAgent} onChange={onPreferAgentChange} aria-label={t('settings.agent.preferAgent')} /></SettingRow>
        <SettingRow label={t('settings.agent.commandTimeout')} description={t('settings.agent.commandTimeoutDescription')}>
          <FormControl size="small"><Select value={commandTimeout} onChange={(e) => onCommandTimeoutChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}><MenuItem value="30">30s</MenuItem><MenuItem value="60">1m</MenuItem><MenuItem value="120">2m</MenuItem><MenuItem value="300">5m</MenuItem><MenuItem value="600">10m</MenuItem></Select></FormControl>
        </SettingRow>
      </Stack>
      <Divider sx={{ my: 2 }} />
      <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>{t('settings.agent.healthMonitoring')}</Typography>
      <Stack spacing={0.5}>
        <SettingRow label={t('settings.agent.heartbeatInterval')} description={t('settings.agent.heartbeatIntervalDescription')}>
          <FormControl size="small"><Select value={heartbeatInterval} onChange={(e) => onHeartbeatIntervalChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}><MenuItem value="10">10s</MenuItem><MenuItem value="30">30s</MenuItem><MenuItem value="60">1m</MenuItem><MenuItem value="120">2m</MenuItem></Select></FormControl>
        </SettingRow>
        <SettingRow label={t('settings.agent.heartbeatTimeout')} description={t('settings.agent.heartbeatTimeoutDescription')}>
          <FormControl size="small"><Select value={heartbeatTimeout} onChange={(e) => onHeartbeatTimeoutChange(e.target.value)} size="small" sx={selectStyles} MenuProps={menuProps}><MenuItem value="30">30s</MenuItem><MenuItem value="60">1m</MenuItem><MenuItem value="90">90s</MenuItem><MenuItem value="120">2m</MenuItem><MenuItem value="300">5m</MenuItem></Select></FormControl>
        </SettingRow>
      </Stack>
      <Divider sx={{ my: 2 }} />
      <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>{t('settings.agent.updates')}</Typography>
      <Stack spacing={0.5}><SettingRow label={t('settings.agent.autoUpdate')} description={t('settings.agent.autoUpdateDescription')}><Toggle checked={agentAutoUpdate} onChange={onAgentAutoUpdateChange} aria-label={t('settings.agent.autoUpdate')} /></SettingRow></Stack>
    </Box>
  )
}

interface ServerSettingsProps {
  activeServerTab: string; connectionTimeout: string; retryCount: string; autoRetry: boolean
  mcpConfig: Record<string, unknown>; isEditingMcpConfig: boolean; mcpConfigText: string; mcpConfigError: string
  mcpConnectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'; mcpConnectionError: string
  preferAgent: boolean; agentAutoUpdate: boolean; heartbeatInterval: string; heartbeatTimeout: string; commandTimeout: string
  onActiveServerTabChange: (tab: string) => void; onConnectionTimeoutChange: (v: string) => void; onRetryCountChange: (v: string) => void; onAutoRetryChange: (v: boolean) => void
  onMcpConfigEdit: () => void; onMcpConfigSave: () => void; onMcpConfigCancel: () => void; onMcpConnect: () => void; onMcpDisconnect: () => void; onMcpConfigTextChange: (v: string) => void
  onPreferAgentChange: (v: boolean) => void; onAgentAutoUpdateChange: (v: boolean) => void; onHeartbeatIntervalChange: (v: string) => void; onHeartbeatTimeoutChange: (v: string) => void; onCommandTimeoutChange: (v: string) => void
}

export function ServerSettings({ activeServerTab, connectionTimeout, retryCount, autoRetry, mcpConfig, isEditingMcpConfig, mcpConfigText, mcpConfigError, mcpConnectionStatus, mcpConnectionError, preferAgent, agentAutoUpdate, heartbeatInterval, heartbeatTimeout, commandTimeout, onActiveServerTabChange, onConnectionTimeoutChange, onRetryCountChange, onAutoRetryChange, onMcpConfigEdit, onMcpConfigSave, onMcpConfigCancel, onMcpConnect, onMcpDisconnect, onMcpConfigTextChange, onPreferAgentChange, onAgentAutoUpdateChange, onHeartbeatIntervalChange, onHeartbeatTimeoutChange, onCommandTimeoutChange }: ServerSettingsProps) {
  const { t } = useTranslation()
  const tabBtnStyle = (isActive: boolean) => ({ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26, ...(isActive && { bgcolor: 'background.paper', boxShadow: 1, color: 'primary.main', '&:hover': { bgcolor: 'background.paper' } }) })

  return (
    <Box sx={{ bgcolor: 'background.paper', borderRadius: 2, border: 1, borderColor: 'divider', p: 2, flex: 1 }}>
      <Stack direction="row" sx={{ display: 'flex', gap: 0.5, bgcolor: 'action.hover', p: 0.5, borderRadius: 2, width: 'fit-content', mb: 1.5 }}>
        <Button variant="ghost" size="sm" onClick={() => onActiveServerTabChange('ssh')} sx={tabBtnStyle(activeServerTab === 'ssh')}>{t('settings.serverSettings.ssh')}</Button>
        <Button variant="ghost" size="sm" onClick={() => onActiveServerTabChange('mcp')} sx={tabBtnStyle(activeServerTab === 'mcp')}>{t('settings.serverSettings.mcp')}</Button>
        <Button variant="ghost" size="sm" onClick={() => onActiveServerTabChange('agent')} sx={tabBtnStyle(activeServerTab === 'agent')}>{t('settings.serverSettings.agent')}</Button>
      </Stack>
      {activeServerTab === 'ssh' && <SSHSection connectionTimeout={connectionTimeout} retryCount={retryCount} autoRetry={autoRetry} onConnectionTimeoutChange={onConnectionTimeoutChange} onRetryCountChange={onRetryCountChange} onAutoRetryChange={onAutoRetryChange} />}
      {activeServerTab === 'mcp' && <MCPSection mcpConfig={mcpConfig} isEditingMcpConfig={isEditingMcpConfig} mcpConfigText={mcpConfigText} mcpConfigError={mcpConfigError} mcpConnectionStatus={mcpConnectionStatus} mcpConnectionError={mcpConnectionError} onMcpConfigEdit={onMcpConfigEdit} onMcpConfigSave={onMcpConfigSave} onMcpConfigCancel={onMcpConfigCancel} onMcpConnect={onMcpConnect} onMcpDisconnect={onMcpDisconnect} onMcpConfigTextChange={onMcpConfigTextChange} />}
      {activeServerTab === 'agent' && <AgentSection preferAgent={preferAgent} agentAutoUpdate={agentAutoUpdate} heartbeatInterval={heartbeatInterval} heartbeatTimeout={heartbeatTimeout} commandTimeout={commandTimeout} onPreferAgentChange={onPreferAgentChange} onAgentAutoUpdateChange={onAgentAutoUpdateChange} onHeartbeatIntervalChange={onHeartbeatIntervalChange} onHeartbeatTimeoutChange={onHeartbeatTimeoutChange} onCommandTimeoutChange={onCommandTimeoutChange} />}
    </Box>
  )
}
