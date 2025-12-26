/**
 * Server Settings Component
 * 
 * SSH connection settings and MCP server configuration.
 */

import { cn } from '@/utils/cn'
import { Toggle, SettingRow } from './components'

interface ServerSettingsProps {
  activeServerTab: string
  connectionTimeout: string
  retryCount: string
  autoRetry: boolean
  mcpConfig: Record<string, unknown>
  isEditingMcpConfig: boolean
  mcpConfigText: string
  mcpConfigError: string
  mcpConnectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  mcpConnectionError: string
  onActiveServerTabChange: (tab: string) => void
  onConnectionTimeoutChange: (timeout: string) => void
  onRetryCountChange: (count: string) => void
  onAutoRetryChange: (enabled: boolean) => void
  onMcpConfigEdit: () => void
  onMcpConfigSave: () => void
  onMcpConfigCancel: () => void
  onMcpConnect: () => void
  onMcpDisconnect: () => void
  onMcpConfigTextChange: (text: string) => void
}

export function ServerSettings({
  activeServerTab,
  connectionTimeout,
  retryCount,
  autoRetry,
  mcpConfig,
  isEditingMcpConfig,
  mcpConfigText,
  mcpConfigError,
  mcpConnectionStatus,
  mcpConnectionError,
  onActiveServerTabChange,
  onConnectionTimeoutChange,
  onRetryCountChange,
  onAutoRetryChange,
  onMcpConfigEdit,
  onMcpConfigSave,
  onMcpConfigCancel,
  onMcpConnect,
  onMcpDisconnect,
  onMcpConfigTextChange
}: ServerSettingsProps) {
  return (
    <div className="space-y-4">
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
        <button
          onClick={() => onActiveServerTabChange('ssh')}
          className={cn(
            'px-3 py-1 rounded text-sm font-medium transition-colors',
            activeServerTab === 'ssh' 
              ? 'bg-background shadow-sm text-primary' 
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          SSH
        </button>
        <button
          onClick={() => onActiveServerTabChange('mcp')}
          className={cn(
            'px-3 py-1 rounded text-sm font-medium transition-colors',
            activeServerTab === 'mcp' 
              ? 'bg-background shadow-sm text-primary' 
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          MCP
        </button>
      </div>

      <div className="space-y-4 flex-1">
        {activeServerTab === 'ssh' && (
          <div className="bg-card rounded-lg border p-3">
            <h4 className="text-sm font-semibold mb-3 text-primary">Connection Settings</h4>
            <div className="space-y-0">
              <SettingRow 
                label="Timeout"
                children={
                  <select 
                    value={connectionTimeout} 
                    onChange={(e) => onConnectionTimeoutChange(e.target.value)} 
                    className="px-2 py-1 border border-input rounded text-sm bg-background min-w-16"
                  >
                    <option value="10">10s</option>
                    <option value="30">30s</option>
                    <option value="60">1m</option>
                  </select>
                }
              />
              <SettingRow 
                label="Retry count"
                children={
                  <select 
                    value={retryCount} 
                    onChange={(e) => onRetryCountChange(e.target.value)} 
                    className="px-2 py-1 border border-input rounded text-sm bg-background min-w-16"
                  >
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="5">5</option>
                    <option value="10">10</option>
                  </select>
                }
              />
              <SettingRow 
                label="Auto-retry" 
                children={
                  <Toggle checked={autoRetry} onChange={onAutoRetryChange} />
                } 
              />
            </div>
          </div>
        )}

        {activeServerTab === 'mcp' && (
          <div className="bg-card rounded-lg border p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <h4 className="text-sm font-semibold text-primary">MCP Server Configuration</h4>
                <div className="flex items-center space-x-2">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    mcpConnectionStatus === 'connected' && "bg-green-500",
                    mcpConnectionStatus === 'connecting' && "bg-yellow-500 animate-pulse",
                    mcpConnectionStatus === 'disconnected' && "bg-gray-400",
                    mcpConnectionStatus === 'error' && "bg-red-500"
                  )} />
                  <span className="text-xs text-muted-foreground">
                    {mcpConnectionStatus === 'connected' && 'Connected'}
                    {mcpConnectionStatus === 'connecting' && 'Connecting...'}
                    {mcpConnectionStatus === 'disconnected' && 'Disconnected'}
                    {mcpConnectionStatus === 'error' && 'Connection Error'}
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {mcpConnectionStatus === 'connected' ? (
                  <button
                    onClick={onMcpDisconnect}
                    className="px-3 py-1 text-xs font-medium rounded transition-colors bg-red-600 text-white hover:bg-red-700"
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={onMcpConnect}
                    disabled={mcpConnectionStatus === 'connecting'}
                    className={cn(
                      "px-3 py-1 text-xs font-medium rounded transition-colors",
                      mcpConnectionStatus === 'connecting'
                        ? "bg-yellow-600 text-white cursor-not-allowed"
                        : "bg-green-600 text-white hover:bg-green-700"
                    )}
                  >
                    {mcpConnectionStatus === 'connecting' ? 'Connecting...' : 'Connect'}
                  </button>
                )}
                <button
                  onClick={isEditingMcpConfig ? onMcpConfigSave : onMcpConfigEdit}
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded transition-colors",
                    isEditingMcpConfig 
                      ? "bg-blue-600 text-white hover:bg-blue-700" 
                      : "bg-primary text-white hover:bg-primary/90"
                  )}
                >
                  {isEditingMcpConfig ? 'Save' : 'Edit'}
                </button>
              </div>
            </div>
            
            {mcpConfigError && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700 dark:bg-red-950 dark:border-red-800 dark:text-red-300">
                {mcpConfigError}
              </div>
            )}
            
            {mcpConnectionError && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700 dark:bg-red-950 dark:border-red-800 dark:text-red-300">
                <strong>Connection Error:</strong> {mcpConnectionError}
              </div>
            )}
            
            {isEditingMcpConfig ? (
              <div className="space-y-2">
                <textarea
                  value={mcpConfigText}
                  onChange={(e) => onMcpConfigTextChange(e.target.value)}
                  onBlur={onMcpConfigCancel}
                  className={cn(
                    "w-full h-96 p-3 text-xs font-mono border border-input rounded-md bg-background",
                    "focus:ring-2 focus:ring-primary focus:border-transparent resize-none",
                    mcpConfigError && "border-red-500 focus:ring-red-500 bg-red-50 dark:bg-red-950/50"
                  )}
                  placeholder="Enter your MCP server configuration..."
                  autoFocus
                />
                <div className="flex items-start justify-between">
                  <p className="text-xs text-muted-foreground">
                    Configure your MCP servers using JSON format. Click away to cancel.
                  </p>
                  {mcpConfigError && (
                    <div className="text-xs text-red-600 dark:text-red-400 max-w-md">
                      {mcpConfigError}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <pre className={cn(
                  "w-full h-96 p-3 text-xs font-mono border border-input rounded-md bg-muted/50 overflow-auto",
                  "whitespace-pre-wrap break-words"
                )}>
                  <code className="text-foreground">
                    {JSON.stringify(mcpConfig, null, 2)}
                  </code>
                </pre>
                <p className="text-xs text-muted-foreground">
                  Current MCP server configuration. Click Edit to modify the settings.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}