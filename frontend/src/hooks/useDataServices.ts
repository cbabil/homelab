/**
 * Data Services Hook
 *
 * React hook for accessing data services with MCP client integration.
 * Provides consistent access to all data services throughout the application.
 */

import { useMemo } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { DataServiceFactory } from '@/services/dataServiceFactory'
import { LogsDataService } from '@/services/logsDataService'
import { ApplicationsDataService } from '@/services/applicationsDataService'

export interface UseDataServicesReturn {
  logs: LogsDataService
  applications: ApplicationsDataService
  factory: DataServiceFactory
  isConnected: boolean
}

export function useDataServices(): UseDataServicesReturn {
  const { client, isConnected } = useMCP()

  const factory = useMemo(() => {
    // Create MCP client adapter for service factory
    const mcpClientAdapter = {
      callTool: client.callTool.bind(client),
      isConnected: client.isConnected?.bind(client) || (() => isConnected),
      connect: client.connect?.bind(client) || (() => Promise.resolve()),
      disconnect: client.disconnect?.bind(client) || (() => Promise.resolve()),
      subscribeTo: client.subscribeTo?.bind(client) || (() => new EventSource(''))
    }

    return new DataServiceFactory(mcpClientAdapter, {
      enableCaching: true,
      defaultOptions: {
        autoRetry: true,
        retryCount: 3,
        retryDelay: 1000,
        cacheTimeout: 300000 // 5 minutes
      }
    })
  }, [client, isConnected])

  const services = useMemo(() => ({
    logs: factory.getLogsService(),
    applications: factory.getApplicationsService(),
    factory,
    isConnected
  }), [factory, isConnected])

  return services
}

// Individual service hooks for convenience
export function useLogsService(): {
  logsService: LogsDataService
  isConnected: boolean
} {
  const { logs, isConnected } = useDataServices()
  return { logsService: logs, isConnected }
}

export function useApplicationsService(): {
  applicationsService: ApplicationsDataService
  isConnected: boolean
} {
  const { applications, isConnected } = useDataServices()
  return { applicationsService: applications, isConnected }
}
