/**
 * Tomo Backup Service
 *
 * Comprehensive backup and restore service for all tomo data including
 * settings, servers, and applications. Provides complete system backup
 * and selective restore capabilities.
 *
 * NOTE: Server data comes from backend via MCP - callers must provide server data.
 */

import { UserSettings } from '@/types/settings'
import { ServerConnection } from '@/types/server'
import { App } from '@/types/app'
import { settingsService } from './settingsService'

// Backup data structure
export interface TomoBackup {
  version: string
  timestamp: string
  settings: UserSettings
  servers: ServerConnection[]
  applications: App[]
  metadata: BackupMetadata
}

export interface BackupMetadata {
  tomoVersion: string
  userAgent: string
  exportedBy: string
  totalItems: number
  checksum?: string
}

export interface BackupResult {
  success: boolean
  message: string
  filename?: string
  backup?: TomoBackup
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

/** MCP client interface for server operations */
interface MCPClient {
  callTool: <T>(name: string, params: Record<string, unknown>) => Promise<{
    success: boolean
    data?: T
    error?: string
  }>
}

class TomoBackupService {
  private readonly BACKUP_VERSION = '1.0.0'

  /**
   * Create a complete backup of all tomo data
   * @param servers - Server list from backend (caller must provide)
   */
  async createBackup(servers: ServerConnection[] = []): Promise<BackupResult> {
    try {
      // Get current settings
      const settings = settingsService.getSettings()

      // Get applications (using mock data for now)
      const applications = await this.getApplications()

      const backup: TomoBackup = {
        version: this.BACKUP_VERSION,
        timestamp: new Date().toISOString(),
        settings,
        servers,
        applications,
        metadata: {
          tomoVersion: '1.0.0', // Could be read from package.json
          userAgent: navigator.userAgent,
          exportedBy: 'Tomo Management System',
          totalItems: 1 + servers.length + applications.length,
          checksum: this.generateChecksum({ settings, servers, applications })
        }
      }

      const filename = `tomo_backup_${this.formatDate(new Date())}.json`

      this.downloadFile(JSON.stringify(backup, null, 2), filename)

      return {
        success: true,
        message: `Backup created successfully with ${servers.length} servers and ${applications.length} applications`,
        filename,
        backup
      }
    } catch (error) {
      return {
        success: false,
        message: `Failed to create backup: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }

  /**
   * Restore from a backup file
   * @param mcpClient - MCP client for server operations
   * @param existingServers - Current servers from backend (for duplicate checking)
   */
  async restoreFromFile(
    mcpClient: MCPClient,
    existingServers: ServerConnection[],
    options: Partial<RestoreOptions> = {}
  ): Promise<RestoreResult> {
    const fullOptions: RestoreOptions = {
      includeSettings: true,
      includeServers: true,
      includeApplications: true,
      overwriteExisting: false,
      ...options
    }

    const result: RestoreResult = {
      success: false,
      message: '',
      restored: { settings: false, servers: 0, applications: 0 },
      skipped: { servers: 0, applications: 0 },
      errors: []
    }

    try {
      const backup = await this.readBackupFile()

      if (!backup) {
        result.message = 'No backup file selected or file is invalid'
        return result
      }

      // Validate backup version
      if (!this.isCompatibleVersion(backup.version)) {
        result.message = `Incompatible backup version: ${backup.version}`
        return result
      }

      // Restore settings
      if (fullOptions.includeSettings && backup.settings) {
        try {
          await this.restoreSettings(backup.settings)
          result.restored.settings = true
        } catch (error) {
          result.errors.push(`Settings restore failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
        }
      }

      // Restore servers
      if (fullOptions.includeServers && backup.servers) {
        const serverResult = await this.restoreServers(
          mcpClient,
          backup.servers,
          existingServers,
          fullOptions.overwriteExisting
        )
        result.restored.servers = serverResult.restored
        result.skipped.servers = serverResult.skipped
        result.errors.push(...serverResult.errors)
      }

      // Restore applications
      if (fullOptions.includeApplications && backup.applications) {
        const appResult = await this.restoreApplications(
          backup.applications,
          fullOptions.overwriteExisting
        )
        result.restored.applications = appResult.restored
        result.skipped.applications = appResult.skipped
        result.errors.push(...appResult.errors)
      }

      result.success = result.errors.length === 0
      result.message = result.success
        ? 'Backup restored successfully'
        : `Restore completed with ${result.errors.length} error(s)`

      return result
    } catch (error) {
      result.message = `Restore failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      return result
    }
  }

  /**
   * Validate a backup file without restoring
   */
  async validateBackupFile(): Promise<{ valid: boolean; message: string; backup?: TomoBackup }> {
    try {
      const backup = await this.readBackupFile()

      if (!backup) {
        return { valid: false, message: 'No file selected or file is empty' }
      }

      // Check required fields
      if (!backup.version || !backup.timestamp) {
        return { valid: false, message: 'Invalid backup format: missing required fields' }
      }

      // Check version compatibility
      if (!this.isCompatibleVersion(backup.version)) {
        return { valid: false, message: `Incompatible backup version: ${backup.version}` }
      }

      // Validate checksum if present
      if (backup.metadata?.checksum) {
        const calculatedChecksum = this.generateChecksum({
          settings: backup.settings,
          servers: backup.servers,
          applications: backup.applications
        })

        if (calculatedChecksum !== backup.metadata.checksum) {
          return { valid: false, message: 'Backup integrity check failed: checksum mismatch' }
        }
      }

      return {
        valid: true,
        message: `Valid backup from ${new Date(backup.timestamp).toLocaleString()}`,
        backup
      }
    } catch (error) {
      return {
        valid: false,
        message: `Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }

