/**
 * Marketplace Converter Service
 *
 * Converts MarketplaceApp to App type and generates deployment config
 * from Docker configuration.
 */

import { App, AppCategory, AppRequirements } from '@/types/app'
import { MarketplaceApp, DockerConfig } from '@/types/marketplace'
import { DeploymentConfig } from '@/hooks/useDeploymentModal'
import { Package, Shield, Activity, HardDrive, Wrench, Globe, Play, Database } from 'lucide-react'

// Default category icons mapping
const categoryIcons: Record<string, typeof Package> = {
  networking: Globe,
  automation: Play,
  media: Play,
  security: Shield,
  monitoring: Activity,
  storage: HardDrive,
  utility: Wrench,
  development: Package,
  database: Database
}

const categoryColors: Record<string, string> = {
  networking: 'blue',
  automation: 'orange',
  media: 'red',
  security: 'green',
  monitoring: 'purple',
  storage: 'yellow',
  utility: 'gray',
  development: 'cyan',
  database: 'emerald'
}

/**
 * Convert MarketplaceApp to App type for deployment
 */
export function marketplaceAppToApp(marketplaceApp: MarketplaceApp): App {
  const categoryId = marketplaceApp.category.toLowerCase()

  const category: AppCategory = {
    id: categoryId,
    name: marketplaceApp.category,
    description: `${marketplaceApp.category} applications`,
    icon: categoryIcons[categoryId] || Package,
    color: categoryColors[categoryId] || 'gray'
  }

  // Convert requirements
  const requirements: AppRequirements = {
    minRam: marketplaceApp.requirements.minRam
      ? `${marketplaceApp.requirements.minRam}MB`
      : undefined,
    minStorage: marketplaceApp.requirements.minStorage
      ? `${marketplaceApp.requirements.minStorage}MB`
      : undefined,
    requiredPorts: marketplaceApp.docker.ports.map(p => p.host),
    supportedArchitectures: marketplaceApp.requirements.architectures
  }

  return {
    id: marketplaceApp.id,
    name: marketplaceApp.name,
    description: marketplaceApp.description,
    longDescription: marketplaceApp.longDescription,
    version: marketplaceApp.version,
    category,
    tags: marketplaceApp.tags,
    icon: marketplaceApp.icon,
    author: marketplaceApp.author,
    repository: marketplaceApp.repository,
    documentation: marketplaceApp.documentation,
    license: marketplaceApp.license,
    requirements,
    status: 'available',
    installCount: marketplaceApp.installCount,
    rating: marketplaceApp.avgRating,
    featured: marketplaceApp.featured,
    createdAt: marketplaceApp.createdAt,
    updatedAt: marketplaceApp.updatedAt
  }
}

/**
 * Generate initial deployment config from MarketplaceApp's Docker config
 */
export function generateDeploymentConfig(docker: DockerConfig): DeploymentConfig {
  // Convert ports: containerPort -> hostPort
  const ports: Record<string, number> = {}
  for (const port of docker.ports) {
    ports[String(port.container)] = port.host
  }

  // Convert volumes: containerPath -> hostPath
  const volumes: Record<string, string> = {}
  for (const volume of docker.volumes) {
    volumes[volume.containerPath] = volume.hostPath
  }

  // Convert environment variables with defaults
  const env: Record<string, string> = {}
  for (const envVar of docker.environment) {
    if (envVar.default) {
      env[envVar.name] = envVar.default
    } else if (envVar.required) {
      env[envVar.name] = '' // Placeholder for required vars
    }
  }

  return { ports, volumes, env }
}

/**
 * Get required environment variables that need user input
 */
export function getRequiredEnvVars(docker: DockerConfig): Array<{
  name: string
  description?: string
  hasDefault: boolean
}> {
  return docker.environment
    .filter(e => e.required)
    .map(e => ({
      name: e.name,
      description: e.description,
      hasDefault: !!e.default
    }))
}

/**
 * Validate deployment config against MarketplaceApp requirements
 */
export function validateMarketplaceDeployment(
  docker: DockerConfig,
  config: DeploymentConfig
): { valid: boolean; errors: string[]; warnings: string[] } {
  const errors: string[] = []
  const warnings: string[] = []

  // Check required environment variables
  for (const envVar of docker.environment) {
    if (envVar.required && !config.env?.[envVar.name]) {
      errors.push(`Required environment variable '${envVar.name}' is not set`)
    }
  }

  // Check port conflicts (basic validation)
  const hostPorts = Object.values(config.ports || {})
  const uniquePorts = new Set(hostPorts)
  if (hostPorts.length !== uniquePorts.size) {
    errors.push('Duplicate host ports detected')
  }

  // Check for privileged mode warning
  if (docker.privileged) {
    warnings.push('This container requires privileged mode')
  }

  // Check for special capabilities
  if (docker.capabilities.length > 0) {
    warnings.push(`Container requires capabilities: ${docker.capabilities.join(', ')}`)
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  }
}
