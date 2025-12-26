/**
 * Applications Data Service
 *
 * Service layer for application catalog operations via MCP tools.
 */

import {
  Film,
  Briefcase,
  BarChart3,
  Shield,
  Zap,
  HardDrive,
  AppWindow
} from 'lucide-react'

import { BaseDataService } from './baseDataService'
import { MCPClient } from '@/types/mcp'
import { ServiceResponse, DataServiceOptions } from '@/types/dataService'
import { App, AppCategory, AppFilter, AppRequirements, AppSearchResult } from '@/types/app'

type LucideIconType = typeof Film

interface RawAppCategory {
  id: string
  name: string
  description: string
  icon: string
  color: string
}

interface RawAppRequirements {
  min_ram?: string
  min_storage?: string
  required_ports?: number[]
  dependencies?: string[]
  supported_architectures?: string[]
}

interface RawApp {
  id: string
  name: string
  description: string
  long_description?: string
  version: string
  category: RawAppCategory
  tags?: string[]
  icon?: string
  screenshots?: string[]
  author: string
  repository?: string
  documentation?: string
  license: string
  requirements?: RawAppRequirements
  status: App['status']
  install_count?: number
  rating?: number
  featured?: boolean
  created_at: string
  updated_at: string
  connected_server_id?: string | null
}

interface RawSearchResult {
  apps: RawApp[]
  total: number
  page: number
  limit: number
  filters: Record<string, unknown>
}

const ICON_MAP: Record<string, LucideIconType> = {
  film: Film,
  media: Film,
  briefcase: Briefcase,
  productivity: Briefcase,
  'bar-chart-3': BarChart3,
  monitoring: BarChart3,
  shield: Shield,
  security: Shield,
  zap: Zap,
  development: Zap,
  'hard-drive': HardDrive,
  storage: HardDrive
}

function resolveCategoryIcon(iconName?: string): LucideIconType {
  if (!iconName) {
    return AppWindow
  }
  const normalized = iconName.toLowerCase()
  return ICON_MAP[normalized] || ICON_MAP[normalized.replace(/-/g, '_')] || AppWindow
}

function mapRequirements(raw?: RawAppRequirements): AppRequirements {
  if (!raw) {
    return {}
  }

  return {
    minRam: raw.min_ram,
    minStorage: raw.min_storage,
    requiredPorts: raw.required_ports,
    dependencies: raw.dependencies,
    supportedArchitectures: raw.supported_architectures
  }
}

function mapCategory(raw: RawAppCategory): AppCategory {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description,
    icon: resolveCategoryIcon(raw.icon),
    color: raw.color
  }
}

function mapApp(raw: RawApp): App {
  const category = mapCategory(raw.category)

  return {
    id: raw.id,
    name: raw.name,
    description: raw.description,
    longDescription: raw.long_description,
    version: raw.version,
    category,
    tags: raw.tags ?? [],
    icon: raw.icon,
    screenshots: raw.screenshots,
    author: raw.author,
    repository: raw.repository,
    documentation: raw.documentation,
    license: raw.license,
    requirements: mapRequirements(raw.requirements),
    status: raw.status,
    installCount: raw.install_count,
    rating: raw.rating,
    featured: raw.featured ?? false,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    connectedServerId: raw.connected_server_id ?? undefined
  }
}

function deriveFilterPayload(filter?: AppFilter): Record<string, unknown> {
  if (!filter) {
    return {}
  }

  const payload: Record<string, unknown> = {}

  if (filter.category) payload.category = filter.category
  if (filter.status) payload.status = filter.status
  if (filter.search) payload.search = filter.search
  if (filter.featured !== undefined) payload.featured = filter.featured
  if (filter.tags && filter.tags.length > 0) payload.tags = filter.tags
  if (filter.sortBy) payload.sort_by = filter.sortBy
  if (filter.sortOrder) payload.sort_order = filter.sortOrder

  return payload
}

export class ApplicationsDataService extends BaseDataService {
  constructor(client: MCPClient, options?: DataServiceOptions) {
    super(client, options)
  }

  /**
   * Search the application catalog using MCP tools.
   */
  async search(filter?: AppFilter): Promise<ServiceResponse<AppSearchResult>> {
    const cacheKey = this.getCacheKey({ filter })
    const cached = this.getCachedData<AppSearchResult>(cacheKey)

    if (cached) {
      return { success: true, data: cached, message: 'Applications retrieved from cache' }
    }

    const filtersPayload = deriveFilterPayload(filter)
    const response = await this.callTool<any>('search_apps', { filters: filtersPayload })

    if (!response.success) {
      return {
        success: false,
        error: response.error || 'Failed to fetch applications',
        message: response.message || 'Failed to fetch applications'
      }
    }

    const payload = response.data as { success: boolean; data?: RawSearchResult; error?: string; message?: string }

    if (!payload?.success) {
      return {
        success: false,
        error: payload?.error || 'Failed to fetch applications',
        message: payload?.message || 'Failed to fetch applications'
      }
    }

    const rawResult: RawSearchResult = payload.data ?? {
      apps: [],
      total: 0,
      page: 1,
      limit: 0,
      filters: {}
    }

    const apps = rawResult.apps.map(mapApp)
    const searchResult: AppSearchResult = {
      apps,
      total: rawResult.total,
      page: rawResult.page,
      limit: rawResult.limit,
      filters: filter || {}
    }

    this.setCachedData(cacheKey, searchResult)
    return {
      success: true,
      data: searchResult,
      message: `Retrieved ${rawResult.total} applications`
    }
  }

  /**
   * Retrieve a single application by identifier.
   */
  async getById(id: string): Promise<ServiceResponse<App>> {
    const result = await this.callTool<any>('get_app_details', { app_id: id })

    if (!result.success) {
      return {
        success: false,
        error: result.error || 'Failed to fetch application',
        message: result.message || 'Failed to fetch application'
      }
    }

    const payload = result.data as { success: boolean; data?: RawApp; error?: string; message?: string }
    if (!payload?.success || !payload.data) {
      return {
        success: false,
        error: payload?.error || 'Invalid response format',
        message: payload?.message || 'Failed to fetch application'
      }
    }

    return {
      success: true,
      data: mapApp(payload.data),
      message: 'Application retrieved'
    }
  }
}
