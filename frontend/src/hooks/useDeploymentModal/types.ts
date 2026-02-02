/**
 * useDeploymentModal Types
 *
 * Types specific to the deployment modal hook interface.
 */

import { App } from '@/types/app'
import { MarketplaceApp } from '@/types/marketplace'
import { ServerConnection } from '@/types/server'
import {
  DeploymentConfig,
  DeploymentStep,
  DeploymentResult,
  PreflightResult,
  ValidationResult,
  ServerDeploymentStatus,
} from '@/types/deployment'
import { InstallationStatusData } from '../useInstallationStatus'

export interface UseDeploymentModalReturn {
  // Modal state
  isOpen: boolean
  openModal: (app: App) => void
  openModalForMarketplace: (marketplaceApp: MarketplaceApp) => void
  closeModal: () => void

  // Current step
  step: DeploymentStep
  setStep: (step: DeploymentStep) => void

  // Selection state
  selectedApp: App | null
  selectedServerIds: string[]
  setSelectedServerIds: (ids: string[]) => void

  // Configuration
  config: DeploymentConfig
  setConfig: (config: DeploymentConfig) => void
  updateConfig: (updates: Partial<DeploymentConfig>) => void

  // Preflight state
  preflightResult: PreflightResult | null
  isRunningPreflight: boolean
  runPreflight: (servers: ServerConnection[]) => Promise<boolean>

  // Validation state
  validationResult: ValidationResult | null
  isValidating: boolean
  validateConfig: () => Promise<boolean>

  // Deployment state
  isDeploying: boolean
  error: string | null
  deploymentResult: DeploymentResult | null

  // Multi-server deployment status
  targetServerStatuses: ServerDeploymentStatus[]

  // Installation status polling (for single server fallback)
  installationStatus: InstallationStatusData | null
  isPollingStatus: boolean

  // Actions
  deploy: (servers: ServerConnection[]) => Promise<boolean>
  cleanup: () => Promise<boolean>
  reset: () => void
  retryDeployment: (servers: ServerConnection[]) => Promise<boolean>
}
