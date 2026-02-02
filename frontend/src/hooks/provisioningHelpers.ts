/**
 * Provisioning Helper Functions
 *
 * Helper utilities for the useServerProvisioning hook.
 */

import { ProvisioningStep, ProvisioningState } from '@/types/server'

/** MCP response types for provisioning tools */
export interface TestConnectionResponse {
  success: boolean
  docker_installed?: boolean
  agent_installed?: boolean
  system_info?: Record<string, unknown>
  message?: string
  error?: string
}

export interface InstallDockerResponse {
  success: boolean
  message?: string
  data?: { docker_version?: string }
  error?: string
}

export interface InstallAgentResponse {
  success: boolean
  agent_id?: string
  message?: string
  error?: string
}

export const INITIAL_STEPS: ProvisioningStep[] = [
  { id: 'connection', status: 'pending' },
  { id: 'docker', status: 'pending' },
  { id: 'agent', status: 'pending' },
]

export const initialState: ProvisioningState = {
  isProvisioning: false,
  steps: INITIAL_STEPS,
  currentStep: 'connection',
  canRetry: false,
  dockerInstalled: false,
}

/** Update a specific step in the steps array */
export function updateStep(
  steps: ProvisioningStep[],
  stepId: ProvisioningStep['id'],
  updates: Partial<ProvisioningStep>
): ProvisioningStep[] {
  return steps.map((s) => (s.id === stepId ? { ...s, ...updates } : s))
}

/** Extract error message from response or exception */
export function extractError(
  response: { error?: string; message?: string } | undefined,
  fallback: string
): string {
  return response?.error || response?.message || fallback
}
