/**
 * Server Types
 * 
 * TypeScript definitions for server-related data structures.
 * Matches backend Pydantic models for consistency.
 */

export type AuthType = 'password' | 'key'
export type ServerStatus = 'connected' | 'disconnected' | 'error' | 'preparing'

export interface SystemInfo {
  os: string
  kernel: string
  architecture: string
  uptime: string
  docker_version?: string
}

export interface ServerConnection {
  id: string
  name: string
  host: string
  port: number
  username: string
  auth_type: AuthType
  status: ServerStatus
  created_at: string
  updated_at?: string
  last_connected?: string
  system_info?: SystemInfo
}

export interface ServerConnectionInput {
  name: string
  host: string
  port: number
  username: string
  auth_type: AuthType
  credentials: {
    password?: string
    private_key?: string
    passphrase?: string
  }
}

export interface ServerPreparationResult {
  success: boolean
  server_id?: string
  message: string
  preparation_log?: string[]
  docker_version?: string
  system_info?: SystemInfo
  error?: string
}