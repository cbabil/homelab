/**
 * Backup Section Component
 *
 * Compact backup and restore functionality for all tomo data
 * including settings, servers, and applications.
 */

import { Download, Upload } from 'lucide-react'
import { Box, Stack, Typography } from '@mui/material'
import { useBackupActions } from '@/hooks/useBackupActions'
import { RestoreOptionsPanel } from '@/components/settings/RestoreOptionsPanel'
import { Button } from '@/components/ui/Button'

export function BackupSection() {
  const {
    isExporting,
    isImporting,
    showRestoreOptions,
    restoreOptions,
    setRestoreOptions,
    handleExport,
    handleImport,
    resetRestoreOptions
  } = useBackupActions()

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>
            Data Backup
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Backup or restore all settings, servers, and apps
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            onClick={() => handleExport()}
            disabled={isExporting}
            variant="outline"
            size="sm"
            leftIcon={<Download style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
          <Button
            onClick={handleImport}
            disabled={isImporting || isExporting}
            variant="outline"
            size="sm"
            leftIcon={<Upload style={{ width: 12, height: 12 }} />}
            sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
          >
            {isImporting ? 'Importing...' : 'Import'}
          </Button>
          {showRestoreOptions && (
            <Button
              onClick={resetRestoreOptions}
              variant="ghost"
              size="sm"
              sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
            >
              Cancel
            </Button>
          )}
        </Stack>
      </Stack>

      {showRestoreOptions && (
        <Box sx={{ mt: 1.5, pt: 1.5, borderTop: 1, borderColor: 'divider' }}>
          <RestoreOptionsPanel
            options={restoreOptions}
            onChange={setRestoreOptions}
          />
        </Box>
      )}
    </Box>
  )
}
