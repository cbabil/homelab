/**
 * useInstalledApps Hook
 *
 * Fetches all installed applications with server and app details.
 * Used by the Applications page to display deployed apps.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { useSettingsContext } from '@/providers/SettingsProvider'

export type InstallationStatus =
  | 'pending'
  | 'pulling'
  | 'creating'
  | 'starting'
  | 'running'
  | 'stopped'
  | 'error'

export interface VolumeMount {
  name: string
  destination: string
  mode: string
}

export interface BindMount {
  source: string
  destination: string
  mode: string
}

export interface InstalledAppInfo {
  /** Installation ID */
  id: string
  /** Application ID from catalog */
  appId: string
  /** Display name of the app */
  appName: string
  /** App icon URL */
  appIcon?: string
  /** App version */
  appVersion: string
  /** App description */
  appDescription: string
  /** App category (e.g., automation, media, storage) */
  appCategory: string
  /** Marketplace source (e.g., CasaOS, LinuxServer) */
  appSource: string
  /** Server ID where app is installed */
  serverId: string
  /** Server display name */
  serverName: string
  /** Server hostname/IP for access URL */
  serverHost: string
  /** Docker container ID */
  containerId?: string
  /** Docker container name */
  containerName: string
  /** Current status */
  status: InstallationStatus
  /** Port mappings: containerPort -> hostPort */
  ports: Record<string, number>
  /** Environment variables */
  env: Record<string, string>
  /** Volume mappings from config: containerPath -> hostPath */
  volumes: Record<string, string>
  /** Docker networks the container is attached to */
  networks: string[]
  /** Named volumes */
  namedVolumes: VolumeMount[]
  /** Host bind mounts */
  bindMounts: BindMount[]
  /** When the app was installed */
  installedAt: string
  /** When the app was started */
  startedAt?: string
  /** Error message if status is error */
  errorMessage?: string
}

interface RawInstallation {
  id: string
  app_id: string
  app_name: string
  app_icon?: string
  app_version: string
  app_description: string
  app_category: string
  app_source: string
  server_id: string
  server_name: string
  server_host: string
  container_id?: string
  container_name: string
  status: string
  ports: Record<string, number>
  env: Record<string, string>
  volumes: Record<string, string>
  networks: string[]
  named_volumes: { name: string; destination: string; mode: string }[]
  bind_mounts: { source: string; destination: string; mode: string }[]
  installed_at: string
  started_at?: string
  error_message?: string
}

interface GetAllInstalledAppsResponse {
  success: boolean
  data?: {
    installations: RawInstallation[]
    total: number
  }
  error?: string
  message?: string
}

interface RefreshStatusResponse {
  success: boolean
  data?: {
    status: string
    networks?: string[]
    named_volumes?: { name: string; destination: string; mode: string }[]
    bind_mounts?: { source: string; destination: string; mode: string }[]
  }
  error?: string
}

export interface UseInstalledAppsReturn {
  /** List of installed apps with details */
  apps: InstalledAppInfo[]
  /** Loading state */
  isLoading: boolean
  /** Whether status is being refreshed from Docker */
  isRefreshingStatus: boolean
  /** Error message if any */
  error: string | null
  /** Refresh the list */
  refresh: () => Promise<void>
  /** Refresh live status from Docker for all apps */
  refreshLiveStatus: () => Promise<void>
}

function transformInstallation(raw: RawInstallation): InstalledAppInfo {
  return {
    id: raw.id,
    appId: raw.app_id,
    appName: raw.app_name,
    appIcon: raw.app_icon,
    appVersion: raw.app_version,
    appDescription: raw.app_description,
    appCategory: raw.app_category,
    appSource: raw.app_source,
    serverId: raw.server_id,
    serverName: raw.server_name,
    serverHost: raw.server_host,
    containerId: raw.container_id,
    containerName: raw.container_name,
    status: raw.status as InstallationStatus,
    ports: raw.ports || {},
    env: raw.env || {},
    volumes: raw.volumes || {},
    networks: raw.networks || [],
    namedVolumes: (raw.named_volumes || []).map(v => ({
      name: v.name,
      destination: v.destination,
      mode: v.mode
    })),
    bindMounts: (raw.bind_mounts || []).map(b => ({
      source: b.source,
      destination: b.destination,
      mode: b.mode
    })),
    installedAt: raw.installed_at,
    startedAt: raw.started_at,
    errorMessage: raw.error_message
  }
}

