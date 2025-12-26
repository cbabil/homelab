/**
 * Data Service Types
 *
 * Base interfaces and types for extensible data service layer.
 * Provides consistent patterns for data fetching, error handling, and loading states.
 */

export interface ServiceResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

export interface FilterOptions {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface LoadingState {
  isLoading: boolean
  error: string | null
  lastUpdated: Date | null
}

export interface DataServiceOptions {
  autoRetry?: boolean
  retryCount?: number
  retryDelay?: number
  cacheTimeout?: number
}

export interface BaseDataService<T, F extends FilterOptions = FilterOptions> {
  getAll(filter?: F): Promise<ServiceResponse<T[]>>
  getById(id: string): Promise<ServiceResponse<T>>
  create?(data: Partial<T>): Promise<ServiceResponse<T>>
  update?(id: string, data: Partial<T>): Promise<ServiceResponse<T>>
  delete?(id: string): Promise<ServiceResponse<void>>
  refresh(): Promise<void>
  getLoadingState(): LoadingState
}

export interface CacheableService {
  clearCache(): void
  getCacheKey(params?: Record<string, unknown>): string
  isCacheValid(key: string): boolean
}