/**
 * Server Card Actions Component
 * 
 * Action buttons for server card operations (connect, edit, delete).
 */

import { Terminal, Settings, Trash2, Unplug } from 'lucide-react'
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
        <button 
          onClick={() => onDisconnect?.(server.id)}
          className="p-1.5 hover:bg-accent rounded-md"
          title="Disconnect from server"
        >
          <Unplug className="h-3.5 w-3.5" />
        </button>
      ) : (
        <button 
          onClick={() => onConnect(server.id)}
          className="p-1.5 hover:bg-accent rounded-md"
          title="Connect to server"
        >
          <Terminal className="h-3.5 w-3.5" />
        </button>
      )}
      <button 
        onClick={() => onEdit(server)}
        className="p-1.5 hover:bg-accent rounded-md"
        title="Edit server"
      >
        <Settings className="h-3.5 w-3.5" />
      </button>
      <button 
        onClick={() => onDelete(server.id)}
        className="p-1.5 hover:bg-accent rounded-md text-destructive"
        title="Delete server"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}