/**
 * App Details Panel Utilities
 *
 * Utility functions and constants for the app details panel.
 */

import { InstallationStatus, InstalledAppInfo } from '@/hooks/useInstalledApps'

// Row height estimate: text-xs (~16px) + py-0.5 (4px) = ~20px
export const LOG_ROW_HEIGHT = 20
export const MIN_LOGS_PER_PAGE = 5

export type TabId = 'overview' | 'settings' | 'logs'

// Status label translation keys
export const STATUS_TRANSLATION_KEYS: Record<InstallationStatus, string> = {
  running: 'applications.status.running',
  stopped: 'applications.status.stopped',
  error: 'applications.status.error',
  pending: 'applications.status.pending',
  pulling: 'applications.status.pulling',
  creating: 'applications.status.creating',
  starting: 'applications.status.starting'
}

export function getStatusChipColor(
  status: InstallationStatus
): 'success' | 'default' | 'error' | 'warning' {
  switch (status) {
    case 'running':
      return 'success'
    case 'stopped':
      return 'default'
    case 'error':
      return 'error'
    default:
      return 'warning'
  }
}

export function getAccessUrl(app: InstalledAppInfo): string | null {
  const ports = Object.entries(app.ports)
  if (ports.length === 0 || !app.serverHost) return null
  const [, hostPort] = ports[0]
  return `http://${app.serverHost}:${hostPort}`
}

export const TABS: { id: TabId; labelKey: string }[] = [
  { id: 'overview', labelKey: 'applications.tabs.overview' },
  { id: 'settings', labelKey: 'applications.tabs.settings' },
  { id: 'logs', labelKey: 'applications.tabs.logs' }
]
