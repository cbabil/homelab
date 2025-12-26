/**
 * Cache Manager
 *
 * Handles caching functionality for data services.
 * Provides cache validation, storage, and cleanup operations.
 */

import { DataServiceOptions } from '@/types/dataService'

export interface CacheEntry {
  data: unknown
  timestamp: number
}

export class CacheManager {
  private cache: Map<string, CacheEntry>
  private cacheTimeout: number

  constructor(options: DataServiceOptions = {}) {
    this.cache = new Map()
    this.cacheTimeout = options.cacheTimeout || 300000 // 5 minutes default
  }

  /**
   * Generate cache key from parameters
   */
  getCacheKey(params: Record<string, unknown> = {}): string {
    return JSON.stringify(params)
  }

  /**
   * Check if cached data is still valid
   */
  isCacheValid(key: string): boolean {
    const cached = this.cache.get(key)
    if (!cached) return false

    const now = Date.now()
    return (now - cached.timestamp) < this.cacheTimeout
  }

  /**
   * Get cached data if valid
   */
  getCachedData<T>(key: string): T | null {
    if (this.isCacheValid(key)) {
      return this.cache.get(key)?.data as T || null
    }
    return null
  }

  /**
   * Set data in cache
   */
  setCachedData(key: string, data: unknown): void {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Remove expired entries from cache
   */
  cleanupExpired(): void {
    const now = Date.now()
    for (const [key, entry] of this.cache.entries()) {
      if ((now - entry.timestamp) >= this.cacheTimeout) {
        this.cache.delete(key)
      }
    }
  }
}