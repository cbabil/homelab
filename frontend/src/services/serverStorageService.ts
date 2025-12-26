/**
 * Server Storage Service
 * 
 * Handles persistent storage of server configurations using data directory structure.
 * Provides CRUD operations for server management with proper data persistence.
 */

import { ServerConnection, ServerConnectionInput, SystemInfo } from '@/types/server'
import { StorageData } from './storage/storageTypes'
import { loadFromStorage, exportServersAsJSON, importServersFromJSON } from './storage/storageHelpers'
import {
  addServerToStorage,
  updateServerInStorage,
  deleteServerFromStorage,
  updateServerStatusInStorage,
  updateServerSystemInfoInStorage
} from './storage/serverStorageOperations'

class ServerStorageService {
  private data: StorageData

  constructor() {
    this.data = loadFromStorage()
  }

  getAllServers(): ServerConnection[] {
    return [...this.data.servers]
  }

  getServerById(id: string): ServerConnection | undefined {
    return this.data.servers.find(server => server.id === id)
  }

  addServer(serverData: ServerConnectionInput): ServerConnection {
    const result = addServerToStorage(this.data, serverData)
    this.data = result.data
    return result.server
  }

  updateServer(id: string, serverData: ServerConnectionInput): ServerConnection | null {
    const result = updateServerInStorage(this.data, id, serverData)
    this.data = result.data
    return result.server
  }

  deleteServer(id: string): boolean {
    const result = deleteServerFromStorage(this.data, id)
    this.data = result.data
    return result.success
  }

  updateServerStatus(id: string, status: ServerConnection['status']): void {
    this.data = updateServerStatusInStorage(this.data, id, status)
  }

  updateServerSystemInfo(id: string, systemInfo: SystemInfo): void {
    this.data = updateServerSystemInfoInStorage(this.data, id, systemInfo)
  }

  exportServersAsJSON(): void {
    exportServersAsJSON(this.data)
  }

  async importServersFromJSON(file: File): Promise<void> {
    const importedData = await importServersFromJSON(file)
    this.data = importedData
  }
}

export const serverStorageService = new ServerStorageService()