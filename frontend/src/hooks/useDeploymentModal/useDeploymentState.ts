/**
 * useDeploymentState Hook
 *
 * Core state management for the deployment modal.
 */

import { useState, useCallback } from 'react'
import { App } from '@/types/app'
import { MarketplaceApp } from '@/types/marketplace'
import {
  DeploymentConfig,
  DeploymentStep,
  DeploymentResult,
  PreflightResult,
  ValidationResult,
  ServerDeploymentStatus,
  initialDeploymentConfig,
} from '@/types/deployment'
import {
  marketplaceAppToApp,
  generateDeploymentConfig,
} from '@/services/marketplaceConverter'
import { useInstallationStatus } from '../useInstallationStatus'
import { useToast } from '@/components/ui/Toast'
import { deploymentLogger } from '@/services/systemLogger'

export interface UseDeploymentStateReturn {
  // Modal state
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  step: DeploymentStep
  setStep: (step: DeploymentStep) => void

  // Selection state
  selectedApp: App | null
  setSelectedApp: (app: App | null) => void
  selectedServerIds: string[]
  setSelectedServerIds: (ids: string[]) => void

  // Server status tracking
  targetServerStatuses: ServerDeploymentStatus[]
  setTargetServerStatuses: (statuses: ServerDeploymentStatus[]) => void
  updateServerStatus: (id: string, updates: Partial<ServerDeploymentStatus>) => void

  // Configuration
  config: DeploymentConfig
  setConfig: (config: DeploymentConfig) => void
  updateConfig: (updates: Partial<DeploymentConfig>) => void

  // Preflight state
  preflightResult: PreflightResult | null
  setPreflightResult: (result: PreflightResult | null) => void
  isRunningPreflight: boolean
  setIsRunningPreflight: (running: boolean) => void

  // Validation state
  validationResult: ValidationResult | null
  setValidationResult: (result: ValidationResult | null) => void
  isValidating: boolean
  setIsValidating: (validating: boolean) => void

  // Deployment state
  isDeploying: boolean
  setIsDeploying: (deploying: boolean) => void
  error: string | null
  setError: (error: string | null) => void
  deploymentResult: DeploymentResult | null
  setDeploymentResult: (result: DeploymentResult | null) => void

  // Installation status hook
  installationStatusHook: ReturnType<typeof useInstallationStatus>

  // Actions
  openModal: (app: App) => void
  openModalForMarketplace: (marketplaceApp: MarketplaceApp) => void
  closeModal: () => void
  reset: () => void
}

export function useDeploymentState(): UseDeploymentStateReturn {
  const { addToast } = useToast()

  // Modal state
  const [isOpen, setIsOpen] = useState(false)
  const [step, setStep] = useState<DeploymentStep>('select')

  // Selection state
  const [selectedApp, setSelectedApp] = useState<App | null>(null)
  const [selectedServerIds, setSelectedServerIds] = useState<string[]>([])

  // Multi-server deployment status tracking
  const [targetServerStatuses, setTargetServerStatuses] = useState<
    ServerDeploymentStatus[]
  >([])

  // Configuration
  const [config, setConfig] = useState<DeploymentConfig>(initialDeploymentConfig)

  // Preflight state
  const [preflightResult, setPreflightResult] = useState<PreflightResult | null>(
    null
  )
  const [isRunningPreflight, setIsRunningPreflight] = useState(false)

  // Validation state
  const [validationResult, setValidationResult] =
    useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Deployment state
  const [isDeploying, setIsDeploying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deploymentResult, setDeploymentResult] =
    useState<DeploymentResult | null>(null)

  // Installation status polling
  const installationStatusHook = useInstallationStatus({
    onComplete: () => {
      setStep('success')
      addToast({
        type: 'success',
        title: 'Deployment Complete',
        message: `${selectedApp?.name} is now running`,
        duration: 5000,
      })
      deploymentLogger.info('Deployment completed successfully', {
        appId: selectedApp?.id,
        appName: selectedApp?.name,
        installationId: deploymentResult?.installationId,
      })
    },
    onError: (errorMsg) => {
      setError(errorMsg)
      deploymentLogger.error('Installation failed during deployment', {
        appId: selectedApp?.id,
        appName: selectedApp?.name,
        installationId: deploymentResult?.installationId,
        error: errorMsg,
      })
    },
  })

  const updateServerStatus = useCallback(
    (serverId: string, updates: Partial<ServerDeploymentStatus>) => {
      setTargetServerStatuses((prev) =>
        prev.map((s) => (s.serverId === serverId ? { ...s, ...updates } : s))
      )
    },
    []
  )

  const updateConfig = useCallback((updates: Partial<DeploymentConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }))
  }, [])

  const reset = useCallback(() => {
    setStep('select')
    setSelectedServerIds([])
    setTargetServerStatuses([])
    setConfig(initialDeploymentConfig)
    setError(null)
    setDeploymentResult(null)
    setIsDeploying(false)
    setPreflightResult(null)
    setIsRunningPreflight(false)
    setValidationResult(null)
    setIsValidating(false)
    installationStatusHook.reset()
  }, [installationStatusHook])

  const openModal = useCallback(
    (app: App) => {
      reset()
      setSelectedApp(app)
      setIsOpen(true)
    },
    [reset]
  )

  const openModalForMarketplace = useCallback(
    (marketplaceApp: MarketplaceApp) => {
      reset()
      const app = marketplaceAppToApp(marketplaceApp)
      setSelectedApp(app)
      const newConfig = generateDeploymentConfig(marketplaceApp.docker)
      setConfig(newConfig)
      setIsOpen(true)
      deploymentLogger.info('Deployment modal opened', {
        appId: app.id,
        appName: app.name,
        image: marketplaceApp.docker?.image,
      })
    },
    [reset]
  )

  const closeModal = useCallback(() => {
    setIsOpen(false)
    setTimeout(() => {
      reset()
      setSelectedApp(null)
    }, 200)
  }, [reset])

  return {
    isOpen,
    setIsOpen,
    step,
    setStep,
    selectedApp,
    setSelectedApp,
    selectedServerIds,
    setSelectedServerIds,
    targetServerStatuses,
    setTargetServerStatuses,
    updateServerStatus,
    config,
    setConfig,
    updateConfig,
    preflightResult,
    setPreflightResult,
    isRunningPreflight,
    setIsRunningPreflight,
    validationResult,
    setValidationResult,
    isValidating,
    setIsValidating,
    isDeploying,
    setIsDeploying,
    error,
    setError,
    deploymentResult,
    setDeploymentResult,
    installationStatusHook,
    openModal,
    openModalForMarketplace,
    closeModal,
    reset,
  }
}
