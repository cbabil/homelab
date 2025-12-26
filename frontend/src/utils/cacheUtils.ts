/**
 * Cache Utilities
 *
 * Helper function for clearing client-side caches and local storage entries
 * used by the Homelab frontend.
 */

import { clearStoredAuth } from '@/hooks/authStorageHelpers'
import { systemLogger } from '@/services/systemLogger'
import { SETTINGS_STORAGE_KEYS } from '@/types/settings'
import { STORAGE_KEY as SERVERS_STORAGE_KEY } from '@/services/storage/storageTypes'

const LOG_STORAGE_KEY = 'homelab-system-logs'
const SESSION_MANAGER_STORAGE_KEY = 'sessionManager_sessions'

export function clearHomelabCaches() {
  try {
    systemLogger.clearLogs()
  } catch (error) {
    console.warn('Failed to clear system logs cache', error)
  }

  try {
    localStorage.removeItem(LOG_STORAGE_KEY)
  } catch (error) {
    console.warn('Failed to remove log storage key', error)
  }

  try {
    Object.values(SETTINGS_STORAGE_KEYS).forEach((key) => {
      localStorage.removeItem(key)
    })
  } catch (error) {
    console.warn('Failed to clear settings cache', error)
  }

  try {
    localStorage.removeItem(SERVERS_STORAGE_KEY)
  } catch (error) {
    console.warn('Failed to clear server cache', error)
  }

  try {
    localStorage.removeItem(SESSION_MANAGER_STORAGE_KEY)
  } catch (error) {
    console.warn('Failed to clear session manager cache', error)
  }

  try {
    clearStoredAuth()
  } catch (error) {
    console.warn('Failed to clear auth storage', error)
  }
}
