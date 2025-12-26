/**
 * Application Name Fields Component
 * 
 * Form fields for application name, description, and version.
 */

import { App } from '@/types/app'

interface ApplicationNameFieldsProps {
  formData: Partial<App>
  onChange: (field: string, value: string | string[]) => void
}

export function ApplicationNameFields({ 
  formData, 
  onChange 
}: ApplicationNameFieldsProps) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Application Name</label>
        <input
          type="text"
          value={formData.name || ''}
          onChange={(e) => onChange('name', e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          placeholder="Enter application name"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Description</label>
        <textarea
          value={formData.description || ''}
          onChange={(e) => onChange('description', e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          rows={2}
          placeholder="Brief description of the application"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">Version</label>
        <input
          type="text"
          value={formData.version || ''}
          onChange={(e) => onChange('version', e.target.value)}
          className="w-full px-3 py-1.5 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20"
          placeholder="1.0.0"
          required
        />
      </div>
    </div>
  )
}