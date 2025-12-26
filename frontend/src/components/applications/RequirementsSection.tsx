/**
 * Requirements Section Component
 * 
 * Form section for application system requirements.
 */

import { AppRequirements } from '@/types/app'

interface RequirementsSectionProps {
  requirements: AppRequirements
  onChange: (field: string, value: string | string[] | number[]) => void
}

export function RequirementsSection({ requirements, onChange }: RequirementsSectionProps) {
  const handlePortsChange = (value: string) => {
    const ports = value.split(',')
      .map(port => parseInt(port.trim()))
      .filter(port => !isNaN(port))
    onChange('requiredPorts', ports)
  }

  const handleDependenciesChange = (value: string) => {
    const deps = value.split(',').map(dep => dep.trim()).filter(Boolean)
    onChange('dependencies', deps)
  }

  const handleArchitecturesChange = (value: string) => {
    const archs = value.split(',').map(arch => arch.trim()).filter(Boolean)
    onChange('supportedArchitectures', archs)
  }

  return (
    <div className="space-y-1.5 border-t pt-1.5">
      <h3 className="text-sm font-medium text-foreground mb-2">System Requirements</h3>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Min RAM</label>
          <input
            type="text"
            value={requirements.minRam || ''}
            onChange={(e) => onChange('minRam', e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="512MB, 1GB, 2GB"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Min Storage</label>
          <input
            type="text"
            value={requirements.minStorage || ''}
            onChange={(e) => onChange('minStorage', e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="100MB, 1GB, 10GB"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5 mt-2.5">
        <div>
          <label className="block text-sm font-medium mb-1">Required Ports</label>
          <input
            type="text"
            value={requirements.requiredPorts?.join(', ') || ''}
            onChange={(e) => handlePortsChange(e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="80, 443, 8080"
          />
          <p className="text-xs text-muted-foreground mt-1">Separate ports with commas</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Supported Architectures</label>
          <input
            type="text"
            value={requirements.supportedArchitectures?.join(', ') || ''}
            onChange={(e) => handleArchitecturesChange(e.target.value)}
            className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
            placeholder="amd64, arm64, armv7"
          />
          <p className="text-xs text-muted-foreground mt-1">Separate architectures with commas</p>
        </div>
      </div>

      <div className="mt-2.5">
        <label className="block text-sm font-medium mb-1">Dependencies</label>
        <input
          type="text"
          value={requirements.dependencies?.join(', ') || ''}
          onChange={(e) => handleDependenciesChange(e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          placeholder="docker, postgresql, redis"
        />
        <p className="text-xs text-muted-foreground mt-1">Separate dependencies with commas</p>
      </div>
    </div>
  )
}