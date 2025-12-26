/**
 * Storage Types
 * 
 * Type definitions for server storage operations.
 */

import { ServerConnection } from '@/types/server'

export const STORAGE_KEY = 'homelab_servers'
export const DATA_VERSION = '1.0'

export interface StorageData {
  version: string
  servers: ServerConnection[]
  updated_at: string
}