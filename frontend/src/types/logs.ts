/**
 * Log Types
 *
 * Type definitions for log entries and related structures.
 * Enhanced to match backend LogEntry model with metadata support.
 */

import { FilterOptions, PaginatedResponse } from './dataService'

// Frontend log structure
export interface LogEntry {
  id: string
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error' | 'critical'
  source: string
  message: string
  category: 'system' | 'application' | 'security' | 'network'
  tags: string[]
  metadata: Record<string, unknown>
  createdAt: string
  details?: string
}

// Database log structure (from MCP backend) - matches backend LogEntry model
export interface DatabaseLogEntry {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  tags: string[]
  metadata: Record<string, unknown>
  created_at: string
}

// Log filter options extending base FilterOptions
export interface LogFilterOptions extends FilterOptions {
  level?: string
  source?: string
  category?: LogEntry['category']
  tags?: string[]
  dateFrom?: string
  dateTo?: string
  search?: string
}

// MCP response structure
export interface LogsResponse extends PaginatedResponse<DatabaseLogEntry> {
  logs: DatabaseLogEntry[]
  filtered: boolean
}