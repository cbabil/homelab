/**
 * Server Types
 * 
 * TypeScript definitions for server-related data structures.
 * Matches backend Pydantic models for consistency.
 */

export type AuthType = 'password' | 'key'
export type ServerStatus = 'connected' | 'disconnected' | 'error' | 'preparing'

export interface SystemInfo {
  os?: string
  kernel?: string
  architecture?: string
  uptime?: string
  docker_version?: string
  agent_status?: string
  agent_version?: string
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
  docker_installed: boolean
  system_info_updated_at?: string
  error_message?: string
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

/**
 * Agent Types
 *
 * TypeScript definitions for agent-related data structures.
 */

export type AgentStatus = 'pending' | 'connected' | 'disconnected' | 'updating'

export interface AgentInfo {
  id: string
  server_id: string
  status: AgentStatus
  version?: string
  last_seen?: string
  registered_at?: string
  is_connected: boolean
}

export interface AgentInstallResult {
  agent_id: string
  server_id: string
  deploy_command: string
}

export type AgentHealthStatus = 'healthy' | 'degraded' | 'offline'

export interface AgentHealthInfo {
  agent_id: string
  server_id: string
  status: AgentStatus
  health: AgentHealthStatus
  is_connected: boolean
  is_stale: boolean
  version?: string
  last_seen?: string
  registered_at?: string
}

export interface AgentVersionInfo {
  current_version: string
  latest_version: string
  update_available: boolean
  release_notes?: string
  update_url?: string
}

export interface AgentPingResult {
  agent_id: string
  responsive: boolean
  latency_ms?: number
}

/**
 * Command Execution Types
 */

export type ExecutionMethod = 'agent' | 'ssh' | 'none'

export interface CommandResult {
  success: boolean
  output: string
  method: ExecutionMethod
  exit_code?: number
  error?: string
  execution_time_ms?: number
}

export interface ExecutionMethodsInfo {
  server_id: string
  methods: ExecutionMethod[]
  agent_available: boolean
  preferred_method?: ExecutionMethod
}

/**
 * Provisioning Types
 *
 * TypeScript definitions for server provisioning flow.
 * Used by useServerProvisioning hook and ProvisioningProgress component.
 */

export type ProvisioningStepStatus = 'pending' | 'active' | 'success' | 'skipped' | 'error'

export interface ProvisioningStep {
  id: 'connection' | 'docker' | 'agent'
  status: ProvisioningStepStatus
  message?: string
  duration?: number
  error?: string
}

export interface ProvisioningState {
  isProvisioning: boolean
  steps: ProvisioningStep[]
  currentStep: 'connection' | 'docker' | 'agent' | 'complete'
  requiresDecision?: 'docker' | 'agent'
  canRetry: boolean
  serverId?: string
  dockerInstalled: boolean
}