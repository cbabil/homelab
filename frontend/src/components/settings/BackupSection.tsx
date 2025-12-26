/**
 * Backup Section Component
 * 
 * Compact backup and restore functionality for all homelab data
 * including settings, servers, and applications.
 */

import { useState } from 'react'
import { Download, Upload, Settings, Server, Package, AlertCircle } from 'lucide-react'
import { homelabBackupService, RestoreOptions, BackupResult, RestoreResult } from '@/services/homelabBackupService'
import { useSettings } from '@/hooks/useSettings'
import { useToast } from '@/components/ui/Toast'

export function BackupSection() {
  const { settings, isLoading } = useSettings()
  const { addToast } = useToast()
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [showRestoreOptions, setShowRestoreOptions] = useState(false)
  const [restoreOptions, setRestoreOptions] = useState<RestoreOptions>({
    includeSettings: true,
    includeServers: true,
    includeApplications: true,
    overwriteExisting: false
  })

  const handleExport = async () => {
    if (isLoading || !settings) {
      addToast({
        type: 'error',
        title: 'Export Failed',
        message: 'Settings not ready for export. Please wait for settings to load.',
        duration: 4000
      })
      return
    }
    
    setIsExporting(true)
    
    try {
      const result: BackupResult = await homelabBackupService.createBackup()
      
      if (result.success) {
        addToast({
          type: 'success',
          title: 'Backup Exported',
          message: `Successfully created backup: ${result.filename}`,
          duration: 3000
        })
      } else {
        addToast({
          type: 'error',
          title: 'Export Failed',
          message: result.message,
          duration: 4000
        })
      }
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Export Failed',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        duration: 4000
      })
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async () => {
    if (!showRestoreOptions) {
      setShowRestoreOptions(true)
      return
    }
    
    setIsImporting(true)
    
    try {
      const result: RestoreResult = await homelabBackupService.restoreFromFile(restoreOptions)
      
      if (result.success) {
        const summary = [
          result.restored.settings ? 'Settings' : null,
          result.restored.servers > 0 ? `${result.restored.servers} servers` : null,
          result.restored.applications > 0 ? `${result.restored.applications} apps` : null
        ].filter(Boolean).join(', ')
        
        addToast({
          type: 'success',
          title: 'Backup Restored',
          message: `Successfully restored: ${summary}`,
          duration: 4000
        })
      } else {
        addToast({
          type: 'error',
          title: 'Restore Failed',
          message: result.message,
          duration: 4000
        })
      }
      
      setShowRestoreOptions(false)
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Import Failed',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        duration: 4000
      })
    } finally {
      setIsImporting(false)
    }
  }

  const resetRestoreOptions = () => {
    setShowRestoreOptions(false)
    setRestoreOptions({
      includeSettings: true,
      includeServers: true,
      includeApplications: true,
      overwriteExisting: false
    })
  }

  return (
    <div className="bg-card rounded-lg border p-3">
      <div className="flex items-center gap-2 mb-3">
        <Package className="h-4 w-4 text-primary" />
        <h4 className="text-sm font-semibold text-primary">Data Backup</h4>
      </div>
      
      {/* Compact Action Buttons */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-muted-foreground">
          Backup or restore all settings, servers, and apps
        </p>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={isExporting || isLoading || !settings}
            className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
          >
            <Download className="h-3 w-3" />
            {isExporting ? 'Exporting...' : isLoading ? 'Loading...' : 'Export'}
          </button>
          <button
            onClick={handleImport}
            disabled={isImporting}
            className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
          >
            <Upload className="h-3 w-3" />
            {isImporting ? 'Importing...' : showRestoreOptions ? 'Select File' : 'Import'}
          </button>
          {showRestoreOptions && (
            <button
              onClick={resetRestoreOptions}
              className="px-2 py-1.5 border border-input bg-background text-xs rounded hover:bg-accent transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Compact Restore Options */}
      {showRestoreOptions && (
        <div className="p-3 bg-accent/30 rounded border border-dashed">
          <h6 className="text-xs font-medium mb-2 text-muted-foreground">Import Options</h6>
          
          <div className="grid grid-cols-2 gap-2 mb-2">
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={restoreOptions.includeSettings}
                onChange={(e) => setRestoreOptions(prev => ({
                  ...prev,
                  includeSettings: e.target.checked
                }))}
                className="rounded border-input"
              />
              <Settings className="h-3 w-3" />
              Settings
            </label>
            
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={restoreOptions.includeServers}
                onChange={(e) => setRestoreOptions(prev => ({
                  ...prev,
                  includeServers: e.target.checked
                }))}
                className="rounded border-input"
              />
              <Server className="h-3 w-3" />
              Servers
            </label>
            
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={restoreOptions.includeApplications}
                onChange={(e) => setRestoreOptions(prev => ({
                  ...prev,
                  includeApplications: e.target.checked
                }))}
                className="rounded border-input"
              />
              <Package className="h-3 w-3" />
              Apps
            </label>
            
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={restoreOptions.overwriteExisting}
                onChange={(e) => setRestoreOptions(prev => ({
                  ...prev,
                  overwriteExisting: e.target.checked
                }))}
                className="rounded border-input"
              />
              <AlertCircle className="h-3 w-3 text-orange-500" />
              Overwrite
            </label>
          </div>
          
          <p className="text-xs text-muted-foreground">
            Select what to restore and whether to overwrite existing data
          </p>
        </div>
      )}
    </div>
  )
}