  /**
   * Get backup summary without full restore
   */
  async getBackupSummary(): Promise<{
    hasServers: boolean
    serverCount: number
    hasSettings: boolean
    hasApplications: boolean
    applicationCount: number
    timestamp: string
    version: string
  } | null> {
    try {
      const backup = await this.readBackupFile()
      if (!backup) return null

      return {
        hasServers: backup.servers && backup.servers.length > 0,
        serverCount: backup.servers?.length || 0,
        hasSettings: !!backup.settings,
        hasApplications: backup.applications && backup.applications.length > 0,
        applicationCount: backup.applications?.length || 0,
        timestamp: backup.timestamp,
        version: backup.version
      }
    } catch {
      return null
    }
  }

  // Private helper methods

  private async getApplications(): Promise<App[]> {
    // Applications backup not implemented - requires MCP client context
    // Applications can be reinstalled from Marketplace
    return []
  }

  private downloadFile(content: string, filename: string): void {
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  private async readBackupFile(): Promise<TomoBackup | null> {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'

      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (!file) {
          resolve(null)
          return
        }

        try {
          const content = await file.text()
          const backup = JSON.parse(content) as TomoBackup
          resolve(backup)
        } catch {
          resolve(null)
        }
      }

      input.oncancel = () => resolve(null)
      input.click()
    })
  }

  private isCompatibleVersion(version: string): boolean {
    // For now, accept any 1.x version
    return version.startsWith('1.')
  }

  private formatDate(date: Date): string {
    return date.toISOString().replace(/[:.]/g, '-').slice(0, 19)
  }

  private generateChecksum(data: object): string {
    // Simple checksum based on JSON string length and char codes
    const str = JSON.stringify(data)
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16)
  }

  private async restoreSettings(settings: UserSettings): Promise<void> {
    // Restore each settings section
    await settingsService.updateSettings('security', settings.security)
    await settingsService.updateSettings('ui', settings.ui)
    await settingsService.updateSettings('system', settings.system)
  }

  /**
   * Restore servers from backup using MCP backend
   */
  private async restoreServers(
    mcpClient: MCPClient,
    servers: ServerConnection[],
    existingServers: ServerConnection[],
    overwrite: boolean
  ): Promise<{ restored: number; skipped: number; errors: string[] }> {
    let restored = 0
    let skipped = 0
    const errors: string[] = []

    for (const server of servers) {
      try {
        const existing = existingServers.find(s =>
          s.host === server.host && s.port === server.port
        )

        if (existing && !overwrite) {
          skipped++
        } else {
          // Add server via MCP backend
          const response = await mcpClient.callTool<{ success: boolean; message?: string }>('add_server', {
            server_id: existing?.id || crypto.randomUUID(),
            name: server.name,
            host: server.host,
            port: server.port,
            username: server.username,
            auth_type: server.auth_type,
            // Note: credentials are not included in backup for security
          })

          if (response.data?.success) {
            restored++
          } else {
            errors.push(`Failed to restore server ${server.name}: ${response.data?.message || 'Unknown error'}`)
          }
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
    _overwrite: boolean
  ): Promise<{ restored: number; skipped: number; errors: string[] }> {
    // Applications restore would need MCP integration
    // For now, just count them as skipped
    return {
      restored: 0,
      skipped: applications.length,
      errors: applications.length > 0
        ? ['Application restore not yet implemented - use Marketplace to reinstall']
        : []
    }
  }
}

export const tomoBackupService = new TomoBackupService()
