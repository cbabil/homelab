/**
 * Marketplace Service
 *
 * Service layer for marketplace repository and app management via MCP tools.
 * Provides type-safe access to the marketplace backend functionality.
 */

import { HomelabMCPClient } from './mcpClient'
import type {
  MarketplaceRepo,
  MarketplaceApp,
  MarketplaceCategory,
  SearchFilters,
  MarketplaceSearchResult,
  RepoType,
  AppRating
} from '@/types/marketplace'

/**
 * Get MCP client instance
 */
function getMcpClient(): HomelabMCPClient {
  const serverUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp'
  return new HomelabMCPClient(serverUrl)
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
  return await callTool<{ appCount: number }>('sync_repo', { repo_id: repoId })
}

// ────────────────────────────────────────────────────────────────────────────
// App Search and Discovery
// ────────────────────────────────────────────────────────────────────────────

/**
 * Search marketplace apps with filters
 */
export async function searchApps(filters: SearchFilters = {}): Promise<MarketplaceSearchResult> {
  return await callTool<MarketplaceSearchResult>('search_marketplace', {
    search: filters.search,
    category: filters.category,
    tags: filters.tags,
    featured: filters.featured,
    sort_by: filters.sortBy || 'name',
    limit: 50
  })
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
  return await callTool<MarketplaceCategory[]>('get_marketplace_categories', {})
}

/**
 * Get featured marketplace apps
 */
export async function getFeaturedApps(limit: number = 10): Promise<MarketplaceApp[]> {
  return await callTool<MarketplaceApp[]>('get_featured_apps', { limit })
}

/**
 * Get trending marketplace apps
 */
export async function getTrendingApps(limit: number = 10): Promise<MarketplaceApp[]> {
  return await callTool<MarketplaceApp[]>('get_trending_apps', { limit })
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

  return await callTool<AppRating>('rate_marketplace_app', {
    app_id: appId,
    user_id: userId,
    rating
  })
}

// ────────────────────────────────────────────────────────────────────────────
// App Import
// ────────────────────────────────────────────────────────────────────────────

/**
 * Import result from backend
 */
interface ImportResult {
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
): Promise<ImportResult> {
  return await callTool<ImportResult>('import_marketplace_app', {
    app_id: appId,
    user_id: userId
  })
}

/**
 * Get list of app IDs already imported to local catalog
 */
export async function getImportedAppIds(): Promise<string[]> {
  return await callTool<string[]>('get_imported_app_ids', {})
}
