/**
 * Backup Actions Hook
 *
 * Handles backup export and restore logic with toast notifications.
 */

import { useState } from 'react'
import { tomoBackupService, RestoreOptions, BackupResult, RestoreResult } from '@/services/tomoBackupService'
import { useToast } from '@/components/ui/Toast'
import { useMCP } from '@/providers/MCPProvider'
import { ServerConnection } from '@/types/server'

const DEFAULT_RESTORE_OPTIONS: RestoreOptions = {
  includeSettings: true,
  includeServers: true,
  includeApplications: true,
  overwriteExisting: false
}

interface UseBackupActionsProps {
  servers?: ServerConnection[]
}

export function useBackupActions({ servers = [] }: UseBackupActionsProps = {}) {
  const { addToast } = useToast()
  const { client, isConnected } = useMCP()
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [showRestoreOptions, setShowRestoreOptions] = useState(false)
  const [restoreOptions, setRestoreOptions] = useState<RestoreOptions>(DEFAULT_RESTORE_OPTIONS)

  const handleExport = async () => {
    setIsExporting(true)

    try {
      const result: BackupResult = await tomoBackupService.createBackup(servers)

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

    if (!isConnected) {
      addToast({
        type: 'error',
        title: 'Import Failed',
        message: 'Not connected to backend',
        duration: 4000
      })
      return
    }

    setIsImporting(true)

    try {
      const result: RestoreResult = await tomoBackupService.restoreFromFile(client, servers, restoreOptions)

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
    setRestoreOptions(DEFAULT_RESTORE_OPTIONS)
  }

  return {
    isExporting,
    isImporting,
    showRestoreOptions,
    restoreOptions,
    setRestoreOptions,
    handleExport,
    handleImport,
    resetRestoreOptions
  }
}
