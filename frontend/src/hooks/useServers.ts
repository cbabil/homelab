/**
 * useServers Hook
 *
 * Custom hook for server state management and CRUD operations.
 * Backend is the single source of truth - no localStorage.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { ServerConnection, ServerConnectionInput, SystemInfo } from '@/types/server'
import { serverInfoService } from '@/services/serverInfoService'
import { useMCP } from '@/providers/MCPProvider'
import {
  ConnectionResult,
  isMcpErrorMessage,
  calculateServerStats,
  filterServers,
  addServerToBackend,
} from './useServerOperations'

/** Backend server response from list_servers */
interface BackendServer {
  id: string
  name: string
  host: string
  port: number
  username: string
  auth_type: string
  status: string
  created_at?: string
  last_connected?: string
  system_info?: Record<string, unknown>
  docker_installed?: boolean
  system_info_updated_at?: string
}

/** Convert backend server to frontend ServerConnection */
function toServerConnection(s: BackendServer): ServerConnection {
  return {
    id: s.id,
    name: s.name,
    host: s.host,
    port: s.port,
    username: s.username,
    auth_type: s.auth_type as 'password' | 'key',
    status: (s.status || 'disconnected') as ServerConnection['status'],
    created_at: s.created_at || new Date().toISOString(),
    last_connected: s.last_connected,
    system_info: s.system_info as SystemInfo | undefined,
    docker_installed: s.docker_installed ?? false,
    system_info_updated_at: s.system_info_updated_at,
  }
}

/** Hook for server bulk selection operations */
function useServerSelection(filteredServers: ServerConnection[]) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const handleSelectServer = useCallback((serverId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(serverId)) {
        next.delete(serverId)
      } else {
        next.add(serverId)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredServers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredServers.map(s => s.id)))
    }
  }, [filteredServers, selectedIds.size])

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  return { selectedIds, setSelectedIds, handleSelectServer, handleSelectAll, handleClearSelection }
}

