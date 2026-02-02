/**
 * Marketplace Service
 *
 * Service layer for marketplace repository and app management via MCP tools.
 * Provides type-safe access to the marketplace backend functionality.
 * Includes caching for frequently accessed data.
 */

import { TomoMCPClient } from './mcpClient'
import type {
  MarketplaceRepo,
  MarketplaceApp,
  MarketplaceCategory,
  SearchFilters,
  MarketplaceSearchResult,
  RepoType,
  AppRating
} from '@/types/marketplace'

// ────────────────────────────────────────────────────────────────────────────
// Cache Implementation
// ────────────────────────────────────────────────────────────────────────────

interface CacheEntry<T> {
  data: T
  expiry: number
}

const CACHE_TTL = {
  categories: 5 * 60 * 1000,      // 5 minutes
  featured: 2 * 60 * 1000,        // 2 minutes
  trending: 2 * 60 * 1000,        // 2 minutes
  search: 1 * 60 * 1000,          // 1 minute
  importedIds: 30 * 1000          // 30 seconds (changes more often)
}

const cache = new Map<string, CacheEntry<unknown>>()

function getCacheKey(prefix: string, params?: Record<string, unknown>): string {
  if (!params || Object.keys(params).length === 0) {
    return prefix
  }
  return `${prefix}:${JSON.stringify(params)}`
}

function getFromCache<T>(key: string): T | null {
  const entry = cache.get(key)
  if (!entry) return null
  if (Date.now() > entry.expiry) {
    cache.delete(key)
    return null
  }
  return entry.data as T
}

function setInCache<T>(key: string, data: T, ttl: number): void {
  cache.set(key, { data, expiry: Date.now() + ttl })
}

/**
 * Clear all marketplace cache (call after mutations like sync, import, rate)
 */
export function clearMarketplaceCache(): void {
  cache.clear()
}

/**
 * Clear specific cache entries by prefix
 */
export function clearCacheByPrefix(prefix: string): void {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) {
      cache.delete(key)
    }
  }
}

/**
 * Get MCP client instance
 */
function getMcpClient(): TomoMCPClient {
  const serverUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp'
  return new TomoMCPClient(serverUrl)
}

/**
 * Backend tool response format
 */
interface ToolResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

/**
 * Helper to call MCP tool with auto-connect
 */
