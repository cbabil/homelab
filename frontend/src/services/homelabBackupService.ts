/**
 * Homelab Backup Service
 * 
 * Comprehensive backup and restore service for all homelab data including
 * settings, servers, and applications. Provides complete system backup
 * and selective restore capabilities.
 */

import { UserSettings } from '@/types/settings'
import { ServerConnection } from '@/types/server'
import { App } from '@/types/app'
import { settingsService } from './settingsService'
import { serverStorageService } from './serverStorageService'
import { HomelabMCPClient } from './mcpClient'
import { ApplicationsDataService } from './applicationsDataService'

// Backup data structure
export interface HomelabBackup {
  version: string
  timestamp: string
  settings: UserSettings
  servers: ServerConnection[]
  applications: App[]
  metadata: BackupMetadata
}

export interface BackupMetadata {
  homelabVersion: string
  userAgent: string
  exportedBy: string
  totalItems: number
  checksum?: string
}

export interface BackupResult {
  success: boolean
  message: string
  filename?: string
  backup?: HomelabBackup
}

export interface RestoreResult {
  success: boolean
  message: string
  restored: {
    settings: boolean
    servers: number
    applications: number
  }
  skipped: {
    servers: number
    applications: number
  }
  errors: string[]
}

export interface RestoreOptions {
  includeSettings: boolean
  includeServers: boolean
  includeApplications: boolean
  overwriteExisting: boolean
}

class HomelabBackupService {
  private readonly BACKUP_VERSION = '1.0.0'
  
