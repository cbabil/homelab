/**
 * Settings Page Component
 * 
 * Main settings container that manages different settings tabs in a modular architecture.
 */

import { GeneralSettings, SecuritySettings, NotificationSettings, ServerSettings, MarketplaceSettings } from './index'
import { useSettingsState } from './useSettingsState'
import { useSettingsHandlers } from './useSettingsHandlers'
import { SettingsHeader } from './SettingsHeader'
import { SettingsTabNavigation } from './SettingsTabNavigation'
import { SettingsActionFooter } from './SettingsActionFooter'

export function SettingsPage() {
  const state = useSettingsState()
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

      case 'marketplace':
        return <MarketplaceSettings />

      default:
        return null
    }
  }

  return (
    <div className="h-full flex flex-col space-y-4">
      <SettingsHeader />
      <SettingsTabNavigation activeTab={state.activeTab} onTabChange={state.setActiveTab} />
      
      {/* Main Content Area */}
      <div className="flex-1 min-h-0 overflow-auto">
        {renderTabContent()}
      </div>

      <SettingsActionFooter />
    </div>
  )
}