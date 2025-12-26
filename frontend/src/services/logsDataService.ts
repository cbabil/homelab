/**
 * Logs Data Service
 *
 * Service for fetching and managing log data using MCP client.
 * Provides filtering, caching, and real-time updates for log entries.
 */

import { BaseDataService } from './baseDataService'
import { MCPClient } from '@/types/mcp'
import { ServiceResponse, DataServiceOptions, BaseDataService as IBaseDataService } from '@/types/dataService'
import { LogEntry, DatabaseLogEntry, LogsResponse, LogFilterOptions } from '@/types/logs'

export class LogsDataService extends BaseDataService implements IBaseDataService<LogEntry, LogFilterOptions> {
  constructor(client: MCPClient, options?: DataServiceOptions) {
    super(client, options)
  }

  /**
   * Maps database log entry to frontend format
   */
  private mapDatabaseLogToFrontend(dbLog: DatabaseLogEntry): LogEntry {
    // Determine category from source or tags
    let category: LogEntry['category'] = 'system'
    if (dbLog.source === 'docker' || dbLog.tags.includes('docker')) {
      category = 'application'
    } else if (dbLog.source === 'application' || dbLog.tags.includes('application')) {
      category = 'application'
    } else if (dbLog.tags.includes('security') || dbLog.source.includes('ssh')) {
      category = 'security'
    } else if (dbLog.tags.includes('network')) {
      category = 'network'
    }

    return {
      id: dbLog.id,
      timestamp: dbLog.timestamp,
      level: (dbLog.level.toLowerCase() as LogEntry['level']) || 'info',
      source: dbLog.source,
      message: dbLog.message,
      category,
      tags: typeof dbLog.tags === 'string' ?
        (dbLog.tags ? JSON.parse(dbLog.tags) : []) :
        (dbLog.tags || []),
      metadata: dbLog.metadata,
      createdAt: dbLog.created_at,
      details: (() => {
        const tags = typeof dbLog.tags === 'string' ?
          (dbLog.tags ? JSON.parse(dbLog.tags) : []) :
          (dbLog.tags || [])
        return tags.length > 0 ? `Tags: ${tags.join(', ')}` : undefined
      })()
    }
  }

  /**
   * Get all logs with optional filtering
   */
  async getAll(filter?: LogFilterOptions): Promise<ServiceResponse<LogEntry[]>> {
    // Build MCP tool parameters
    const params: Record<string, unknown> = {}
    if (filter?.level) params.level = filter.level
    if (filter?.source) params.source = filter.source
    if (filter?.limit) params.limit = filter.limit
    if (filter?.page) params.offset = (filter.page - 1) * (filter.limit || 100)

    const result = await this.callTool<any>('get_logs', params)

    console.log('MCP Response:', JSON.stringify(result, null, 2))

    if (!result.success) {
      return {
        success: false,
        error: result.error || 'Failed to fetch logs',
        message: result.message || 'Failed to fetch logs'
      }
    }

    const rawData = result.data

    let toolResponse: any = null

    if (rawData?.content?.[0]?.text) {
      const textPayload = rawData.content[0].text.trim()

      if (textPayload.startsWith('{') || textPayload.startsWith('[')) {
        try {
          toolResponse = JSON.parse(textPayload)
        } catch (error) {
          console.error('Failed to parse logs response:', error)
          return {
            success: false,
            error: 'Failed to parse response',
            message: 'Invalid response format'
          }
        }
      } else {
        return {
          success: false,
          error: textPayload,
          message: textPayload
        }
      }
    } else if (rawData && typeof rawData === 'object') {
      toolResponse = rawData
    } else if (typeof rawData === 'string') {
      const trimmed = rawData.trim()
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          toolResponse = JSON.parse(trimmed)
        } catch (error) {
          console.error('Failed to parse logs response:', error)
          return {
            success: false,
            error: 'Failed to parse response',
            message: 'Invalid response format'
          }
        }
      } else {
        return {
          success: false,
          error: trimmed,
          message: trimmed
        }
      }
    }

    if (toolResponse?.success && toolResponse.data?.logs) {
      const mappedLogs = toolResponse.data.logs.map(log => this.mapDatabaseLogToFrontend(log))
      return {
        success: true,
        data: mappedLogs,
        message: toolResponse.message || `Retrieved ${toolResponse.data.logs.length} log entries`
      }
    }

    console.log('Tool response failed:', toolResponse)
    return {
      success: false,
      error: toolResponse?.error || 'Failed to fetch logs',
      message: toolResponse?.message || 'Failed to fetch logs'
    }
  }

  /**
   * Get single log entry by ID
   */
  async getById(id: string): Promise<ServiceResponse<LogEntry>> {
    const result = await this.callTool<DatabaseLogEntry>('get_log_by_id', { id })

    if (result.success && result.data) {
      const mappedLog = this.mapDatabaseLogToFrontend(result.data)
      return { success: true, data: mappedLog, message: result.message }
    }

    return { success: false, error: result.error, message: result.message }
  }

  /**
   * Refresh logs data and clear cache
   */
  async refresh(): Promise<ServiceResponse<PaginatedResponse<LogEntry>>> {
    this.clearCache()
    return await this.getAll()
  }

  /**
   * Purge all log entries via MCP tool
   */
  async purge(): Promise<ServiceResponse<{ deleted?: number }>> {
    const result = await this.callTool<any>('purge_logs')

    if (!result.success) {
      return {
        success: false,
        error: result.error || 'Failed to purge logs',
        message: result.message || 'Failed to purge logs'
      }
    }

    const rawData = result.data
    let toolResponse: any = null

    // Handle streamed text payloads (content array)
    if (rawData?.content?.[0]?.text) {
      const textPayload = rawData.content[0].text.trim()

      if (textPayload.startsWith('{') || textPayload.startsWith('[')) {
        try {
          toolResponse = JSON.parse(textPayload)
        } catch (error) {
          console.error('Failed to parse purge logs response:', error)
          return {
            success: false,
            error: 'Failed to parse response',
            message: 'Invalid response format'
          }
        }
      } else {
        // Treat plain text response as backend error message
        return {
          success: false,
          error: textPayload,
          message: textPayload
        }
      }
    } else if (rawData && typeof rawData === 'object') {
      toolResponse = rawData
    } else if (typeof rawData === 'string') {
      const trimmed = rawData.trim()
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          toolResponse = JSON.parse(trimmed)
        } catch (error) {
          console.error('Failed to parse purge logs response:', error)
          return {
            success: false,
            error: 'Failed to parse response',
            message: 'Invalid response format'
          }
        }
      } else {
        return {
          success: false,
          error: trimmed,
          message: trimmed
        }
      }
    }

    if (toolResponse?.success) {
      this.clearCache()
      return {
        success: true,
        data: { deleted: toolResponse.deleted },
        message: toolResponse.message || 'Logs purged successfully'
      }
    }

    const fallbackMessage = toolResponse?.message || 'Failed to purge logs'
    const fallbackError = toolResponse?.error || fallbackMessage

    if (!toolResponse) {
      console.error('Unexpected purge logs response shape', rawData)
    }

    return {
      success: false,
      error: fallbackError,
      message: fallbackMessage
    }
  }
}
