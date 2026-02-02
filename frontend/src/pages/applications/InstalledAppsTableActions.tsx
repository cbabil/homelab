/**
 * Installed Apps Table Action Buttons
 *
 * Action buttons for start, stop, restart, and uninstall operations.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Play, Square, RotateCcw, Trash2 } from 'lucide-react'
import { IconButton, Stack } from '@mui/material'
import { InstalledAppInfo } from '@/hooks/useInstalledApps'

interface ActionButtonsProps {
  app: InstalledAppInfo
  onStart?: (app: InstalledAppInfo) => Promise<void>
  onStop?: (app: InstalledAppInfo) => Promise<void>
  onRestart?: (app: InstalledAppInfo) => Promise<void>
  onUninstall?: (app: InstalledAppInfo) => Promise<void>
  onUninstallStateChange?: (appId: string, isUninstalling: boolean) => void
}

export function ActionButtons({
  app, onStart, onStop, onRestart, onUninstall, onUninstallStateChange
}: ActionButtonsProps) {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState<string | null>(null)

  const canStart = app.status === 'stopped' || app.status === 'error'
  const canStop = app.status === 'running'

  const handleAction = async (action: string, handler?: (app: InstalledAppInfo) => Promise<void>) => {
    if (!handler) return
    setIsLoading(action)
    if (action === 'uninstall' && onUninstallStateChange) {
      onUninstallStateChange(app.id, true)
    }
    try {
      await handler(app)
    } finally {
      setIsLoading(null)
      if (action === 'uninstall' && onUninstallStateChange) {
        onUninstallStateChange(app.id, false)
      }
    }
  }

  const buttonSx = {
    width: 24,
    height: 24,
    color: 'text.secondary',
    '&:hover': { color: 'text.primary', bgcolor: 'transparent' }
  }

  return (
    <Stack direction="row" spacing={-0.5} sx={{ justifyContent: 'center', alignItems: 'center' }}>
      <IconButton
        size="small"
        disabled={!canStart || isLoading !== null || !onStart}
        onClick={(e) => { e.stopPropagation(); handleAction('start', onStart) }}
        title={t('applications.actions.start')}
        sx={buttonSx}
      >
        <Play className={`h-3.5 w-3.5 ${isLoading === 'start' ? 'animate-pulse' : ''}`} />
      </IconButton>
      <IconButton
        size="small"
        disabled={!canStop || isLoading !== null || !onStop}
        onClick={(e) => { e.stopPropagation(); handleAction('stop', onStop) }}
        title={t('applications.actions.stop')}
        sx={buttonSx}
      >
        <Square className={`h-3.5 w-3.5 ${isLoading === 'stop' ? 'animate-pulse' : ''}`} />
      </IconButton>
      <IconButton
        size="small"
        disabled={!canStop || isLoading !== null || !onRestart}
        onClick={(e) => { e.stopPropagation(); handleAction('restart', onRestart) }}
        title={t('applications.actions.restart')}
        sx={buttonSx}
      >
        <RotateCcw className={`h-3.5 w-3.5 ${isLoading === 'restart' ? 'animate-spin' : ''}`} />
      </IconButton>
      <IconButton
        size="small"
        disabled={isLoading !== null || !onUninstall}
        onClick={(e) => { e.stopPropagation(); handleAction('uninstall', onUninstall) }}
        title={t('applications.actions.uninstall')}
        sx={{ ...buttonSx, '&:hover': { color: 'error.main', bgcolor: 'transparent' } }}
      >
        <Trash2 className={`h-3.5 w-3.5 ${isLoading === 'uninstall' ? 'animate-pulse text-destructive' : ''}`} />
      </IconButton>
    </Stack>
  )
}
