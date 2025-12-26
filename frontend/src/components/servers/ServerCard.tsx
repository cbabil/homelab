/**
 * Server Card Component
 * 
 * Displays individual server information with status and actions.
 */

import { Wifi, WifiOff, AlertCircle, Clock } from 'lucide-react'
import { ServerConnection } from '@/types/server'
import { cn } from '@/utils/cn'
import { ServerInfoDisplay } from './ServerInfoDisplay'
import { ServerCardActions } from './ServerCardActions'

interface ServerCardProps {
  server: ServerConnection
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
}

const statusConfig = {
  connected: {
    icon: Wifi,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-950/50',
    label: 'Connected'
  },
  disconnected: {
    icon: WifiOff, 
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-950/50',
    label: 'Disconnected'
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-600 dark:text-red-400', 
    bg: 'bg-red-50 dark:bg-red-950/50',
    label: 'Error'
  },
  preparing: {
    icon: Clock,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-950/50', 
    label: 'Preparing'
  }
}

export function ServerCard({ server, onEdit, onDelete, onConnect, onDisconnect }: ServerCardProps) {
  const status = statusConfig[server.status]
  const StatusIcon = status.icon

  return (
    <div className="bg-card p-4 rounded-xl border h-full flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="text-base font-semibold truncate">{server.name}</h3>
            <div className={cn("flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium", status.bg, status.color)}>
              <StatusIcon className="h-3 w-3" />
              <span>{status.label}</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground truncate">
            {server.username}@{server.host}:{server.port}
          </p>
        </div>
        
        <ServerCardActions 
          server={server}
          onEdit={onEdit}
          onDelete={onDelete}
          onConnect={onConnect}
          onDisconnect={onDisconnect}
        />
      </div>

      <div className="flex-1">
        <ServerInfoDisplay 
          systemInfo={server.system_info}
          status={server.status}
        />
      </div>

      <div className="pt-3 mt-auto border-t border-border/50">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Auth: {server.auth_type}</span>
          {server.last_connected && (
            <span>Last: {new Date(server.last_connected).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </div>
  )
}