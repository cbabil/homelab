/**
 * Data Service Factory
 *
 * Factory for creating and managing data service instances.
 * Provides consistent service instantiation and dependency injection.
 */

import { MCPClient } from '@/types/mcp'
import { DataServiceOptions } from '@/types/dataService'
import { LogsDataService } from './logsDataService'
import { ApplicationsDataService } from './applicationsDataService'

export interface ServiceFactoryOptions {
  defaultOptions?: DataServiceOptions
  enableCaching?: boolean
}

export class DataServiceFactory {
  private client: MCPClient
  private options: ServiceFactoryOptions
  private serviceInstances: Map<string, unknown>

  constructor(client: MCPClient, options: ServiceFactoryOptions = {}) {
    this.client = client
    this.options = {
      defaultOptions: {
        autoRetry: true,
        retryCount: 3,
        retryDelay: 1000,
        cacheTimeout: 300000 // 5 minutes
      },
      enableCaching: true,
      ...options
    }
    this.serviceInstances = new Map()
  }

  /**
   * Get or create logs data service instance
   */
  getLogsService(customOptions?: DataServiceOptions): LogsDataService {
    const serviceKey = 'logs'

    if (this.options.enableCaching && this.serviceInstances.has(serviceKey)) {
      return this.serviceInstances.get(serviceKey) as LogsDataService
    }

    const mergedOptions = {
      ...this.options.defaultOptions,
      ...customOptions
    }

    const service = new LogsDataService(this.client, mergedOptions)

    if (this.options.enableCaching) {
      this.serviceInstances.set(serviceKey, service)
    }

    return service
  }

  /**
   * Get or create applications data service instance
   */
  getApplicationsService(customOptions?: DataServiceOptions): ApplicationsDataService {
    const serviceKey = 'applications'

    if (this.options.enableCaching && this.serviceInstances.has(serviceKey)) {
      return this.serviceInstances.get(serviceKey) as ApplicationsDataService
    }

    const mergedOptions = {
      ...this.options.defaultOptions,
      ...customOptions
    }

    const service = new ApplicationsDataService(this.client, mergedOptions)

    if (this.options.enableCaching) {
      this.serviceInstances.set(serviceKey, service)
    }

    return service
  }

  /**
   * Clear all cached service instances
   */
  clearServiceCache(): void {
    this.serviceInstances.clear()
  }

  /**
   * Clear data caches in all service instances
   */
  clearDataCaches(): void {
    for (const service of this.serviceInstances.values()) {
      if ('clearCache' in service && typeof (service as any).clearCache === 'function') {
        (service as any).clearCache()
      }
    }
  }

  /**
   * Check if client is connected
   */
  isClientConnected(): boolean {
    return this.client.isConnected()
  }

  /**
   * Update client instance (useful for reconnections)
   */
  updateClient(newClient: MCPClient): void {
    this.client = newClient
    this.clearServiceCache() // Force recreation with new client
  }
}
