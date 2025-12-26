/**
 * Server Storage Operations
 * 
 * Core CRUD operations for server data persistence.
 */

import { ServerConnection, ServerConnectionInput, SystemInfo } from '@/types/server'
import { StorageData } from './storageTypes'
import { saveToStorage } from './storageHelpers'

export function addServerToStorage(
  data: StorageData, 
  serverData: ServerConnectionInput
): { data: StorageData; server: ServerConnection } {
  const newServer: ServerConnection = {
    ...serverData,
    id: `srv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    status: 'disconnected',
    created_at: new Date().toISOString()
  }

  const updatedData = {
    ...data,
    servers: [...data.servers, newServer]
  }

  saveToStorage(updatedData)
  return { data: updatedData, server: newServer }
}

export function updateServerInStorage(
  data: StorageData,
  id: string,
  serverData: ServerConnectionInput
): { data: StorageData; server: ServerConnection | null } {
  const index = data.servers.findIndex(server => server.id === id)
  if (index === -1) return { data, server: null }

  const existingServer = data.servers[index]
  const updatedServer: ServerConnection = {
    ...existingServer,
    ...serverData,
    updated_at: new Date().toISOString()
  }

  const updatedServers = [...data.servers]
  updatedServers[index] = updatedServer

  const updatedData = {
    ...data,
    servers: updatedServers
  }

  saveToStorage(updatedData)
  return { data: updatedData, server: updatedServer }
}

export function deleteServerFromStorage(
  data: StorageData,
  id: string
): { data: StorageData; success: boolean } {
  const index = data.servers.findIndex(server => server.id === id)
  if (index === -1) return { data, success: false }

  const updatedData = {
    ...data,
    servers: data.servers.filter(server => server.id !== id)
  }

  saveToStorage(updatedData)
  return { data: updatedData, success: true }
}

export function updateServerStatusInStorage(
  data: StorageData,
  id: string,
  status: ServerConnection['status']
): StorageData {
  const server = data.servers.find(s => s.id === id)
  if (!server) return data

  const updatedServers = data.servers.map(s => 
    s.id === id 
      ? { 
          ...s, 
          status, 
          ...(status === 'connected' && { last_connected: new Date().toISOString() })
        }
      : s
  )

  const updatedData = {
    ...data,
    servers: updatedServers
  }

  saveToStorage(updatedData)
  return updatedData
}

export function updateServerSystemInfoInStorage(
  data: StorageData,
  id: string,
  systemInfo: SystemInfo
): StorageData {
  const server = data.servers.find(s => s.id === id)
  if (!server) return data

  const updatedServers = data.servers.map(s => 
    s.id === id 
      ? { 
          ...s, 
          system_info: systemInfo,
          updated_at: new Date().toISOString()
        }
      : s
  )

  const updatedData = {
    ...data,
    servers: updatedServers
  }

  saveToStorage(updatedData)
  return updatedData
}