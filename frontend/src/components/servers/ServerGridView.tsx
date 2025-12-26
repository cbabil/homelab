/**
 * Server Grid View Component
 * 
 * Displays filtered servers in a responsive grid or empty state.
 * Handles both server cards display and empty state messaging.
 */

import { Server } from 'lucide-react'
import { ServerConnection } from '@/types/server'
import { ServerCard } from './ServerCard'

interface ServerGridViewProps {
  servers: ServerConnection[]
  searchTerm: string
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
  onAddServer: () => void
  onClearSearch: () => void
}

export function ServerGridView({
  servers,
  searchTerm,
  onEdit,
  onDelete,
  onConnect,
  onDisconnect,
  onAddServer,
  onClearSearch
}: ServerGridViewProps) {
  if (servers.length > 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {servers.map((server) => (
          <ServerCard
            key={server.id}
            server={server}
            onEdit={onEdit}
            onDelete={onDelete}
            onConnect={onConnect}
            onDisconnect={onDisconnect}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="text-center py-16 px-4">
      <div className="w-20 h-20 mx-auto rounded-2xl bg-muted/50 flex items-center justify-center mb-6">
        <Server className="w-10 h-10 text-muted-foreground" />
      </div>
      <h3 className="text-xl font-semibold mb-3">
        {searchTerm ? 'No servers found' : 'No servers configured'}
      </h3>
      <p className="text-muted-foreground mb-6 max-w-md mx-auto">
        {searchTerm 
          ? 'Try adjusting your search terms or clear the search to see all servers.' 
          : 'Add a server to get started with your homelab management and monitoring.'
        }
      </p>
      {!searchTerm ? (
        <button 
          onClick={onAddServer}
          className="btn-gradient px-6 py-3 rounded-lg font-medium shadow-sm hover:shadow-md transition-all"
        >
          Add Your First Server
        </button>
      ) : (
        <button 
          onClick={onClearSearch}
          className="px-4 py-2 rounded-lg border border-input hover:bg-accent transition-colors text-sm font-medium"
        >
          Clear Search
        </button>
      )}
    </div>
  )
}