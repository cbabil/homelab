/**
 * Settings Page Component
 *
 * Main settings container that manages different settings tabs in a modular architecture.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Box, Stack } from '@mui/material'
import { GeneralSettings, SecuritySettings, NotificationSettings, ServerSettings, SystemSettings } from './index'
import { useSettingsState } from './useSettingsState'
import { useSettingsHandlers } from './useSettingsHandlers'
import { SettingsHeader } from './SettingsHeader'
import { SettingsTabNavigation } from './SettingsTabNavigation'
import { SettingsSavingProvider } from './SettingsSavingContext'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { useToast } from '@/components/ui/Toast'

function SettingsPageContent() {
  const { t } = useTranslation()
  const state = useSettingsState()
  const { resetSettings } = useSettingsContext()
  const { addToast } = useToast()
  const [searchTerm, setSearchTerm] = useState('')
  const [isResetting, setIsResetting] = useState(false)
  const handlers = useSettingsHandlers({
    mcpConfigText: state.mcpConfigText,
    setMcpConfig: state.setMcpConfig,
    setMcpConfigError: state.setMcpConfigError,
    setIsEditingMcpConfig: state.setIsEditingMcpConfig,
    setOriginalMcpConfig: state.setOriginalMcpConfig,
    setMcpConfigText: state.setMcpConfigText,
    setSortBy: state.setSortBy,
    setSortOrder: state.setSortOrder,
    setSessions: state.setSessions,
    sortBy: state.sortBy,
    sortOrder: state.sortOrder,
    mcpConfig: state.mcpConfig,
    originalMcpConfig: state.originalMcpConfig,
    setMcpConnectionStatus: state.setMcpConnectionStatus,
    setMcpConnectionError: state.setMcpConnectionError
  })

  const renderTabContent = () => {
    switch (state.activeTab) {
      case 'general':
        return <GeneralSettings />

      case 'servers':
        return (
          <ServerSettings
            activeServerTab={state.activeServerTab}
            connectionTimeout={state.connectionTimeout}
            retryCount={state.retryCount}
            autoRetry={state.autoRetry}
            mcpConfig={state.mcpConfig}
            isEditingMcpConfig={state.isEditingMcpConfig}
            mcpConfigText={state.mcpConfigText}
            mcpConfigError={state.mcpConfigError}
            mcpConnectionStatus={state.mcpConnectionStatus}
            mcpConnectionError={state.mcpConnectionError}
            preferAgent={state.preferAgent}
            agentAutoUpdate={state.agentAutoUpdate}
            heartbeatInterval={state.heartbeatInterval}
            heartbeatTimeout={state.heartbeatTimeout}
            commandTimeout={state.commandTimeout}
            onActiveServerTabChange={state.setActiveServerTab}
            onConnectionTimeoutChange={state.setConnectionTimeout}
            onRetryCountChange={state.setRetryCount}
            onAutoRetryChange={state.setAutoRetry}
            onMcpConfigEdit={handlers.handleMcpConfigEdit}
            onMcpConfigSave={handlers.handleMcpConfigSave}
            onMcpConfigCancel={handlers.handleMcpConfigCancel}
            onMcpConnect={handlers.handleMcpConnect}
            onMcpDisconnect={handlers.handleMcpDisconnect}
            onMcpConfigTextChange={(text) => {
              state.setMcpConfigText(text)
              if (state.mcpConfigError) {
                state.setMcpConfigError('')
              }
            }}
            onPreferAgentChange={state.setPreferAgent}
            onAgentAutoUpdateChange={state.setAgentAutoUpdate}
            onHeartbeatIntervalChange={state.setHeartbeatInterval}
            onHeartbeatTimeoutChange={state.setHeartbeatTimeout}
            onCommandTimeoutChange={state.setCommandTimeout}
          />
        )

      case 'security':
        return <SecuritySettings />

      case 'notifications':
        return (
          <NotificationSettings
            serverAlerts={state.serverAlerts}
            resourceAlerts={state.resourceAlerts}
            updateAlerts={state.updateAlerts}
            onServerAlertsChange={state.setServerAlerts}
            onResourceAlertsChange={state.setResourceAlerts}
            onUpdateAlertsChange={state.setUpdateAlerts}
          />
        )

      case 'system':
        return <SystemSettings />

      default:
        return null
    }
  }

  const handleImport = () => {
    // TODO: Implement settings import
    addToast({ type: 'info', title: t('settings.importComingSoon') })
  }

  const handleExport = () => {
    // TODO: Implement settings export
    addToast({ type: 'info', title: t('settings.exportComingSoon') })
  }

  const handleReset = async () => {
    try {
      setIsResetting(true)
      const result = await resetSettings()
      if (result.success) {
        addToast({ type: 'success', title: t('settings.resetSuccess') })
      }
    } catch (error) {
      console.error('Failed to reset settings:', error)
      addToast({ type: 'error', title: t('settings.resetFailed') })
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <Stack spacing={2} sx={{ height: '100%' }}>
      <SettingsHeader
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onImport={handleImport}
        onExport={handleExport}
        onReset={handleReset}
        isResetting={isResetting}
      />
      <SettingsTabNavigation activeTab={state.activeTab} onTabChange={state.setActiveTab} />

      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {renderTabContent()}
      </Box>
    </Stack>
  )
}

export function SettingsPage() {
  return (
    <SettingsSavingProvider>
      <SettingsPageContent />
    </SettingsSavingProvider>
  )
}