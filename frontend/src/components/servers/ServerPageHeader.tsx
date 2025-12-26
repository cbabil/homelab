/**
 * Server Page Header Component
 *
 * Modern header section with title, description, and Add Server button.
 * Provides clean separation of header functionality from main page logic.
 */

import { Plus, Download, Upload } from 'lucide-react'
import { Button } from '@/components/ui/Button'

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
        <Button
          onClick={onImportServers}
          variant="outline"
          size="md"
          leftIcon={<Upload className="h-4 w-4" />}
        >
          Import
        </Button>
        <Button
          onClick={onExportServers}
          variant="outline"
          size="md"
          leftIcon={<Download className="h-4 w-4" />}
        >
          Export
        </Button>
        <Button
          onClick={onAddServer}
          variant="primary"
          size="md"
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Add Server
        </Button>
      </div>
    </div>
  )
}