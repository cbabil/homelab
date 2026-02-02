/**
 * Settings Handlers Hook
 * 
 * Custom hook to manage settings page event handlers.
 */

import { SortKey, Session, McpConfig } from './types'
import { validateMcpConfig } from './utils'
import { TomoMCPClient } from '@/services/mcpClient'
import { settingsLogger } from '@/services/systemLogger'

interface UseSettingsHandlersProps {
  mcpConfigText: string
  setMcpConfig: (config: McpConfig | null) => void
  setMcpConfigError: (error: string) => void
  setIsEditingMcpConfig: (editing: boolean) => void
  setOriginalMcpConfig: (config: string) => void
  setMcpConfigText: (text: string) => void
  setSortBy: (sortBy: SortKey) => void
  setSortOrder: (order: 'asc' | 'desc') => void
  setSessions: (sessions: Session[] | ((prev: Session[]) => Session[])) => void
  sortBy: SortKey
  sortOrder: 'asc' | 'desc'
  mcpConfig: McpConfig | null
  originalMcpConfig: string
  setMcpConnectionStatus: (status: 'disconnected' | 'connecting' | 'connected' | 'error') => void
  setMcpConnectionError: (error: string) => void
}

export function useSettingsHandlers({
  mcpConfigText,
  setMcpConfig,
  setMcpConfigError,
  setIsEditingMcpConfig,
  setOriginalMcpConfig,
  setMcpConfigText,
  setSortBy,
  setSortOrder,
  setSessions,
  sortBy,
  sortOrder,
  mcpConfig,
  originalMcpConfig,
  setMcpConnectionStatus,
  setMcpConnectionError
}: UseSettingsHandlersProps) {

  const handleSort = (column: SortKey) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const handleTerminateSession = (sessionId: string) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId))
  }

  const handleRestoreSession = (sessionId: string) => {
    setSessions(prev => prev.map(session => 
      session.id === sessionId 
        ? { ...session, status: 'active', lastActivity: new Date() }
        : session
    ))
  }

  // Handle MCP config edit mode
  const handleMcpConfigEdit = () => {
    const formattedConfig = JSON.stringify(mcpConfig, null, 2)
    setMcpConfigText(formattedConfig)
    setOriginalMcpConfig(formattedConfig)
    setMcpConfigError('')
    setIsEditingMcpConfig(true)
  }

  // Handle MCP config save
  const handleMcpConfigSave = () => {
    settingsLogger.info('Saving MCP configuration')
    const validation = validateMcpConfig(mcpConfigText)
    
    if (!validation.isValid) {
      settingsLogger.warn('MCP config validation failed', { error: validation.error })
      setMcpConfigError(validation.error)
      return // Prevent saving and stay in edit mode
    }
    
    try {
      const parsedConfig = JSON.parse(mcpConfigText)
      settingsLogger.info('MCP configuration saved successfully', { 
        servers: Object.keys(parsedConfig.mcpServers || {}) 
      })
      setMcpConfig(parsedConfig) // This automatically saves to localStorage
      
      setMcpConfigError('')
      setIsEditingMcpConfig(false)
      setOriginalMcpConfig('')
    } catch {
      settingsLogger.error('Failed to parse MCP configuration JSON')
      setMcpConfigError('Unexpected error parsing JSON')
    }
  }

  // Handle MCP config cancel (blur or explicit cancel)
  const handleMcpConfigCancel = () => {
    setMcpConfigText(originalMcpConfig)
    setMcpConfigError('')
    setIsEditingMcpConfig(false)
    setOriginalMcpConfig('')
  }

  // Handle MCP connection
  const handleMcpConnect = async () => {
    settingsLogger.info('Initiating MCP connection')
    try {
      setMcpConnectionStatus('connecting')
      setMcpConnectionError('')

      // Get the server URL from config
      if (!mcpConfig) {
        settingsLogger.error('MCP config not loaded')
        throw new Error('MCP config not loaded')
      }

      const serverConfig = mcpConfig.mcpServers?.['tomo']
      if (!serverConfig?.url) {
        settingsLogger.error('No MCP server URL configured')
        throw new Error('No MCP server URL configured')
      }
      
      settingsLogger.info('Connecting to MCP server', { url: serverConfig.url })
      const client = new TomoMCPClient(serverConfig.url)
      await client.connect()
      
      setMcpConnectionStatus('connected')
      settingsLogger.info('MCP connection established successfully')
    } catch (error) {
      settingsLogger.error('MCP connection failed', error)
      setMcpConnectionStatus('error')
      setMcpConnectionError(error instanceof Error ? error.message : 'Connection failed')
    }
  }

  // Handle MCP disconnection
  const handleMcpDisconnect = async () => {
    settingsLogger.info('Initiating MCP disconnection')
    try {
      setMcpConnectionStatus('disconnected')
      setMcpConnectionError('')
      settingsLogger.info('MCP disconnected successfully')
      // In a real app, you'd store the client instance and call disconnect on it
    } catch (error) {
      settingsLogger.error('MCP disconnection failed', error)
      setMcpConnectionError(error instanceof Error ? error.message : 'Disconnection failed')
    }
  }

  return {
    handleSort,
    handleTerminateSession,
    handleRestoreSession,
    handleMcpConfigEdit,
    handleMcpConfigSave,
    handleMcpConfigCancel,
    handleMcpConnect,
    handleMcpDisconnect
  }
}