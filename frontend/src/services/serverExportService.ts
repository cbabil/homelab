/**
 * Server Export Service
 * 
 * Handles exporting and importing server configurations in JSON format
 * for easy backup and sharing of server data.
 */

import { ServerConnection } from '@/types/server'

interface ExportResult {
  success: boolean
  message: string
  filename?: string
}

class ServerExportService {
  /**
   * Export user-added servers to a downloadable JSON file
   */
  exportUserServers(servers: ServerConnection[]): ExportResult {
    try {
      // Filter out mock servers (assume they start with 'srv-')
      const userServers = servers.filter(server => !server.id.startsWith('srv-'))
      
      if (userServers.length === 0) {
        // If no user servers, export all servers for demonstration
        const filename = `tomo_servers_demo_${new Date().toISOString().split('T')[0]}.json`
        
        this.downloadFile(JSON.stringify(servers, null, 2), filename, 'application/json')
        
        return {
          success: true,
          message: `No user-added servers found. Exported all ${servers.length} servers for demonstration.`,
          filename
        }
      }

      const filename = `tomo_servers_${new Date().toISOString().split('T')[0]}.json`
      
      this.downloadFile(JSON.stringify(userServers, null, 2), filename, 'application/json')
      
      return {
        success: true,
        message: `Exported ${userServers.length} servers`,
        filename
      }
    } catch (error) {
      return {
        success: false,
        message: `Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }


  /**
   * Import servers from a JSON file upload
   */
  importServers(): Promise<ServerConnection[]> {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.style.display = 'none'
      
      input.onchange = async (event) => {
        const file = (event.target as HTMLInputElement).files?.[0]
        if (!file) {
          reject(new Error('No file selected'))
          return
        }
        
        try {
          const content = await this.readFileContent(file)
          const servers = this.parseServerFile(content)
          resolve(servers)
        } catch (error) {
          reject(error)
        } finally {
          document.body.removeChild(input)
        }
      }
      
      input.oncancel = () => {
        document.body.removeChild(input)
        reject(new Error('File selection cancelled'))
      }
      
      document.body.appendChild(input)
      input.click()
    })
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
   * Parse JSON file content to extract servers
   */
  private parseServerFile(content: string): ServerConnection[] {
    try {
      const parsed = JSON.parse(content)
      
      // Ensure we have an array
      if (!Array.isArray(parsed)) {
        throw new Error('File must contain an array of servers')
      }
      
      return parsed as ServerConnection[]
    } catch (error) {
      throw new Error(`Invalid JSON format: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Trigger file download in browser
   */
  private downloadFile(content: string, filename: string, mimeType = 'application/json'): void {
    const blob = new Blob([content], { type: mimeType })
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

export const serverExportService = new ServerExportService()