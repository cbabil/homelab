/**
 * useServers Hook
 *
 * Custom hook for server state management and CRUD operations.
 * Syncs with backend database via MCP tools for persistence.
 */

import { useState, useEffect, useCallback } from 'react'
import { ServerConnection, ServerConnectionInput } from '@/types/server'
import { serverStorageService } from '@/services/serverStorageService'
import { serverInfoService } from '@/services/serverInfoService'
import { useMCP } from '@/providers/MCPProvider'

export function useServers() {
  const [servers, setServers] = useState<ServerConnection[]>([])
  const { client, isConnected } = useMCP()

  // Sync server to backend database (upsert)
  const syncToBackend = useCallback(async (server: ServerConnection) => {
    if (!isConnected) return
    try {
      await client.callTool('sync_server', {
        server_id: server.id,
        name: server.name,
        host: server.host,
        port: server.port,
        username: server.username,
        auth_type: server.auth_type,
        status: server.status || 'disconnected'
      })
    } catch (error) {
      console.error('Failed to sync server to backend:', error)
    }
  }, [client, isConnected])

  // Delete from backend
  const deleteFromBackend = useCallback(async (serverId: string) => {
    if (!isConnected) return
    try {
      await client.callTool('delete_server', { server_id: serverId })
    } catch (error) {
      console.error('Failed to delete server from backend:', error)
    }
  }, [client, isConnected])

  // Initial load and sync to backend
  useEffect(() => {
    const initServers = async () => {
      const localServers = serverStorageService.getAllServers()
      setServers(localServers)

      // Sync all existing servers to backend on mount
      if (isConnected) {
        for (const server of localServers) {
          await syncToBackend(server)
        }
      }
    }
    initServers()
  }, [isConnected, syncToBackend])
  const [searchTerm, setSearchTerm] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingServer, setEditingServer] = useState<ServerConnection | undefined>()

  const filteredServers = servers.filter(server =>
    server.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.username.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleAddServer = () => {
    setEditingServer(undefined)
    setIsFormOpen(true)
  }

  const handleEditServer = (server: ServerConnection) => {
    setEditingServer(server)
    setIsFormOpen(true)
  }

  const handleDeleteServer = async (serverId: string) => {
    if (confirm('Are you sure you want to delete this server?')) {
      serverStorageService.deleteServer(serverId)
      setServers(serverStorageService.getAllServers())
      await deleteFromBackend(serverId)
    }
  }

  const handleConnectServer = async (serverId: string) => {
    let server = serverStorageService.getServerById(serverId)
    if (!server) return

    // Set server to preparing state
    serverStorageService.updateServerStatus(serverId, 'preparing')
    setServers(serverStorageService.getAllServers())
    server = serverStorageService.getServerById(serverId)!
    await syncToBackend(server)

    try {
      // Fetch server information
      const result = await serverInfoService.fetchServerInfo(server)

      if (result.success && result.system_info) {
        // Update server with system info and connected status
        serverStorageService.updateServerSystemInfo(serverId, result.system_info)
        serverStorageService.updateServerStatus(serverId, 'connected')
      } else {
        // Connection succeeded but info fetch failed - still mark as connected
        serverStorageService.updateServerStatus(serverId, 'connected')
        console.warn(`Failed to fetch system info: ${result.error || result.message}`)
      }
    } catch (error) {
      // Connection failed completely
      serverStorageService.updateServerStatus(serverId, 'error')
      console.error(`Server connection failed: ${error}`)
    }

    setServers(serverStorageService.getAllServers())
    // Sync final status to backend
    const updatedServer = serverStorageService.getServerById(serverId)
    if (updatedServer) {
      await syncToBackend(updatedServer)
    }
  }

  const handleDisconnectServer = async (serverId: string) => {
    serverStorageService.updateServerStatus(serverId, 'disconnected')
    setServers(serverStorageService.getAllServers())
    const server = serverStorageService.getServerById(serverId)
    if (server) {
      await syncToBackend(server)
    }
  }

  const handleSaveServer = async (serverData: ServerConnectionInput) => {
    if (editingServer) {
      serverStorageService.updateServer(editingServer.id, serverData)
      setServers(serverStorageService.getAllServers())
    } else {
      const newServer = serverStorageService.addServer(serverData)
      setServers(serverStorageService.getAllServers())
      await syncToBackend(newServer)
    }
  }

  const refreshServers = () => {
    setServers(serverStorageService.getAllServers())
  }

  const connectedCount = servers.filter(s => s.status === 'connected').length
  const totalServers = servers.length
  const healthPercentage = Math.round((connectedCount / totalServers) * 100) || 0

  return {
    servers,
    filteredServers,
    searchTerm,
    setSearchTerm,
    isFormOpen,
    setIsFormOpen,
    editingServer,
    connectedCount,
    totalServers,
    healthPercentage,
    handleAddServer,
    handleEditServer,
    handleDeleteServer,
    handleConnectServer,
    handleDisconnectServer,
    handleSaveServer,
    refreshServers
  }
}