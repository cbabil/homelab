/**
 * useServerDeletion Hook
 *
 * Manages server deletion flow with agent/docker cleanup.
 */

import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { ServerConnection, AgentInfo } from '@/types/server'
import { useToast } from '@/components/ui/Toast'

interface UseServerDeletionProps {
  servers: ServerConnection[]
  agentStatuses: Map<string, AgentInfo | null>
  uninstallAgent: (serverId: string) => Promise<boolean>
  removeDocker: (serverId: string) => Promise<boolean>
  deleteServer: (serverId: string) => Promise<void>
}

export function useServerDeletion({
  servers,
  agentStatuses,
  uninstallAgent,
  removeDocker,
  deleteServer
}: UseServerDeletionProps) {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [deletingServer, setDeletingServer] = useState<ServerConnection | null>(null)

  const handleOpenDeleteDialog = useCallback((serverId: string) => {
    const server = servers.find(s => s.id === serverId)
    if (server) {
      setDeletingServer(server)
    }
  }, [servers])

  const handleCloseDeleteDialog = useCallback(() => {
    setDeletingServer(null)
  }, [])

  const handleUninstallAgentForDeletion = useCallback(async (serverId: string): Promise<boolean> => {
    const success = await uninstallAgent(serverId)
    if (success) {
      addToast({
        type: 'success',
        title: t('agent.uninstall'),
        message: t('agent.uninstallSuccess')
      })
    } else {
      addToast({
        type: 'error',
        title: t('agent.errors.uninstallFailed'),
        message: t('errors.generic')
      })
    }
    return success
  }, [uninstallAgent, addToast, t])

  const handleRemoveDockerForDeletion = useCallback(async (serverId: string): Promise<boolean> => {
    const success = await removeDocker(serverId)
    if (success) {
      addToast({
        type: 'success',
        title: t('servers.dockerRemoved'),
        message: t('servers.dockerRemovedSuccess')
      })
    } else {
      addToast({
        type: 'error',
        title: t('servers.dockerRemoveFailed'),
        message: t('errors.generic')
      })
    }
    return success
  }, [removeDocker, addToast, t])

  const handleDeleteComplete = useCallback(async (serverId: string) => {
    await deleteServer(serverId)
    setDeletingServer(null)
    addToast({
      type: 'success',
      title: t('servers.deleted'),
      message: t('servers.deletedSuccess')
    })
  }, [deleteServer, addToast, t])

  const getAgentInfoForServer = useCallback((serverId: string) => {
    return agentStatuses.get(serverId) ?? null
  }, [agentStatuses])

  return {
    deletingServer,
    handleOpenDeleteDialog,
    handleCloseDeleteDialog,
    handleUninstallAgentForDeletion,
    handleRemoveDockerForDeletion,
    handleDeleteComplete,
    getAgentInfoForServer
  }
}
