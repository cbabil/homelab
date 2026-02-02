/**
 * Deployment Types
 *
 * Type definitions for deployment modal and related functionality.
 */

export interface DeploymentConfig {
  // General
  containerName?: string
  hostname?: string
  restartPolicy?: 'no' | 'always' | 'on-failure' | 'unless-stopped'
  workingDir?: string
  user?: string
  command?: string
  entrypoint?: string
  // Ports
  ports?: Record<string, number> // containerPort: hostPort
  // Environment
  env?: Record<string, string> // key: value
  // Volumes
  volumes?: Record<string, string> // containerPath: hostPath
  // Network
  networkMode?: 'bridge' | 'host' | 'none'
  networks?: string[]
  // Resources
  cpuLimit?: number // CPU cores (e.g., 0.5, 1, 2)
  memoryLimit?: string // e.g., "512m", "1g"
  // Labels
  labels?: Record<string, string>
  // Health Check
  healthCheck?: {
    command?: string
    interval?: string // e.g., "30s"
    timeout?: string // e.g., "10s"
    retries?: number
  }
  // Security
  privileged?: boolean
  capabilities?: {
    add?: string[]
    drop?: string[]
  }
  // Custom raw config (YAML)
  customConfig?: string
}

export type DeploymentStep = 'select' | 'deploying' | 'success' | 'error'

// Preflight check result
export interface PreflightCheck {
  name: string
  passed: boolean
  message: string
  details?: Record<string, unknown>
}

export interface PreflightResult {
  passed: boolean
  checks: PreflightCheck[]
  message?: string
}

// Config validation result
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

// Server deployment status for multi-server deployments
export interface ServerDeploymentStatus {
  serverId: string
  serverName: string
  progress: number
  status: 'pending' | 'pulling' | 'creating' | 'starting' | 'running' | 'error'
  error?: string
  installationId?: string
}

export interface DeploymentResult {
  success: boolean
  installationId?: string
  serverId?: string
  appId?: string
  message?: string
}

export const initialDeploymentConfig: DeploymentConfig = {
  ports: {},
  volumes: {},
  env: {},
}
