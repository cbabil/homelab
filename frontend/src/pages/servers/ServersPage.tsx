/**
 * Servers Page Component
 * 
 * Modern server management page with enhanced layout and CRUD operations.
 * Features prominently positioned search, statistics dashboard, and server grid.
 */

import { Server } from 'lucide-react'
import { ServerPageHeader } from '@/components/servers/ServerPageHeader'
import { ServerSearchBar } from '@/components/servers/ServerSearchBar'
import { ServerStatsCard } from '@/components/servers/ServerStatsCard'
import { ServerGridView } from '@/components/servers/ServerGridView'
import { ServerFormDialog } from '@/components/servers/ServerFormDialog'
import { useServers } from '@/hooks/useServers'
import { serverExportService } from '@/services/serverExportService'
import { serverStorageService } from '@/services/serverStorageService'

export function ServersPage() {
  const {
    filteredServers,
    searchTerm,
    setSearchTerm,
    isFormOpen,
    setIsFormOpen,
    editingServer,
    connectedCount,
    totalServers,
    healthPercentage,
    handleAddServer,
    handleEditServer,
    handleDeleteServer,
    handleConnectServer,
    handleDisconnectServer,
    handleSaveServer,
    servers,
    refreshServers
  } = useServers()

  const handleExportServers = () => {
    const result = serverExportService.exportUserServers(servers)
    if (result.success) {
      alert(`✅ Export successful: ${result.message}. File downloaded: ${result.filename}`)
    } else {
      alert(`⚠️ Export failed: ${result.message}`)
    }
  }

  const handleImportServers = async () => {
    try {
      const importedServers = await serverExportService.importServers()
      
      let addedCount = 0
      let skippedCount = 0
      
      for (const server of importedServers) {
        // Check if server already exists (by hostname and port)
        const existingServer = servers.find(s => 
          s.hostname === server.hostname && s.port === server.port
        )
        
        if (existingServer) {
          skippedCount++
        } else {
          // Generate new ID for imported server
          const serverInput = {
            name: server.name,
            hostname: server.hostname,
            port: server.port,
            username: server.username,
            authType: server.authType,
            password: server.authType === 'password' ? server.password : undefined,
            privateKeyFile: server.authType === 'key' ? server.privateKeyFile : undefined
          }
          
          serverStorageService.addServer(serverInput)
          addedCount++
        }
      }
      
      // Refresh the servers list
      refreshServers()
      
      const message = `Import completed: ${addedCount} servers added, ${skippedCount} skipped (already exist)`
      alert(`✅ ${message}`)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      alert(`⚠️ Import failed: ${errorMessage}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <ServerPageHeader 
        onAddServer={handleAddServer}
        onExportServers={handleExportServers}
        onImportServers={handleImportServers}
      />

      {/* Search Section - Prominently positioned at top of content */}
      <ServerSearchBar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        resultCount={filteredServers.length}
        totalCount={totalServers}
      />

      {/* Statistics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ServerStatsCard
          title="Connected"
          value={connectedCount}
          icon={Server}
          iconColor="text-green-600 dark:text-green-400"
          bgColor="bg-green-100 dark:bg-green-950/50"
        />
        <ServerStatsCard
          title="Total Servers"
          value={totalServers}
          icon={Server}
          iconColor="text-blue-600 dark:text-blue-400"
          bgColor="bg-blue-100 dark:bg-blue-950/50"
        />
        <ServerStatsCard
          title="Health"
          value={`${healthPercentage}%`}
          icon={Server}
          iconColor="text-purple-600 dark:text-purple-400"
          bgColor="bg-purple-100 dark:bg-purple-950/50"
        />
      </div>

      {/* Server Grid */}
      <ServerGridView
        servers={filteredServers}
        searchTerm={searchTerm}
        onEdit={handleEditServer}
        onDelete={handleDeleteServer}
        onConnect={handleConnectServer}
        onDisconnect={handleDisconnectServer}
        onAddServer={handleAddServer}
        onClearSearch={() => setSearchTerm('')}
      />

      {/* Form Dialog */}
      <ServerFormDialog
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSave={handleSaveServer}
        server={editingServer}
        title={editingServer ? 'Edit Server' : 'Add New Server'}
      />
    </div>
  )
}