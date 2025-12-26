/**
 * useServers Hook
 * 
 * Custom hook for server state management and CRUD operations.
 * Centralizes all server-related logic for better maintainability.
 */

import { useState, useEffect } from 'react'
import { ServerConnection, ServerConnectionInput } from '@/types/server'
import { serverStorageService } from '@/services/serverStorageService'
import { serverInfoService } from '@/services/serverInfoService'

export function useServers() {
  const [servers, setServers] = useState<ServerConnection[]>([])

  useEffect(() => {
    setServers(serverStorageService.getAllServers())
  }, [])
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

  const handleDeleteServer = (serverId: string) => {
    if (confirm('Are you sure you want to delete this server?')) {
      serverStorageService.deleteServer(serverId)
      setServers(serverStorageService.getAllServers())
    }
  }

  const handleConnectServer = async (serverId: string) => {
    const server = serverStorageService.getServerById(serverId)
    if (!server) return

    // Set server to preparing state
    serverStorageService.updateServerStatus(serverId, 'preparing')
    setServers(serverStorageService.getAllServers())
    
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
  }

  const handleDisconnectServer = (serverId: string) => {
    serverStorageService.updateServerStatus(serverId, 'disconnected')
    setServers(serverStorageService.getAllServers())
  }

  const handleSaveServer = (serverData: ServerConnectionInput) => {
    if (editingServer) {
      serverStorageService.updateServer(editingServer.id, serverData)
    } else {
      serverStorageService.addServer(serverData)
    }
    setServers(serverStorageService.getAllServers())
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