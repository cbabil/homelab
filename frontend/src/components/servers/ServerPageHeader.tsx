/**
 * Server Page Header Component
 * 
 * Modern header section with title, description, and Add Server button.
 * Provides clean separation of header functionality from main page logic.
 */

import { Plus, Download, Upload } from 'lucide-react'

interface ServerPageHeaderProps {
  onAddServer: () => void
  onExportServers: () => void
  onImportServers: () => void
}

export function ServerPageHeader({ onAddServer, onExportServers, onImportServers }: ServerPageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Servers</h1>
        <p className="text-muted-foreground mt-1">
          Manage your homelab server connections and configurations.
        </p>
      </div>
      <div className="flex items-center space-x-3">
        <button 
          onClick={onImportServers}
          className="px-3 py-2 rounded-lg font-medium text-sm flex items-center space-x-2 border border-input bg-background hover:bg-accent transition-colors"
        >
          <Upload className="h-4 w-4" />
          <span>Import</span>
        </button>
        <button 
          onClick={onExportServers}
          className="px-3 py-2 rounded-lg font-medium text-sm flex items-center space-x-2 border border-input bg-background hover:bg-accent transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
        <button 
          onClick={onAddServer}
          className="btn-gradient px-4 py-2.5 rounded-lg font-medium text-sm flex items-center space-x-2 shadow-sm hover:shadow-md transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Add Server</span>
        </button>
      </div>
    </div>
  )
}