/**
 * Servers Page Component
 *
 * Modern server management page with enhanced layout and CRUD operations.
 * Features prominently positioned search, statistics dashboard, and server grid.
 */

import { useState, useMemo, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Box, Typography } from '@mui/material'
import { ServerPageHeader } from '@/components/servers/ServerPageHeader'
import { ServersTable } from '@/components/servers/ServersTable'
import { ServerFormDialog } from '@/components/servers/ServerFormDialog'
import { ServerDeletionDialog } from '@/components/servers/ServerDeletionDialog'
import { TablePagination } from '@/components/ui/TablePagination'
import { ConfirmationDialog, useConfirmationDialog } from '@/components/ui/ConfirmationDialog'
import type { ServerConnection } from '@/types/server'
import { useServers } from '@/hooks/useServers'
import { useAgentStatus } from '@/hooks/useAgentStatus'
import { useServerDeletion } from '@/hooks/useServerDeletion'
import { useSettingsContext } from '@/providers/SettingsProvider'
import { serverExportService } from '@/services/serverExportService'
import { useToast } from '@/components/ui/Toast'

const ITEMS_PER_PAGE = 20

export function ServersPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const {
    filteredServers, searchTerm, setSearchTerm, isFormOpen, setIsFormOpen, editingServer,
    handleAddServer, handleEditServer, handleDeleteServer, handleConnectServer,
    handleDisconnectServer, handleInstallDocker, handleRemoveDocker, handleSaveServer,
    servers, refreshServers, refreshConnectedServersInfo
  } = useServers()

  const { settings } = useSettingsContext()
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const { agentStatuses, installAgent, uninstallAgent, refreshAllAgentStatuses } = useAgentStatus()

  // Server deletion flow
  const { deletingServer, handleOpenDeleteDialog, handleCloseDeleteDialog } = useServerDeletion({
    servers, agentStatuses, uninstallAgent, removeDocker: handleRemoveDocker, deleteServer: handleDeleteServer
  })

  // Fetch agent statuses when servers change
  useEffect(() => {
    if (servers.length > 0) {
      refreshAllAgentStatuses(servers.map((s) => s.id))
    }
  }, [servers.length, refreshAllAgentStatuses])

  // Auto-refresh servers page
  useEffect(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
      refreshIntervalRef.current = null
    }
    const refreshRate = settings?.ui?.refreshRate
    if (!refreshRate || refreshRate <= 0) return

    refreshIntervalRef.current = setInterval(async () => {
      await refreshConnectedServersInfo()
      if (servers.length > 0) refreshAllAgentStatuses(servers.map((s) => s.id))
    }, refreshRate * 1000)

    return () => {
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current)
    }
  }, [settings?.ui?.refreshRate, servers, refreshConnectedServersInfo, refreshAllAgentStatuses])

  const [currentPage, setCurrentPage] = useState(1)
  useEffect(() => { setCurrentPage(1) }, [searchTerm])

  const totalPages = Math.ceil(filteredServers.length / ITEMS_PER_PAGE)
  const paginatedServers = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return filteredServers.slice(start, start + ITEMS_PER_PAGE)
  }, [filteredServers, currentPage])

  const handleConnect = useCallback(async (serverId: string) => {
    const result = await handleConnectServer(serverId)
    if (!result.success && result.isMcpError) {
      addToast({ type: 'error', title: t('servers.connectionFailed'), message: result.error || t('errors.serverError') })
    }
    return result
  }, [handleConnectServer, addToast, t])

  const getAgentErrorMessage = useCallback((errorCode?: string, fallbackMessage?: string): string => {
    const map: Record<string, string> = {
      'SERVER_NOT_FOUND': 'agent.errors.serverNotFound',
      'DOCKER_NOT_INSTALLED': 'agent.errors.dockerNotInstalled',
      'CREDENTIALS_NOT_FOUND': 'agent.errors.credentialsNotFound',
      'DEPLOY_FAILED': 'agent.errors.deployFailed',
    }
    return (errorCode && map[errorCode]) ? t(map[errorCode]) : (fallbackMessage || t('errors.generic'))
  }, [t])

  const handleInstallAgent = useCallback(async (serverId: string) => {
    const result = await installAgent(serverId)
    if (result.success && result.data) {
      addToast({ type: 'success', title: t('agent.installed'), message: t('agent.installSuccess') })
      // Refresh server data and agent statuses to update UI
      await refreshServers()
      await refreshAllAgentStatuses(servers.map((s) => s.id))
    } else {
      addToast({ type: 'error', title: t('agent.errors.installFailed'), message: getAgentErrorMessage(result.error, result.message) })
    }
  }, [installAgent, addToast, t, getAgentErrorMessage, refreshServers, refreshAllAgentStatuses, servers])

  const performUninstallAgent = useCallback(async (server: ServerConnection) => {
    const success = await uninstallAgent(server.id)
    if (success) {
      addToast({ type: 'success', title: t('agent.uninstall'), message: t('agent.uninstallSuccess') })
      // Refresh server data and agent statuses to update UI
      await refreshServers()
      await refreshAllAgentStatuses(servers.map((s) => s.id))
    } else {
      addToast({ type: 'error', title: t('agent.errors.uninstallFailed'), message: t('errors.generic') })
    }
    return success
  }, [uninstallAgent, addToast, t, refreshServers, refreshAllAgentStatuses, servers])

  const agentUninstallDialog = useConfirmationDialog<ServerConnection>({ onConfirm: performUninstallAgent })

  const handleUninstallAgent = useCallback((serverId: string) => {
    const server = servers.find(s => s.id === serverId)
    if (server) agentUninstallDialog.openDialog(server)
  }, [servers, agentUninstallDialog])

  const handleExportServers = useCallback(() => {
    const hasKeyAuth = servers.some(s => s.auth_type === 'key')
    if (!window.confirm(hasKeyAuth ? t('servers.exportWarningWithKeys') : t('servers.exportWarning'))) return
    const result = serverExportService.exportUserServers(servers)
    alert(result.success
      ? t('servers.exportSuccess', { message: result.message, filename: result.filename })
      : t('servers.exportFailed', { message: result.message }))
  }, [servers, t])

  const handleImportServers = useCallback(async () => {
    try {
      const importedServers = await serverExportService.importServers()
      let addedCount = 0, skippedCount = 0
      for (const server of importedServers) {
        if (servers.find(s => s.host === server.host && s.port === server.port)) {
          skippedCount++
        } else {
          try {
            await handleSaveServer({
              name: server.name, host: server.host, port: server.port, username: server.username, auth_type: server.auth_type,
              credentials: { password: undefined, private_key: undefined, passphrase: undefined }
            })
            addedCount++
          } catch {
            // Server import failed, skip and continue
            skippedCount++
          }
        }
      }
      refreshServers()
      const notice = addedCount > 0 ? `\n\n⚠️ ${t('servers.importCredentialsNotice')}` : ''
      alert(`✅ ${t('servers.importSuccess', { added: addedCount, skipped: skippedCount })}${notice}`)
    } catch (error) {
      alert(`⚠️ ${t('servers.importFailed', { message: error instanceof Error ? error.message : t('errors.generic') })}`)
    }
  }, [servers, refreshServers, handleSaveServer, t])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ServerPageHeader onAddServer={handleAddServer} onExportServers={handleExportServers}
        onImportServers={handleImportServers} searchTerm={searchTerm} onSearchChange={setSearchTerm} />
      <Typography variant="body2" color="text.secondary" fontWeight={600} sx={{ mb: 2 }}>
        {searchTerm ? t('servers.serverCountFiltered', { filtered: filteredServers.length, total: servers.length })
          : t('servers.serverCount', { count: servers.length })}
      </Typography>
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <ServersTable servers={paginatedServers} onEdit={handleEditServer} onDelete={handleOpenDeleteDialog}
          onConnect={handleConnect} onDisconnect={handleDisconnectServer} onInstallDocker={handleInstallDocker}
          agentStatuses={agentStatuses} onInstallAgent={handleInstallAgent} onUninstallAgent={handleUninstallAgent} />
      </Box>
      {servers.length > 0 && <TablePagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />}
      <ServerFormDialog isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} onSave={handleSaveServer}
        onDeleteServer={handleDeleteServer} onRefreshServers={refreshServers} onConnectServer={handleConnectServer}
        server={editingServer} title={editingServer ? t('servers.editServer') : t('servers.addServer')} />
      <ServerDeletionDialog open={deletingServer !== null} server={deletingServer}
        agentInfo={deletingServer ? agentStatuses.get(deletingServer.id) ?? null : null}
        onClose={handleCloseDeleteDialog} uninstallAgent={uninstallAgent}
        removeDocker={handleRemoveDocker} deleteServer={handleDeleteServer} />
      <ConfirmationDialog
        open={agentUninstallDialog.isOpen}
        title={t('agent.uninstallConfirmTitle')}
        message={t('agent.uninstallConfirmMessage', { name: agentUninstallDialog.item?.name })}
        hint={t('agent.uninstallConfirmHint')}
        confirmLabel={t('agent.actions.uninstallAgent')}
        confirmingLabel={t('servers.uninstalling')}
        cancelLabel={t('common.cancel')}
        onClose={agentUninstallDialog.closeDialog}
        onConfirm={agentUninstallDialog.handleConfirm}
      />
    </Box>
  )
}