async function callTool<T>(name: string, params: Record<string, unknown>): Promise<T> {
  const client = getMcpClient()

  try {
    await client.connect()
    const response = await client.callTool<unknown>(name, params)

    if (!response.success) {
      throw new Error(response.error || response.message || 'MCP call failed')
    }

    // The MCP response wraps the tool's response
    // Tool returns: { success: true, data: <actual_data> }
    // But sometimes it might return the data directly
    const toolResponse = response.data as ToolResponse<T> | T

    // Check if it's a wrapped response
    if (toolResponse && typeof toolResponse === 'object' && 'success' in toolResponse) {
      const wrapped = toolResponse as ToolResponse<T>
      if (!wrapped.success) {
        throw new Error(wrapped.error || wrapped.message || 'Tool call failed')
      }
      return wrapped.data as T
    }

    // Otherwise assume it's the direct data
    return toolResponse as T
  } finally {
    await client.disconnect()
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Repository Management
// ────────────────────────────────────────────────────────────────────────────

/**
 * List all marketplace repositories
 */
export async function getRepos(): Promise<MarketplaceRepo[]> {
  return await callTool<MarketplaceRepo[]>('list_repos', {})
}

/**
 * Add a new marketplace repository
 */
export async function addRepo(
  name: string,
  url: string,
  repoType: RepoType = 'community',
  branch: string = 'main'
): Promise<MarketplaceRepo> {
  return await callTool<MarketplaceRepo>('add_repo', {
    name,
    url,
    repo_type: repoType,
    branch
  })
}

/**
 * Remove a marketplace repository
 */
export async function removeRepo(repoId: string): Promise<void> {
  await callTool<void>('remove_repo', { repo_id: repoId })
}

/**
 * Sync apps from a repository
 */
export async function syncRepo(repoId: string): Promise<{ appCount: number }> {
  const result = await callTool<{ appCount: number }>('sync_repo', { repo_id: repoId })
  // Clear cache after syncing as app data may have changed
  clearMarketplaceCache()
  return result
}

/**
 * Enable or disable a marketplace repository
 */
export async function toggleRepo(repoId: string, enabled: boolean): Promise<{ enabled: boolean }> {
  const result = await callTool<{ enabled: boolean }>('toggle_repo', { repo_id: repoId, enabled })
  // Clear cache as app visibility may have changed
  clearMarketplaceCache()
  return result
}

// ────────────────────────────────────────────────────────────────────────────
// App Search and Discovery
// ────────────────────────────────────────────────────────────────────────────

/**
 * Search marketplace apps with filters
 */
export async function searchApps(filters: SearchFilters = {}): Promise<MarketplaceSearchResult> {
  const cacheKey = getCacheKey('search', filters as Record<string, unknown>)
  const cached = getFromCache<MarketplaceSearchResult>(cacheKey)
  if (cached) return cached

  const result = await callTool<MarketplaceSearchResult>('search_marketplace', {
    search: filters.search,
    category: filters.category,
    tags: filters.tags,
    repo_id: filters.repoId,
    featured: filters.featured,
    sort_by: filters.sortBy || 'name',
    limit: 500
  })

  setInCache(cacheKey, result, CACHE_TTL.search)
  return result
}

/**
 * Get a single marketplace app by ID
 */
export async function getApp(appId: string): Promise<MarketplaceApp> {
  return await callTool<MarketplaceApp>('get_marketplace_app', { app_id: appId })
}

/**
 * Get all marketplace categories with app counts
 */
export async function getCategories(): Promise<MarketplaceCategory[]> {
  const cacheKey = 'categories'
  const cached = getFromCache<MarketplaceCategory[]>(cacheKey)
  if (cached) return cached

  const result = await callTool<MarketplaceCategory[]>('get_marketplace_categories', {})
  setInCache(cacheKey, result, CACHE_TTL.categories)
  return result
}

/**
 * Get featured marketplace apps
 */
export async function getFeaturedApps(limit: number = 10): Promise<MarketplaceApp[]> {
  const cacheKey = getCacheKey('featured', { limit })
  const cached = getFromCache<MarketplaceApp[]>(cacheKey)
  if (cached) return cached

  const result = await callTool<MarketplaceApp[]>('get_featured_apps', { limit })
  setInCache(cacheKey, result, CACHE_TTL.featured)
  return result
}

/**
 * Get trending marketplace apps
 */
export async function getTrendingApps(limit: number = 10): Promise<MarketplaceApp[]> {
  const cacheKey = getCacheKey('trending', { limit })
  const cached = getFromCache<MarketplaceApp[]>(cacheKey)
  if (cached) return cached

  const result = await callTool<MarketplaceApp[]>('get_trending_apps', { limit })
  setInCache(cacheKey, result, CACHE_TTL.trending)
  return result
}

// ────────────────────────────────────────────────────────────────────────────
// Ratings
// ────────────────────────────────────────────────────────────────────────────

/**
 * Rate a marketplace app (1-5 stars)
 */
export async function rateApp(
  appId: string,
  userId: string,
  rating: number
): Promise<AppRating> {
  if (rating < 1 || rating > 5) {
    throw new Error('Rating must be between 1 and 5')
  }

  const result = await callTool<AppRating>('rate_marketplace_app', {
    app_id: appId,
    user_id: userId,
    rating
  })
  // Clear trending cache as rating affects trending order
  clearCacheByPrefix('trending')
  return result
}

// ────────────────────────────────────────────────────────────────────────────
// Import App to Catalog
// ────────────────────────────────────────────────────────────────────────────

/**
 * Import result from backend
 */
interface ImportAppResult {
  app_id: string
  app_name: string
  version: string
  category: string
}

/**
 * Import a marketplace app to local applications catalog
 */
export async function importApp(
  appId: string,
  userId: string
): Promise<ImportAppResult> {
  const result = await callTool<ImportAppResult>('import_app', {
    app_id: appId,
    user_id: userId
  })
  return result
}

/**
 * Compare semantic versions
 * Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
 */
export function compareVersions(v1: string, v2: string): number {
  // Clean version strings (remove 'v' prefix if present)
  const clean = (v: string) => v.replace(/^v/, '').trim()
  const a = clean(v1).split('.').map(n => parseInt(n, 10) || 0)
  const b = clean(v2).split('.').map(n => parseInt(n, 10) || 0)

  const maxLen = Math.max(a.length, b.length)
  for (let i = 0; i < maxLen; i++) {
    const numA = a[i] || 0
    const numB = b[i] || 0
    if (numA > numB) return 1
    if (numA < numB) return -1
  }
  return 0
}

/**
 * Check if marketplace version is newer than installed version
 */
export function hasUpdate(marketplaceVersion: string, installedVersion: string): boolean {
  return compareVersions(marketplaceVersion, installedVersion) > 0
}
