/**
 * Application Types
 *
 * Type definitions for the tomo application marketplace.
 */

import { LucideIcon } from 'lucide-react'

export interface App {
  id: string
  name: string
  description: string
  longDescription?: string
  version: string
  category: AppCategory
  tags: string[]
  icon?: string
  screenshots?: string[]
  author: string
  repository?: string
  documentation?: string
  license: string
  requirements: AppRequirements
  status: AppStatus
  installCount?: number
  rating?: number
  featured?: boolean
  createdAt: string
  updatedAt: string
  connectedServerId?: string | null
}

export interface AppRequirements {
  minRam?: string
  minStorage?: string
  requiredPorts?: number[]
  dependencies?: string[]
  supportedArchitectures?: string[]
}

export interface AppCategory {
  id: string
  name: string
  description: string
  icon: LucideIcon
  color: string
}

export type AppStatus = 
  | 'available'
  | 'installed' 
  | 'installing'
  | 'updating'
  | 'removing'
  | 'error'
  | 'deprecated'

export interface AppInstallation {
  appId: string
  status: AppStatus
  version: string
  installedAt: string
  lastUpdated?: string
  config?: Record<string, unknown>
  logs?: string[]
}

export interface AppFilter {
  category?: string
  tags?: string[]
  status?: AppStatus
  search?: string
  featured?: boolean
  sortBy?: 'name' | 'popularity' | 'rating' | 'updated'
  sortOrder?: 'asc' | 'desc'
}

export interface AppSearchResult {
  apps: App[]
  total: number
  page: number
  limit: number
  filters: AppFilter
}
