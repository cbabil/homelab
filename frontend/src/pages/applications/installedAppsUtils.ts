/**
 * Utility functions and constants for Installed Apps Table
 */

import { InstallationStatus } from '@/hooks/useInstalledApps'

export type DisplayStatus = InstallationStatus | 'uninstalling'

export function getStatusChipColor(status: DisplayStatus): 'success' | 'default' | 'error' | 'warning' {
  switch (status) {
    case 'running':
      return 'success'
    case 'stopped':
      return 'default'
    case 'error':
    case 'uninstalling':
      return 'error'
    case 'pending':
    case 'pulling':
    case 'creating':
    case 'starting':
      return 'warning'
    default:
      return 'default'
  }
}

// Status label translation keys
export const STATUS_TRANSLATION_KEYS: Record<DisplayStatus, string> = {
  running: 'applications.status.running',
  stopped: 'applications.status.stopped',
  error: 'applications.status.error',
  uninstalling: 'applications.status.uninstalling',
  pending: 'applications.status.pending',
  pulling: 'applications.status.pulling',
  creating: 'applications.status.creating',
  starting: 'applications.status.starting'
}
