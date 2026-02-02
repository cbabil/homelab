/**
 * Helper functions for retention settings operations
 */

import { mcpLogger } from '@/services/systemLogger'
import {
  RetentionSettings,
  RETENTION_LIMITS,
  RetentionPreviewResult,
  RetentionOperationResult
} from '@/types/settings'
import {
  GetSettingsResponse,
  UpdateSettingsResponse,
  PreviewResponse,
  CleanupResponse,
  CSRFTokenResponse,
  DEFAULT_RETENTION_SETTINGS
} from './retentionSettingsTypes'
import type { MCPClient } from '@/types/mcp'

/** Minimal client interface for retention helpers - only needs callTool */
type RetentionMCPClient = Pick<MCPClient, 'callTool'>

/** Validate retention settings against limits */
export function validateRetentionSettings(retentionSettings: RetentionSettings): {
  valid: boolean
  error?: string
} {
  if (
    retentionSettings.log_retention < RETENTION_LIMITS.LOG_MIN ||
    retentionSettings.log_retention > RETENTION_LIMITS.LOG_MAX
  ) {
    return {
      valid: false,
      error: `Log retention must be between ${RETENTION_LIMITS.LOG_MIN}-${RETENTION_LIMITS.LOG_MAX} days`
    }
  }

  if (
    retentionSettings.data_retention < RETENTION_LIMITS.DATA_MIN ||
    retentionSettings.data_retention > RETENTION_LIMITS.DATA_MAX
  ) {
    return {
      valid: false,
      error: `Data retention must be between ${RETENTION_LIMITS.DATA_MIN}-${RETENTION_LIMITS.DATA_MAX} days`
    }
  }

  return { valid: true }
}

/** Parse settings from backend response */
export function parseSettingsResponse(response: GetSettingsResponse): RetentionSettings {
  const data = response?.data
  if (data) {
    return {
      log_retention: data.log_retention,
      data_retention: data.data_retention,
      last_updated: data.last_updated,
      updated_by_user_id: data.updated_by_user_id
    }
  }
  return DEFAULT_RETENTION_SETTINGS
}

/** Build preview result from response data */
export function buildPreviewResult(data: PreviewResponse['data']): RetentionPreviewResult {
  if (!data) {
    return {
      logEntriesAffected: 0,
      otherDataAffected: 0,
      estimatedSpaceFreed: '0 MB',
      affectedTables: []
    }
  }
  return {
    logEntriesAffected: data.affected_records,
    otherDataAffected: 0,
    estimatedSpaceFreed: `${data.estimated_space_freed_mb.toFixed(1)} MB`,
    affectedTables: [data.retention_type]
  }
}

/** Get mock preview result for offline mode */
export function getMockPreview(): RetentionPreviewResult {
  return {
    logEntriesAffected: 0,
    otherDataAffected: 0,
    estimatedSpaceFreed: '0 MB',
    affectedTables: ['log_entries']
  }
}

/** Fetch CSRF token from backend */
export async function fetchCSRFToken(
  client: RetentionMCPClient
): Promise<string | null> {
  try {
    const response = await client.callTool<CSRFTokenResponse>('get_csrf_token', { params: {} })

    if (response.success) {
      const responseData = response.data as CSRFTokenResponse
      const token = responseData?.data?.csrf_token || null
      mcpLogger.info('[useRetentionSettings] CSRF token obtained')
      return token
    }
    mcpLogger.error('[useRetentionSettings] Failed to get CSRF token', { error: response.error })
    return null
  } catch (err) {
    mcpLogger.error('[useRetentionSettings] CSRF token request failed', { error: err })
    return null
  }
}

/** Execute cleanup operation via MCP */
export async function executeCleanup(
  client: RetentionMCPClient,
  retentionType: string,
  token: string
): Promise<RetentionOperationResult> {
  const response = await client.callTool<CleanupResponse>('perform_retention_cleanup', {
    params: { retention_type: retentionType, csrf_token: token }
  })

  if (response.success) {
    const responseData = response.data as CleanupResponse
    const data = responseData?.data

    if (data) {
      mcpLogger.info('[useRetentionSettings] Cleanup completed', {
        records: data.records_affected,
        space: data.space_freed_mb
      })

      return {
        success: true,
        operation: 'execute',
        deletedCounts: { [data.retention_type]: data.records_affected }
      }
    }
  }

  const responseData = response.data as CleanupResponse
  mcpLogger.error('[useRetentionSettings] Cleanup failed', { error: response.error })
  return { success: false, operation: 'execute', error: responseData?.message || 'Cleanup failed' }
}

/** Execute preview operation via MCP */
export async function executePreview(
  client: RetentionMCPClient,
  retentionType: string
): Promise<{
  success: boolean
  preview?: RetentionPreviewResult
  error?: string
}> {
  const response = await client.callTool<PreviewResponse>('preview_retention_cleanup', {
    params: { retention_type: retentionType }
  })

  const responseData = response.data as PreviewResponse

  if (response.success && responseData?.data) {
    const preview = buildPreviewResult(responseData.data)
    mcpLogger.info('[useRetentionSettings] Preview completed', {
      affected: responseData.data.affected_records
    })
    return { success: true, preview }
  }

  mcpLogger.error('[useRetentionSettings] Preview failed', { error: response.error })
  return { success: false, error: responseData?.message || 'Preview failed' }
}

/** Update settings via MCP */
export async function updateSettingsViaBackend(
  client: RetentionMCPClient,
  newSettings: RetentionSettings
): Promise<{ success: boolean; data?: RetentionSettings; error?: string }> {
  const response = await client.callTool<UpdateSettingsResponse>('update_retention_settings', {
    params: {
      log_retention: newSettings.log_retention,
      data_retention: newSettings.data_retention
    }
  })

  if (response.success) {
    const responseData = response.data as UpdateSettingsResponse
    mcpLogger.info('[useRetentionSettings] Settings updated on backend')
    return { success: true, data: responseData?.data }
  }

  const responseData = response.data as UpdateSettingsResponse
  return { success: false, error: responseData?.error || 'Failed to update settings' }
}