export function useServers() {
  const [servers, setServers] = useState<ServerConnection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { client, isConnected } = useMCP()
  const initialFetchDone = useRef(false)

  // Fetch servers from backend
  const fetchServers = useCallback(async () => {
    if (!isConnected) {
      setServers([])
      setIsLoading(false)
      return
    }
    try {
      const response = await client.callTool<{
        success: boolean
        data?: { servers: BackendServer[] }
        message?: string
      }>('list_servers', {})

      if (response.data?.success && response.data.data?.servers) {
        setServers(response.data.data.servers.map(toServerConnection))
      } else {
        setServers([])
      }
    } catch (error) {
      console.error('Failed to fetch servers:', error)
      setServers([])
    } finally {
      setIsLoading(false)
    }
  }, [client, isConnected])

  // Set MCP client for serverInfoService
  useEffect(() => {
    serverInfoService.setMCPClient(isConnected ? client : null)
  }, [client, isConnected])

  // Initial fetch when connected
  useEffect(() => {
    if (isConnected && !initialFetchDone.current) {
      initialFetchDone.current = true
      fetchServers()
    } else if (!isConnected) {
      initialFetchDone.current = false
      setServers([])
      setIsLoading(false)
    }
  }, [isConnected, fetchServers])

  const [searchTerm, setSearchTerm] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingServer, setEditingServer] = useState<ServerConnection | undefined>()

  const filteredServers = filterServers(servers, searchTerm)
  const { selectedIds, setSelectedIds, handleSelectServer, handleSelectAll, handleClearSelection } =
    useServerSelection(filteredServers)

  const handleAddServer = () => { setEditingServer(undefined); setIsFormOpen(true) }
  const handleEditServer = (server: ServerConnection) => { setEditingServer(server); setIsFormOpen(true) }

  const handleDeleteServer = useCallback(async (serverId: string) => {
    if (!isConnected) return
    try {
      await client.callTool('delete_server', { server_id: serverId })
      await fetchServers()
    } catch (error) {
      console.error('Failed to delete server:', error)
    }
  }, [client, isConnected, fetchServers])

  const handleConnectServer = useCallback(async (serverId: string): Promise<ConnectionResult> => {
    const server = servers.find(s => s.id === serverId)
    if (!server) return { success: false, error: 'Server not found' }

    // Optimistically update status to preparing
    setServers(prev => prev.map(s => s.id === serverId ? { ...s, status: 'preparing' as const } : s))

    try {
      const result = await serverInfoService.fetchServerInfoById(serverId)
      if (result.success) {
        // Refresh from backend to get updated state
        await fetchServers()
        return { success: true, isMcpError: false }
      }
      const errorMsg = result.error || result.message || 'Connection failed'
      // Update status to error
      setServers(prev => prev.map(s => s.id === serverId ? { ...s, status: 'error' as const } : s))
      return { success: false, error: errorMsg, isMcpError: isMcpErrorMessage(errorMsg) }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Connection failed'
      setServers(prev => prev.map(s => s.id === serverId ? { ...s, status: 'error' as const } : s))
      console.error(`Server connection failed: ${errorMsg}`)
      return { success: false, error: errorMsg, isMcpError: isMcpErrorMessage(errorMsg) }
    }
  }, [servers, fetchServers])

  const handleDisconnectServer = useCallback(async (serverId: string) => {
    if (!isConnected) return
    try {
      // Update status in backend
      await client.callTool('update_server_status', { server_id: serverId, status: 'disconnected' })
      await fetchServers()
    } catch (error) {
      console.error('Failed to disconnect server:', error)
      // Optimistic update as fallback
      setServers(prev => prev.map(s => s.id === serverId ? { ...s, status: 'disconnected' as const } : s))
    }
  }, [client, isConnected, fetchServers])

  const handleSaveServer = async (
    serverData: ServerConnectionInput,
    systemInfo?: SystemInfo,
    onStatusChange?: (status: 'saving' | 'testing' | 'success' | 'error', message?: string) => void,
    preGeneratedServerId?: string
  ): Promise<string | null> => {
    if (!isConnected) {
      throw new Error('Not connected to backend')
    }

    if (editingServer) {
      // Update existing server
      try {
        await client.callTool('update_server', {
          server_id: editingServer.id,
          name: serverData.name,
          host: serverData.host,
          port: serverData.port,
          username: serverData.username,
        })
        await fetchServers()
        return editingServer.id
      } catch (error) {
        console.error('Failed to update server:', error)
        throw error
      }
    }

    // Add new server
    let serverId = preGeneratedServerId || crypto.randomUUID()
    onStatusChange?.('saving')

    try {
      const actualServerId = await addServerToBackend(client, serverId, serverData, systemInfo)
      serverId = actualServerId
      await fetchServers()
      return serverId
    } catch (error) {
      console.error('Failed to add server to backend:', error)
      throw error
    }
  }

  const refreshServers = useCallback(() => {
    fetchServers()
  }, [fetchServers])

  const handleInstallDocker = async (serverId: string) => {
    if (!isConnected) return
    try {
      const response = await client.callTool<{
        success: boolean; message: string; data?: { docker_version?: string }
      }>('install_docker', { server_id: serverId })

      if (response.data?.success) {
        await handleConnectServer(serverId)
      } else {
        throw new Error(response.data?.message || 'Docker installation failed')
      }
    } catch (error) {
      console.error('Failed to install Docker:', error)
      throw error
    }
  }

  const handleRemoveDocker = useCallback(async (serverId: string): Promise<boolean> => {
    if (!isConnected) return false
    try {
      const response = await client.callTool<{
        success: boolean; message: string
      }>('remove_docker', { server_id: serverId })

      if (response.data?.success) {
        await fetchServers()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to remove Docker:', error)
      return false
    }
  }, [client, isConnected, fetchServers])

  const { connectedCount, totalServers, healthPercentage } = calculateServerStats(servers)

  const handleBulkConnect = useCallback(async () => {
    for (const id of Array.from(selectedIds)) await handleConnectServer(id)
    setSelectedIds(new Set())
  }, [selectedIds, handleConnectServer, setSelectedIds])

  const handleBulkDisconnect = useCallback(async () => {
    for (const id of Array.from(selectedIds)) await handleDisconnectServer(id)
    setSelectedIds(new Set())
  }, [selectedIds, handleDisconnectServer, setSelectedIds])

  // Refresh info for all connected servers (used by auto-refresh)
  const refreshConnectedServersInfo = useCallback(async () => {
    const connectedServers = servers.filter(s => s.status === 'connected')

    for (const server of connectedServers) {
      try {
        await serverInfoService.fetchServerInfoById(server.id)
      } catch (error) {
        console.error(`Auto-refresh failed for server ${server.name}:`, error)
      }
    }
    await fetchServers()
  }, [servers, fetchServers])

  return {
    servers, filteredServers, searchTerm, setSearchTerm, isFormOpen, setIsFormOpen,
    editingServer, connectedCount, totalServers, healthPercentage, isLoading,
    handleAddServer, handleEditServer, handleDeleteServer, handleConnectServer,
    handleInstallDocker, handleRemoveDocker, handleDisconnectServer, handleSaveServer, refreshServers,
    refreshConnectedServersInfo,
    selectedIds, handleSelectServer, handleSelectAll, handleClearSelection,
    handleBulkConnect, handleBulkDisconnect
  }
}
