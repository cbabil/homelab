/**
 * useDeploymentModal Hook
 *
 * Re-exports the deployment modal hook from the refactored module structure.
 * This file is kept for backward compatibility with existing imports.
 */

export {
  useDeploymentModal,
  type DeploymentConfig,
  type DeploymentStep,
  type PreflightCheck,
  type PreflightResult,
  type ValidationResult,
  type ServerDeploymentStatus,
  type DeploymentResult,
  type UseDeploymentModalReturn,
} from './useDeploymentModal/index'