export function useInstalledApps(): UseInstalledAppsReturn {
  const { client, isConnected } = useMCP()
  const { settings } = useSettingsContext()

  const [apps, setApps] = useState<InstalledAppInfo[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRefreshingStatus, setIsRefreshingStatus] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasAutoRefreshed = useRef(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Get settings with defaults
  const autoRefreshStatus = settings?.applications?.autoRefreshStatus ?? true
  const statusRefreshInterval = settings?.applications?.statusRefreshInterval ?? 0

  // Refresh live status from Docker for all apps
  const refreshLiveStatus = useCallback(async () => {
    if (!isConnected || apps.length === 0) {
      return
    }

    setIsRefreshingStatus(true)

    try {
      // Refresh each app's status in parallel
      const refreshPromises = apps.map(async (app) => {
        try {
          const response = await client.callTool<RefreshStatusResponse>(
            'refresh_installation_status',
            { installation_id: app.id }
          )

          const toolResponse = response.data as RefreshStatusResponse | undefined

          if (response.success && toolResponse?.success && toolResponse?.data) {
            return {
              id: app.id,
              status: toolResponse.data.status as InstallationStatus,
              networks: toolResponse.data.networks,
              namedVolumes: toolResponse.data.named_volumes?.map(v => ({
                name: v.name,
                destination: v.destination,
                mode: v.mode
              })),
              bindMounts: toolResponse.data.bind_mounts?.map(b => ({
                source: b.source,
                destination: b.destination,
                mode: b.mode
              }))
            }
          }
          return null
        } catch {
          return null
        }
      })

      const results = await Promise.all(refreshPromises)

      // Update apps with refreshed status
      setApps(currentApps =>
        currentApps.map(app => {
          const update = results.find(r => r?.id === app.id)
          if (update) {
            return {
              ...app,
              status: update.status,
              networks: update.networks ?? app.networks,
              namedVolumes: update.namedVolumes ?? app.namedVolumes,
              bindMounts: update.bindMounts ?? app.bindMounts
            }
          }
          return app
        })
      )
    } finally {
      setIsRefreshingStatus(false)
    }
  }, [client, isConnected, apps])

  const refresh = useCallback(async () => {
    if (!isConnected) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await client.callTool<GetAllInstalledAppsResponse>(
        'get_app',
        {}
      )

      // MCP client returns { success, data, message }
      // where data is the backend tool's full response { success, data: { installations, total }, message }
      const toolResponse = response.data as GetAllInstalledAppsResponse | undefined

      if (response.success && toolResponse?.success && toolResponse?.data?.installations) {
        const transformed = toolResponse.data.installations.map(transformInstallation)
        setApps(transformed)
      } else if (!response.success) {
        // MCP call failed
        setError(response.error || 'Failed to connect to backend')
        setApps([])
      } else if (toolResponse && !toolResponse.success) {
        // Tool returned an error
        setError(toolResponse.error || toolResponse.message || 'Failed to fetch installed apps')
        setApps([])
      } else {
        // Unexpected response format - don't show error, just empty list
        setApps([])
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(message)
      setApps([])
    } finally {
      setIsLoading(false)
    }
  }, [client, isConnected])

  // Fetch on mount and when connection status changes
  useEffect(() => {
    if (isConnected) {
      refresh()
      hasAutoRefreshed.current = false // Reset when connection changes
    }
  }, [isConnected, refresh])

  // Auto-refresh live status after initial data loads (if enabled)
  useEffect(() => {
    if (
      apps.length > 0 &&
      !isLoading &&
      isConnected &&
      autoRefreshStatus &&
      !hasAutoRefreshed.current
    ) {
      hasAutoRefreshed.current = true
      refreshLiveStatus()
    }
  }, [apps.length, isLoading, isConnected, autoRefreshStatus, refreshLiveStatus])

  // Set up periodic refresh if interval > 0
  useEffect(() => {
    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Set up new interval if enabled and interval > 0
    if (autoRefreshStatus && statusRefreshInterval > 0 && isConnected && apps.length > 0) {
      intervalRef.current = setInterval(() => {
        refreshLiveStatus()
      }, statusRefreshInterval * 1000)
    }

    // Cleanup on unmount or when dependencies change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [autoRefreshStatus, statusRefreshInterval, isConnected, apps.length, refreshLiveStatus])

  return {
    apps,
    isLoading,
    isRefreshingStatus,
    error,
    refresh,
    refreshLiveStatus
  }
}
