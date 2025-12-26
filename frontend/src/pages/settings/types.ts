/**
 * Shared Settings Types
 * 
 * Common type definitions used across settings components.
 */

export interface Session {
  id: string
  status: 'active' | 'idle' | 'expired'
  started: Date
  lastActivity: Date
  location: string
  ip: string
}

export type SortKey = 'status' | 'sessionId' | 'started' | 'lastActivity' | 'location' | 'actions'

import type { LucideIcon } from 'lucide-react'

export interface Tab {
  id: string
  label: string
  icon: LucideIcon
}

export interface McpConfig {
  mcpServers: Record<string, {
    command?: string
    args?: string[]
    type: 'stdio' | 'http'
    workingDirectory?: string
    url?: string
    headers?: Record<string, string>
  }>
}