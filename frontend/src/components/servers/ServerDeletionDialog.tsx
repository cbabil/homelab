/**
 * Server Deletion Dialog Component
 *
 * Multi-step confirmation dialog for server deletion.
 * Prompts for agent uninstall, Docker removal, then deletes the server.
 */

import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Dialog } from '@mui/material'
import { ConfirmStep, DeletingStep } from './ServerDeletionSteps'
import { ConfirmationDialog } from '@/components/ui/ConfirmationDialog'
import type { ServerConnection, AgentInfo } from '@/types/server'

type DeletionStep = 'confirm' | 'agent' | 'docker' | 'deleting' | 'done'

interface ServerDeletionDialogProps {
  open: boolean
  server: ServerConnection | null
  agentInfo: AgentInfo | null
  onClose: () => void
  uninstallAgent: (serverId: string) => Promise<boolean>
  removeDocker: (serverId: string) => Promise<boolean>
  deleteServer: (serverId: string) => Promise<void>
}

export function ServerDeletionDialog({
  open, server, agentInfo, onClose, uninstallAgent, removeDocker, deleteServer
}: ServerDeletionDialogProps) {
  const { t } = useTranslation()
  const [step, setStep] = useState<DeletionStep>('confirm')

  const hasAgent = agentInfo !== null && !!(agentInfo.version || agentInfo.is_connected)
  const hasDocker = !!server?.system_info?.docker_version && server.system_info.docker_version.toLowerCase() !== 'not installed'

  const performDelete = useCallback(async () => {
    if (!server) return
    setStep('deleting')
    await deleteServer(server.id)
    setStep('done')
    onClose()
  }, [server, deleteServer, onClose])

  const handleAgentUninstall = useCallback(async () => {
    if (!server) return
    await uninstallAgent(server.id)
    if (hasDocker) setStep('docker')
    else performDelete()
  }, [server, hasDocker, uninstallAgent, performDelete])

  const handleAgentSkip = useCallback(() => {
    if (hasDocker) setStep('docker')
    else performDelete()
  }, [hasDocker, performDelete])

  const handleDockerRemove = useCallback(async () => {
    if (!server) return
    await removeDocker(server.id)
    performDelete()
  }, [server, removeDocker, performDelete])

  const handleDockerSkip = useCallback(() => {
    performDelete()
  }, [performDelete])

  const handleConfirm = useCallback(() => {
    if (hasAgent) setStep('agent')
    else if (hasDocker) setStep('docker')
    else performDelete()
  }, [hasAgent, hasDocker, performDelete])

  useEffect(() => {
    if (open) setStep('confirm')
  }, [open])

  if (!server) return null

  if (step === 'agent') {
    return (
      <ConfirmationDialog
        open={true}
        title={t('agent.uninstallConfirmTitle')}
        message={t('agent.uninstallConfirmMessage', { name: server.name })}
        hint={t('agent.uninstallConfirmHint')}
        confirmLabel={t('agent.actions.uninstallAgent')}
        confirmingLabel={t('servers.uninstalling')}
        cancelLabel={t('common.cancel')}
        skipLabel={t('common.skip')}
        onClose={onClose}
        onSkip={handleAgentSkip}
        onConfirm={handleAgentUninstall}
      />
    )
  }

  if (step === 'docker') {
    return (
      <ConfirmationDialog
        open={true}
        title={t('servers.deletion.dockerTitle')}
        message={t('servers.deletion.dockerMessage')}
        hint={t('servers.deletion.dockerHint')}
        confirmLabel={t('servers.deletion.removeDocker')}
        confirmingLabel={t('servers.removingDocker')}
        cancelLabel={t('common.cancel')}
        skipLabel={t('common.skip')}
        onClose={onClose}
        onSkip={handleDockerSkip}
        onConfirm={handleDockerRemove}
      />
    )
  }

  return (
    <Dialog open={open} onClose={step === 'deleting' ? undefined : onClose} maxWidth="sm" fullWidth>
      {step === 'confirm' && (
        <ConfirmStep t={t} serverName={server.name} hasAgent={hasAgent} hasDocker={hasDocker} onClose={onClose} onConfirm={handleConfirm} />
      )}
      {step === 'deleting' && <DeletingStep t={t} />}
    </Dialog>
  )
}
