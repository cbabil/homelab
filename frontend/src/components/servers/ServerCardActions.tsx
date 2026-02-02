/**
 * Server Card Actions Component
 *
 * Action buttons for server card operations (connect, edit, delete).
 */

import { useTranslation } from 'react-i18next'
import { Terminal, Settings, Trash2, Unplug } from 'lucide-react'
import { Box, IconButton } from '@mui/material'
import { ServerConnection } from '@/types/server'

interface ServerCardActionsProps {
  server: ServerConnection
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
}

export function ServerCardActions({ server, onEdit, onDelete, onConnect, onDisconnect }: ServerCardActionsProps) {
  const { t } = useTranslation()
  const isConnected = server.status === 'connected'

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {isConnected ? (
        <IconButton
          onClick={() => onDisconnect?.(server.id)}
          size="small"
          title={t('servers.actions.disconnectFromServer')}
          sx={{
            p: 0.5,
            borderRadius: 1,
            '&:hover': { bgcolor: 'action.hover' }
          }}
        >
          <Unplug style={{ width: 14, height: 14 }} />
        </IconButton>
      ) : (
        <IconButton
          onClick={() => onConnect(server.id)}
          size="small"
          title={t('servers.actions.connectToServer')}
          sx={{
            p: 0.5,
            borderRadius: 1,
            '&:hover': { bgcolor: 'action.hover' }
          }}
        >
          <Terminal style={{ width: 14, height: 14 }} />
        </IconButton>
      )}
      <IconButton
        onClick={() => onEdit(server)}
        size="small"
        title={t('servers.actions.editServer')}
        sx={{
          p: 0.5,
          borderRadius: 1,
          '&:hover': { bgcolor: 'action.hover' }
        }}
      >
        <Settings style={{ width: 14, height: 14 }} />
      </IconButton>
      <IconButton
        onClick={() => onDelete(server.id)}
        size="small"
        title={t('servers.actions.deleteServer')}
        sx={{
          p: 0.5,
          borderRadius: 1,
          color: 'error.main',
          '&:hover': { bgcolor: 'action.hover' }
        }}
      >
        <Trash2 style={{ width: 14, height: 14 }} />
      </IconButton>
    </Box>
  )
}