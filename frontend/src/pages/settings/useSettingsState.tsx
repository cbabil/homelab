/**
 * Settings State Hook
 * 
 * Custom hook to manage settings page state and handlers.
 */

import { useState, useEffect } from 'react'
import { Session, SortKey } from './types'
import { validateMcpConfig } from './utils'
import { settingsLogger } from '@/services/systemLogger'
import { useMCP } from '@/providers/MCPProvider'

export function useSettingsState() {
  // Get MCP provider status
  const { isConnected, error } = useMCP()
  
  const [activeTab, setActiveTab] = useState('general')
  const [activeServerTab, setActiveServerTab] = useState('ssh')
  const [serverAlerts, setServerAlerts] = useState(true)
  const [resourceAlerts, setResourceAlerts] = useState(true)
  const [updateAlerts, setUpdateAlerts] = useState(false)
  const [autoRetry, setAutoRetry] = useState(true)
  const [connectionTimeout, setConnectionTimeout] = useState('30')
  const [retryCount, setRetryCount] = useState('3')
  
  // Load MCP config from localStorage or use default
  const getInitialMcpConfig = () => {
    try {
      const saved = localStorage.getItem('homelab-mcp-config')
      if (saved) {
        const config = JSON.parse(saved)
        settingsLogger.info('Loaded MCP config from localStorage', { 
          servers: Object.keys(config.mcpServers || {}) 
        })
        return config
      }
    } catch (error) {
      settingsLogger.warn('Failed to load MCP config from localStorage', error)
    }
    
    // Default configuration
    settingsLogger.info('Using default MCP configuration')
    return {
      "mcpServers": {
        "homelab-assistant": {
          "type": "http",
          "url": import.meta.env.VITE_MCP_SERVER_URL || '/mcp',
          "name": "Homelab Assistant",
          "description": "Local homelab management MCP server"
        }
      }
    }
  }

  // MCP Configuration state
  const [mcpConfig, setMcpConfigState] = useState(getInitialMcpConfig)
  
  // Wrapper to persist to localStorage when MCP config changes
  const setMcpConfig = (newConfig: typeof mcpConfig) => {
    settingsLogger.info('Persisting MCP config to localStorage', { 
      servers: Object.keys(newConfig.mcpServers || {}) 
    })
    setMcpConfigState(newConfig)
    try {
      localStorage.setItem('homelab-mcp-config', JSON.stringify(newConfig))
      settingsLogger.info('MCP config successfully saved to localStorage')
    } catch (error) {
      settingsLogger.warn('Failed to save MCP config to localStorage', error)
    }
  }
  const [isEditingMcpConfig, setIsEditingMcpConfig] = useState(false)
  const [mcpConfigText, setMcpConfigText] = useState('')
  const [originalMcpConfig, setOriginalMcpConfig] = useState('')
  const [mcpConfigError, setMcpConfigError] = useState('')
  
  // MCP Connection state - sync with actual provider
  const [mcpConnectionStatus, setMcpConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [mcpConnectionError, setMcpConnectionError] = useState('')

  // Sync MCP connection status with actual provider
  useEffect(() => {
    if (isConnected) {
      setMcpConnectionStatus('connected')
      setMcpConnectionError('')
    } else if (error) {
      setMcpConnectionStatus('error')
      setMcpConnectionError(error)
    } else {
      setMcpConnectionStatus('disconnected')
      setMcpConnectionError('')
    }
  }, [isConnected, error])
  
  // Session table state
  const [sortBy, setSortBy] = useState<SortKey>('lastActivity')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // Mock session data
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: 'sess_****7a2f',
      status: 'active',
      started: new Date('2024-01-15T09:15:00'),
      lastActivity: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
      location: '192.168.1.*** (Local network)',
      ip: '192.168.1.100'
    },
    {
      id: 'sess_****9b4c',
      status: 'idle',
      started: new Date('2024-01-15T08:30:00'),
      lastActivity: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
      location: '10.0.1.*** (VPN)',
      ip: '10.0.1.50'
    }
    // Additional sessions truncated for brevity
  ])

  return {
    // State
    activeTab,
    activeServerTab,
    serverAlerts,
    resourceAlerts,
    updateAlerts,
    autoRetry,
    connectionTimeout,
    retryCount,
    mcpConfig,
    isEditingMcpConfig,
    mcpConfigText,
    originalMcpConfig,
    mcpConfigError,
    mcpConnectionStatus,
    mcpConnectionError,
    sortBy,
    sortOrder,
    sessions,
    
    // Setters
    setActiveTab,
    setActiveServerTab,
    setServerAlerts,
    setResourceAlerts,
    setUpdateAlerts,
    setAutoRetry,
    setConnectionTimeout,
    setRetryCount,
    setMcpConfig,
    setIsEditingMcpConfig,
    setMcpConfigText,
    setOriginalMcpConfig,
    setMcpConfigError,
    setMcpConnectionStatus,
    setMcpConnectionError,
    setSortBy,
    setSortOrder,
    setSessions
  }
}