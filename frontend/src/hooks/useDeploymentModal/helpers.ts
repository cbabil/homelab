/**
 * Deployment Modal Helpers
 *
 * Helper functions for deployment operations.
 */

import { DeploymentConfig, ServerDeploymentStatus } from '@/types/deployment'
import { InstallationStatusData } from '../useInstallationStatus'

/**
 * Build config payload for API calls, filtering out empty objects
 */
export function buildConfigPayload(config: DeploymentConfig) {
  return {
    ports:
      config.ports && Object.keys(config.ports).length > 0
        ? config.ports
        : undefined,
    volumes:
      config.volumes && Object.keys(config.volumes).length > 0
        ? config.volumes
        : undefined,
    env:
      config.env && Object.keys(config.env).length > 0 ? config.env : undefined,
  }
}

/**
 * Calculate progress percentage based on installation status
 * 3 tasks = 33% each (pulling, creating, running)
 */
export function calculateProgress(
  status: string,
  backendProgress: number
): number {
  if (status === 'pending') {
    return 0
  }
  if (status === 'pulling') {
    // Pulling: 0-33% (first task)
    return Math.round(backendProgress * 0.33)
  }
  if (status === 'creating') {
    // Creating: 33-66% (second task)
    return 33 + Math.round(backendProgress * 0.33)
  }
  if (status === 'running') {
    // Running: 100% complete
    return 100
  }
  if (status === 'error') {
    // Keep current progress on error (don't reset to 0)
    return Math.round(backendProgress * 0.33)
  }
  return 0
}

/**
 * Parse installation status from nested tool response
 */
export function parseStatusResponse(
  statusData: InstallationStatusData
): { status: ServerDeploymentStatus['status']; progress: number } {
  const status = statusData.status
  const backendProgress = (statusData as { progress?: number }).progress ?? 0
  const progress = calculateProgress(status, backendProgress)

  return {
    status: status as ServerDeploymentStatus['status'],
    progress,
  }
}
