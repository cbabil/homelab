/**
 * Marketplace Types
 *
 * Type definitions for Git-based app marketplace.
 * Matches backend Pydantic models with camelCase aliases.
 */

export type RepoType = 'official' | 'community' | 'personal'
export type RepoStatus = 'active' | 'syncing' | 'error' | 'disabled'

/**
 * Marketplace repository configuration and status
 */
export interface MarketplaceRepo {
  id: string
  name: string
  url: string
  branch: string
  repoType: RepoType
  enabled: boolean
  status: RepoStatus
  lastSynced?: string
  appCount: number
  errorMessage?: string
  createdAt: string
  updatedAt: string
}

/**
 * Docker container port mapping
 */
export interface AppPort {
  container: number
  host: number
  protocol: string
}

/**
 * Docker container volume mapping
 */
export interface AppVolume {
  hostPath: string
  containerPath: string
  readonly: boolean
}

/**
 * Application environment variable configuration
 */
export interface AppEnvVar {
  name: string
  description?: string
  required: boolean
  default?: string
}

/**
 * Docker container configuration
 */
export interface DockerConfig {
  image: string
  ports: AppPort[]
  volumes: AppVolume[]
  environment: AppEnvVar[]
  restartPolicy: string
  networkMode?: string
  privileged: boolean
  capabilities: string[]
}

/**
 * Application system requirements
 */
export interface AppRequirements {
  minRam?: number
  minStorage?: number
  architectures: string[]
}

/**
 * Marketplace application with full metadata and configuration
 */
export interface MarketplaceApp {
  id: string
  name: string
  description: string
  longDescription?: string
  version: string
  category: string
  tags: string[]
  icon?: string
  author: string
  license: string
  maintainers: string[]
  repository?: string
  documentation?: string
  repoId: string
  docker: DockerConfig
  requirements: AppRequirements
  installCount: number
  avgRating?: number
  ratingCount: number
  featured: boolean
  createdAt: string
  updatedAt: string
}

/**
 * User rating for a marketplace application
 */
export interface AppRating {
  id: string
  appId: string
  userId: string
  rating: number
  createdAt: string
  updatedAt: string
}

/**
 * Marketplace category with app count
 */
export interface MarketplaceCategory {
  id: string
  name: string
  count: number
}

/**
 * Search filter options for marketplace apps
 */
export interface SearchFilters {
  search?: string
  category?: string
  tags?: string[]
  repoId?: string
  featured?: boolean
  sortBy?: SortOption
  sortOrder?: 'asc' | 'desc'
}

/**
 * Available sort options for marketplace apps
 */
export type SortOption = 'name' | 'rating' | 'popularity' | 'updated'

/**
 * Search result containing apps and total count
 */
export interface MarketplaceSearchResult {
  apps: MarketplaceApp[]
  total: number
}
