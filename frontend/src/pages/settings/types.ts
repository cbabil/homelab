/**
 * Shared Settings Types
 * 
 * Common type definitions used across settings components.
 */

export interface Session {
  id: string
  userId: string
  username: string
  status: 'active' | 'idle' | 'expired' | 'terminated'
  started: Date
  lastActivity: Date
  expiresAt: Date
  location: string
  ip: string
  isCurrent: boolean
}

export type SortKey = 'status' | 'userId' | 'sessionId' | 'started' | 'lastActivity' | 'expiresAt' | 'location' | 'actions'

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