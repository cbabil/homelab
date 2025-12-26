/**
 * Server Card Actions Component
 *
 * Action buttons for server card operations (connect, edit, delete).
 */

import { Terminal, Settings, Trash2, Unplug } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ServerConnection } from '@/types/server'

interface ServerCardActionsProps {
  server: ServerConnection
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
}

export function ServerCardActions({ server, onEdit, onDelete, onConnect, onDisconnect }: ServerCardActionsProps) {
  const isConnected = server.status === 'connected'
  
  return (
    <div className="flex items-center space-x-1">
      {isConnected ? (
        <Button
          onClick={() => onDisconnect?.(server.id)}
          variant="ghost"
          size="icon"
          title="Disconnect from server"
        >
          <Unplug className="h-3.5 w-3.5" />
        </Button>
      ) : (
        <Button
          onClick={() => onConnect(server.id)}
          variant="ghost"
          size="icon"
          title="Connect to server"
        >
          <Terminal className="h-3.5 w-3.5" />
        </Button>
      )}
      <Button
        onClick={() => onEdit(server)}
        variant="ghost"
        size="icon"
        title="Edit server"
      >
        <Settings className="h-3.5 w-3.5" />
      </Button>
      <Button
        onClick={() => onDelete(server.id)}
        variant="ghost"
        size="icon"
        className="text-destructive"
        title="Delete server"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}