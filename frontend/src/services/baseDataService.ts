/**
 * Base Data Service
 *
 * Abstract base class providing common functionality for data services.
 * Uses composition with CacheManager and LoadingStateManager for modularity.
 */

import { MCPClient, MCPResponse } from '@/types/mcp'
import { ServiceResponse, LoadingState, DataServiceOptions, CacheableService } from '@/types/dataService'
import { CacheManager } from './cacheManager'
import { LoadingStateManager } from './loadingStateManager'

export abstract class BaseDataService implements CacheableService {
  protected client: MCPClient
  protected options: DataServiceOptions
  protected cacheManager: CacheManager
  protected loadingManager: LoadingStateManager

  constructor(client: MCPClient, options: DataServiceOptions = {}) {
    this.client = client
    this.options = {
      autoRetry: true,
      retryCount: 3,
      retryDelay: 1000,
      cacheTimeout: 300000, // 5 minutes
      ...options
    }
    this.cacheManager = new CacheManager(this.options)
    this.loadingManager = new LoadingStateManager()
  }

  protected async callTool<T>(
    toolName: string,
    params: Record<string, unknown> = {}
  ): Promise<ServiceResponse<T>> {
    this.loadingManager.setLoading(true)

    try {
      const response: MCPResponse<T> = await this.client.callTool(toolName, params)

      if (response.success) {
        this.loadingManager.setLoading(false, null)
        return {
          success: true,
          data: response.data,
          message: response.message || 'Operation successful'
        }
      } else {
        this.loadingManager.setLoading(false, response.error || 'Unknown error')
        return {
          success: false,
          error: response.error || 'Operation failed',
          message: response.message || 'Operation failed'
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      this.loadingManager.setLoading(false, errorMessage)
      return {
        success: false,
        error: errorMessage,
        message: 'Service call failed'
      }
    }
  }

  getLoadingState(): LoadingState {
    return this.loadingManager.getLoadingState()
  }

  getCacheKey(params: Record<string, unknown> = {}): string {
    return this.cacheManager.getCacheKey(params)
  }

  isCacheValid(key: string): boolean {
    return this.cacheManager.isCacheValid(key)
  }

  clearCache(): void {
    this.cacheManager.clearCache()
  }

  protected getCachedData<T>(key: string): T | null {
    return this.cacheManager.getCachedData<T>(key)
  }

  protected setCachedData(key: string, data: unknown): void {
    this.cacheManager.setCachedData(key, data)
  }
}