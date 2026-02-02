/**
 * Servers Table Component
 *
 * Table view for displaying servers using DataTable.
 * Shows status, name, connection info, OS, Docker, and actions.
 */

import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Server } from 'lucide-react'
import { DataTable } from '@/components/ui/DataTable'
import { getColumns, sortFn } from './ServersTableColumns'
import type { ServerConnection, AgentInfo } from '@/types/server'

interface ServersTableProps {
  servers: ServerConnection[]
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
  onInstallDocker?: (serverId: string) => Promise<void>
  agentStatuses?: Map<string, AgentInfo | null>
  onInstallAgent?: (serverId: string) => Promise<void>
  onUninstallAgent?: (serverId: string) => void
}

export function ServersTable({
  servers,
  onEdit,
  onDelete,
  onConnect,
  onDisconnect,
  onInstallDocker,
  agentStatuses,
  onInstallAgent,
  onUninstallAgent
}: ServersTableProps) {
  const { t } = useTranslation()
  const [installingDocker, setInstallingDocker] = useState<string | null>(null)
  const [installingAgent, setInstallingAgent] = useState<string | null>(null)

  const handleInstallDocker = async (serverId: string) => {
    if (!onInstallDocker || installingDocker) return
    setInstallingDocker(serverId)
    try {
      await onInstallDocker(serverId)
    } finally {
      setInstallingDocker(null)
    }
  }

  const handleInstallAgent = async (serverId: string) => {
    if (!onInstallAgent || installingAgent) return
    setInstallingAgent(serverId)
    try {
      await onInstallAgent(serverId)
    } finally {
      setInstallingAgent(null)
    }
  }

  const handleUninstallAgent = (serverId: string) => {
    if (!onUninstallAgent) return
    onUninstallAgent(serverId)
  }

  const columns = useMemo(() => getColumns({
    t,
    onEdit,
    onDelete,
    onConnect,
    onDisconnect,
    onInstallDocker: handleInstallDocker,
    installingDocker,
    agentStatuses,
    onInstallAgent: handleInstallAgent,
    onUninstallAgent: handleUninstallAgent,
    installingAgent
  }), [t, onEdit, onDelete, onConnect, onDisconnect, installingDocker, agentStatuses, onInstallAgent, installingAgent, onUninstallAgent])

  return (
    <DataTable
      data={servers}
      columns={columns}
      keyExtractor={(server) => server.id}
      emptyTitle={t('servers.empty.title')}
      emptyMessage={t('servers.empty.description')}
      emptyIcon={Server}
      emptyIconSize={56}
      defaultSortField="name"
      defaultSortDirection="asc"
      sortFn={sortFn}
    />
  )
}
