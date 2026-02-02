/**
 * useDeploymentModal Hook
 *
 * State management for the deployment modal workflow.
 * Handles server selection, configuration, deployment execution,
 * preflight checks, config validation, and cleanup.
 */

import { useDeploymentState } from './useDeploymentState'
import { useDeploymentValidation } from './useDeploymentValidation'
import { useDeploymentActions } from './useDeploymentActions'
import { UseDeploymentModalReturn } from './types'

// Re-export types from shared types module
export type {
  DeploymentConfig,
  DeploymentStep,
  PreflightCheck,
  PreflightResult,
  ValidationResult,
  ServerDeploymentStatus,
  DeploymentResult,
} from '@/types/deployment'

// Re-export the hook return type
export type { UseDeploymentModalReturn } from './types'

export function useDeploymentModal(): UseDeploymentModalReturn {
  // Core state management
  const state = useDeploymentState()

  // Validation hooks (preflight and config)
  const validation = useDeploymentValidation({
    selectedApp: state.selectedApp,
    selectedServerIds: state.selectedServerIds,
    config: state.config,
    setPreflightResult: state.setPreflightResult,
    setIsRunningPreflight: state.setIsRunningPreflight,
    setValidationResult: state.setValidationResult,
    setIsValidating: state.setIsValidating,
    setError: state.setError,
  })

  // Deployment actions
  const actions = useDeploymentActions({
    selectedApp: state.selectedApp,
    selectedServerIds: state.selectedServerIds,
    config: state.config,
    deploymentResult: state.deploymentResult,
    setStep: state.setStep,
    setIsDeploying: state.setIsDeploying,
    setError: state.setError,
    setDeploymentResult: state.setDeploymentResult,
    setTargetServerStatuses: state.setTargetServerStatuses,
    updateServerStatus: state.updateServerStatus,
  })

  return {
    // Modal state
    isOpen: state.isOpen,
    openModal: state.openModal,
    openModalForMarketplace: state.openModalForMarketplace,
    closeModal: state.closeModal,

    // Current step
    step: state.step,
    setStep: state.setStep,

    // Selection state
    selectedApp: state.selectedApp,
    selectedServerIds: state.selectedServerIds,
    setSelectedServerIds: state.setSelectedServerIds,

    // Configuration
    config: state.config,
    setConfig: state.setConfig,
    updateConfig: state.updateConfig,

    // Preflight state
    preflightResult: state.preflightResult,
    isRunningPreflight: state.isRunningPreflight,
    runPreflight: validation.runPreflight,

    // Validation state
    validationResult: state.validationResult,
    isValidating: state.isValidating,
    validateConfig: validation.validateConfig,

    // Deployment state
    isDeploying: state.isDeploying,
    error: state.error,
    deploymentResult: state.deploymentResult,

    // Multi-server deployment status
    targetServerStatuses: state.targetServerStatuses,

    // Installation status polling (for single server fallback)
    installationStatus: state.installationStatusHook.statusData,
    isPollingStatus: state.installationStatusHook.isPolling,

    // Actions
    deploy: actions.deploy,
    cleanup: actions.cleanup,
    reset: state.reset,
    retryDeployment: actions.retryDeployment,
  }
}
