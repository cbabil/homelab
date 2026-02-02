/**
 * Type definitions for retention settings MCP responses
 */

import { RetentionSettings } from '@/types/settings'

// Default settings when backend is unavailable
export const DEFAULT_RETENTION_SETTINGS: RetentionSettings = {
  log_retention: 30,
  data_retention: 90,
}

// Response types for MCP tools
export interface GetSettingsResponse {
  success: boolean
  data?: RetentionSettings
  message?: string
  error?: string
}

export interface UpdateSettingsResponse {
  success: boolean
  data?: RetentionSettings
  message?: string
  error?: string
}

export interface CSRFTokenResponse {
  success: boolean
  data?: { csrf_token: string }
  message?: string
  error?: string
}

export interface PreviewResponse {
  success: boolean
  data?: {
    retention_type: string
    affected_records: number
    oldest_record_date: string | null
    newest_record_date: string | null
    estimated_space_freed_mb: number
    cutoff_date: string
  }
  message?: string
  error?: string
}

export interface CleanupResponse {
  success: boolean
  data?: {
    operation_id: string
    retention_type: string
    records_affected: number
    space_freed_mb: number
    duration_seconds: number
    start_time: string
    end_time: string
  }
  message?: string
  error?: string
}