  /**
   * Create a complete backup of all homelab data
   */
  async createBackup(): Promise<BackupResult> {
    try {
      // Get current settings
      const settings = settingsService.getSettings()
      
      // Get all servers
      const servers = serverStorageService.getAllServers()
      
      // Get applications (using mock data for now)
      const applications = await this.getApplications()
      
      const backup: HomelabBackup = {
        version: this.BACKUP_VERSION,
        timestamp: new Date().toISOString(),
        settings,
        servers,
        applications,
        metadata: {
          homelabVersion: '1.0.0', // Could be read from package.json
          userAgent: navigator.userAgent,
          exportedBy: 'Homelab Management System',
          totalItems: 1 + servers.length + applications.length,
          checksum: this.generateChecksum({ settings, servers, applications })
        }
      }
      
      const filename = `homelab_backup_${this.formatDate(new Date())}.json`
      
      this.downloadFile(JSON.stringify(backup, null, 2), filename)
      
      return {
        success: true,
        message: `Backup created successfully with ${backup.metadata.totalItems} items`,
        filename,
        backup
      }
    } catch (error) {
      return {
        success: false,
        message: `Backup failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }
  
  /**
   * Restore data from a backup file
   */
  async restoreFromFile(options: RestoreOptions): Promise<RestoreResult> {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.style.display = 'none'
      
      input.onchange = async (event) => {
        const file = (event.target as HTMLInputElement).files?.[0]
        if (!file) {
          resolve({
            success: false,
            message: 'No file selected',
            restored: { settings: false, servers: 0, applications: 0 },
            skipped: { servers: 0, applications: 0 },
            errors: ['No file selected']
          })
          return
        }
        
        try {
          const content = await this.readFileContent(file)
          const result = await this.restoreBackup(content, options)
          resolve(result)
        } catch (error) {
          resolve({
            success: false,
            message: `Restore failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
            restored: { settings: false, servers: 0, applications: 0 },
            skipped: { servers: 0, applications: 0 },
            errors: [error instanceof Error ? error.message : 'Unknown error']
          })
        } finally {
          document.body.removeChild(input)
        }
      }
      
      input.oncancel = () => {
        document.body.removeChild(input)
        resolve({
          success: false,
          message: 'File selection cancelled',
          restored: { settings: false, servers: 0, applications: 0 },
          skipped: { servers: 0, applications: 0 },
          errors: ['Operation cancelled']
        })
      }
      
      document.body.appendChild(input)
      input.click()
    })
  }
  
  /**
   * Restore backup from parsed content
   */
  private async restoreBackup(content: string, options: RestoreOptions): Promise<RestoreResult> {
    const errors: string[] = []
    const result: RestoreResult = {
      success: false,
      message: '',
      restored: { settings: false, servers: 0, applications: 0 },
      skipped: { servers: 0, applications: 0 },
      errors: []
    }
    
    try {
      const backup = this.parseBackup(content)
      
      // Validate backup integrity
      const validation = this.validateBackup(backup)
      if (!validation.isValid) {
        return {
          ...result,
          message: `Invalid backup: ${validation.errors.join(', ')}`,
          errors: validation.errors
        }
      }
      
      // Restore settings
      if (options.includeSettings && backup.settings) {
        try {
          await this.restoreSettings(backup.settings)
          result.restored.settings = true
        } catch (error) {
          errors.push(`Settings restore failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
        }
      }
      
      // Restore servers
      if (options.includeServers && backup.servers) {
        const serverResult = await this.restoreServers(backup.servers, options.overwriteExisting)
        result.restored.servers = serverResult.restored
        result.skipped.servers = serverResult.skipped
        errors.push(...serverResult.errors)
      }
      
      // Restore applications
      if (options.includeApplications && backup.applications) {
        const appResult = await this.restoreApplications(backup.applications, options.overwriteExisting)
        result.restored.applications = appResult.restored
        result.skipped.applications = appResult.skipped
        errors.push(...appResult.errors)
      }
      
      result.errors = errors
      result.success = errors.length === 0
      result.message = result.success 
        ? `Restore completed successfully`
        : `Restore completed with ${errors.length} errors`
      
      return result
    } catch (error) {
      return {
        ...result,
        message: `Restore failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      }
    }
  }
  
  /**
   * Parse and validate backup file content
   */
  private parseBackup(content: string): HomelabBackup {
    try {
      const parsed = JSON.parse(content)
      
      // Basic structure validation
      if (!parsed.version || !parsed.timestamp) {
        throw new Error('Invalid backup format: missing version or timestamp')
      }
      
      return parsed as HomelabBackup
    } catch (error) {
      throw new Error(`Invalid backup file: ${error instanceof Error ? error.message : 'Parse error'}`)
    }
  }
  
  /**
   * Validate backup integrity
   */
  private validateBackup(backup: HomelabBackup): { isValid: boolean; errors: string[] } {
    const errors: string[] = []
    
    if (!backup.version || backup.version !== this.BACKUP_VERSION) {
      errors.push(`Unsupported backup version: ${backup.version}`)
    }
    
    if (!backup.timestamp) {
      errors.push('Missing backup timestamp')
    }
    
    if (!backup.metadata) {
      errors.push('Missing backup metadata')
    }
    
    return { isValid: errors.length === 0, errors }
  }
  
  /**
   * Restore settings from backup
   */
  private async restoreSettings(settings: UserSettings): Promise<void> {
    // Restore each settings section
    await settingsService.updateSettings('security', settings.security)
    await settingsService.updateSettings('ui', settings.ui)  
    await settingsService.updateSettings('system', settings.system)
  }
  
  /**
   * Restore servers from backup
   */
  private async restoreServers(
    servers: ServerConnection[], 
    overwrite: boolean
  ): Promise<{ restored: number; skipped: number; errors: string[] }> {
    let restored = 0
    let skipped = 0
    const errors: string[] = []
    
    for (const server of servers) {
      try {
        const existing = serverStorageService.getAllServers().find(s => 
          s.hostname === server.hostname && s.port === server.port
        )
        
        if (existing && !overwrite) {
          skipped++
        } else {
          const serverInput = {
            name: server.name,
            hostname: server.hostname,
            port: server.port,
            username: server.username,
            authType: server.authType,
            password: server.authType === 'password' ? server.password : undefined,
            privateKeyFile: server.authType === 'key' ? server.privateKeyFile : undefined
          }
          
          if (existing && overwrite) {
            serverStorageService.updateServer(existing.id, serverInput)
          } else {
            serverStorageService.addServer(serverInput)
          }
          restored++
        }
      } catch (error) {
        errors.push(`Failed to restore server ${server.name}: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }
    
    return { restored, skipped, errors }
  }
  
  /**
   * Restore applications from backup
   */
  private async restoreApplications(
    applications: App[], 
    overwrite: boolean
  ): Promise<{ restored: number; skipped: number; errors: string[] }> {
    // Applications are currently read-only in this implementation
    // This is a placeholder for future application management
    return {
      restored: 0,
      skipped: applications.length,
      errors: ['Application restore not yet implemented - applications are currently read-only']
    }
  }
  
  /**
   * Get current applications data
   */
  private async getApplications(): Promise<App[]> {
    try {
      const serverUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp'
      const client = new HomelabMCPClient(serverUrl)

      try {
        await client.connect()
        const applicationsService = new ApplicationsDataService(client, { cacheTimeout: 0 })
        const response = await applicationsService.search()

        if (response.success && response.data) {
          return response.data.apps
        }

        console.warn('Applications fetch failed:', response.error || response.message)
        return []
      } finally {
        await client.disconnect()
      }
    } catch (error) {
      console.warn('Could not load applications data:', error)
      return []
    }
  }
  
  /**
   * Generate checksum for backup validation
   */
  private generateChecksum(data: { settings: UserSettings; servers: ServerConnection[]; applications: App[] }): string {
    const content = JSON.stringify(data)
    // Simple hash function (in production, consider using crypto.subtle.digest)
    let hash = 0
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash.toString(16)
  }
  
  /**
   * Format date for filename
   */
  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0]
  }
  
  /**
   * Read file content as text
   */
  private readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
  }
  
  /**
   * Trigger file download in browser
   */
  private downloadFile(content: string, filename: string): void {
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
  }
}

export const homelabBackupService = new HomelabBackupService()
