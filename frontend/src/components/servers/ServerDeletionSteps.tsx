/**
 * Server Deletion Step Components
 *
 * Step content components for the ServerDeletionDialog.
 */

import { DialogTitle, DialogContent, DialogActions, Button, Typography, Box, CircularProgress, Stack } from '@mui/material'
import { Bot, Container, AlertTriangle } from 'lucide-react'
import type { TFunction } from 'i18next'

interface ConfirmStepProps {
  t: TFunction
  serverName: string
  hasAgent: boolean
  hasDocker: boolean
  onClose: () => void
  onConfirm: () => void
}

export function ConfirmStep({ t, serverName, hasAgent, hasDocker, onClose, onConfirm }: ConfirmStepProps) {
  return (
    <>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AlertTriangle size={20} color="#f59e0b" />
        {t('servers.deletion.confirmTitle')}
      </DialogTitle>
      <DialogContent>
        <Typography>{t('servers.deletion.confirmMessage', { name: serverName })}</Typography>
        {(hasAgent || hasDocker) && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>{t('servers.deletion.willBeRemoved')}</Typography>
            <Stack spacing={0.5} sx={{ mt: 1, ml: 2 }}>
              {hasAgent && <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Bot size={14} /> {t('agent.title')}</Typography>}
              {hasDocker && <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Container size={14} /> Docker</Typography>}
            </Stack>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button size="small" onClick={onClose}>{t('common.cancel')}</Button>
        <Button size="small" onClick={onConfirm} color="error" variant="contained">{t('common.continue')}</Button>
      </DialogActions>
    </>
  )
}

export function DeletingStep({ t }: { t: TFunction }) {
  return (
    <>
      <DialogTitle>{t('servers.deletion.deletingTitle')}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={24} />
          <Typography>{t('servers.deletion.deletingMessage')}</Typography>
        </Box>
      </DialogContent>
    </>
  )
}
