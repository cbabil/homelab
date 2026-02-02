/** Server Form Dialog - Modal for adding/editing server connections with provisioning */

import { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react'
import { X } from 'lucide-react'
import { Dialog, DialogTitle, DialogContent, DialogActions, IconButton, Typography } from '@mui/material'
import { ServerConnection, ServerConnectionInput, SystemInfo } from '@/types/server'
import { ProvisioningProgress } from './ProvisioningProgress'
import { ServerFormContent } from './serverFormDialogHelpers'
import { parseHostPort, canSubmitForm } from './serverFormUtils'
import { useServerForm } from '@/hooks/useServerForm'
import { useServerProvisioning } from '@/hooks/useServerProvisioning'
import { Button } from '@/components/ui/Button'
import { useTranslation } from 'react-i18next'

type ConnectionStatus = 'idle' | 'saving' | 'testing' | 'success' | 'error'

type StatusCallback = (status: 'saving' | 'testing' | 'success' | 'error', message?: string) => void

interface ServerFormDialogProps {
  isOpen: boolean
  onClose: () => void
  onSave: (s: ServerConnectionInput, info?: SystemInfo, cb?: StatusCallback, id?: string) => Promise<string | null>
  onDeleteServer?: (serverId: string) => Promise<void>
  onRefreshServers?: () => void
  onConnectServer?: (serverId: string) => Promise<unknown>
  server?: ServerConnection
  title: string
}

export function ServerFormDialog({ isOpen, onClose, onSave, onDeleteServer, onRefreshServers, onConnectServer, server, title }: ServerFormDialogProps) {
  const { t } = useTranslation()
  const { formData, handleInputChange, handleAuthTypeChange, handleCredentialChange, resetForm } = useServerForm(server)
  const provisioning = useServerProvisioning()
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle')
  const [submitError, setSubmitError] = useState<string | null>(null)
  const isEditMode = !!server

  // Track server ID created during this session for cleanup on cancel
  const createdServerIdRef = useRef<string | null>(null)

  const handleStatusChange = (status: 'saving' | 'testing' | 'success' | 'error', message?: string) => {
    setConnectionStatus(status)
    if (status === 'error' && message) setSubmitError(message)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitError(null)
    setConnectionStatus('idle')
    try {
      if (isEditMode) {
        await onSave(formData, undefined, handleStatusChange)
        onClose()
      } else {
        const preGeneratedId = crypto.randomUUID()
        // onSave returns actual server_id (may differ if server already existed in backend)
        const actualServerId = await onSave(formData, undefined, undefined, preGeneratedId)
        if (actualServerId) {
          // Track the created server for potential rollback
          createdServerIdRef.current = actualServerId
          provisioning.startProvisioning(actualServerId)
        }
      }
    } catch (error) {
      setConnectionStatus('error')
      setSubmitError(error instanceof Error ? error.message : t('servers.form.saveFailed'))
    }
  }

  // Reset all local state to clean slate
  const resetAllState = () => {
    createdServerIdRef.current = null
    provisioning.reset()
    resetForm()
    setConnectionStatus('idle')
    setSubmitError(null)
  }

  // Handle successful provisioning completion
  useEffect(() => {
    if (provisioning.state.currentStep === 'complete' && provisioning.state.serverId) {
      const finalize = async () => {
        await onConnectServer?.(provisioning.state.serverId!)
        onRefreshServers?.()
        resetAllState()
        onClose()
      }
      finalize()
    }
  }, [provisioning.state.currentStep, provisioning.state.serverId])

  // Rollback: delete server and reset all state
  const handleCancel = async () => {
    const serverIdToDelete = createdServerIdRef.current || provisioning.state.serverId

    if (serverIdToDelete) {
      // Cancel provisioning (resets provisioning state)
      await provisioning.cancel()
      // Delete the server from backend
      try {
        await onDeleteServer?.(serverIdToDelete)
      } catch {
        // Server may already be deleted by provisioning.cancel(), ignore
      }
      onRefreshServers?.()
    }

    resetAllState()
    onClose()
  }

  const handleHostChange = (e: ChangeEvent<HTMLInputElement>) => {
    const host = parseHostPort(e.target.value, (port) => handleInputChange('port', port))
    handleInputChange('host', host)
  }

  const hasExistingKey = formData.auth_type === 'key' &&
    formData.credentials.private_key === '***EXISTING_KEY***' && !!server?.id
  const canSubmit = canSubmitForm(formData, hasExistingKey)
  const isProcessing = connectionStatus === 'saving' || connectionStatus === 'testing'
  const showProvisioningUI = provisioning.state.isProvisioning || provisioning.state.currentStep !== 'connection'

  return (
    <Dialog open={isOpen} onClose={handleCancel} maxWidth="xs" fullWidth PaperProps={{ sx: { borderRadius: 2 } }}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 2, px: 2.5 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          {showProvisioningUI && !isEditMode ? t('servers.provisioning.title') : title}
        </Typography>
        <IconButton onClick={handleCancel} size="small" sx={{ ml: 1 }}><X size={18} /></IconButton>
      </DialogTitle>

      <DialogContent sx={{ px: 2.5, pb: 2.5 }}>
        {showProvisioningUI && !isEditMode ? (
          <ProvisioningProgress
            state={provisioning.state}
            onInstallDocker={provisioning.installDocker} onSkipDocker={provisioning.skipDocker}
            onInstallAgent={provisioning.installAgent} onSkipAgent={provisioning.skipAgent}
            onRetry={provisioning.retry} onCancel={handleCancel}
          />
        ) : (
          <ServerFormContent
            formData={formData} onInputChange={handleInputChange} onHostChange={handleHostChange}
            onAuthTypeChange={handleAuthTypeChange} onCredentialChange={handleCredentialChange}
            isEditMode={isEditMode} isProcessing={isProcessing} submitError={submitError}
          />
        )}
      </DialogContent>

      {!showProvisioningUI && (
        <DialogActions sx={{ px: 2.5, py: 1.5 }}>
          <Button variant="ghost" size="sm" onClick={handleCancel} disabled={isProcessing}>{t('common.cancel')}</Button>
          <Button variant="primary" size="sm" onClick={handleSubmit} disabled={!canSubmit} loading={isProcessing}>
            {server ? t('common.save') : t('common.add')}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  )
}
