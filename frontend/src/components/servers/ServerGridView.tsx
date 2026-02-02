/**
 * Server Grid View Component
 *
 * Displays filtered servers in a responsive grid or empty state.
 * Handles both server cards display and empty state messaging.
 * Supports bulk selection and operations.
 */

import { useTranslation } from 'react-i18next'
import { Server, Wifi, WifiOff, X } from 'lucide-react'
import { Box, Stack, Typography, Divider, Paper } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { ServerConnection } from '@/types/server'
import { ServerCard } from './ServerCard'

interface BulkActionBarProps {
  selectedCount: number
  allSelected: boolean
  onSelectAll?: () => void
  onClearSelection?: () => void
  onBulkConnect?: () => void
  onBulkDisconnect?: () => void
}

function BulkActionBar({
  selectedCount,
  allSelected,
  onSelectAll,
  onClearSelection,
  onBulkConnect,
  onBulkDisconnect
}: BulkActionBarProps) {
  const { t } = useTranslation()

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 50
      }}
    >
      <Paper
        elevation={3}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 3,
          px: 4,
          py: 3,
          borderRadius: '9999px'
        }}
      >
        <Typography variant="body2" fontWeight={500}>
          {t('servers.selectedCount', { count: selectedCount })}
        </Typography>
        <Divider orientation="vertical" flexItem sx={{ height: 20 }} />
        {onSelectAll && (
          <Box
            component="button"
            onClick={onSelectAll}
            sx={{
              fontSize: 14,
              color: 'text.secondary',
              '&:hover': { color: 'text.primary' },
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0
            }}
          >
            {allSelected ? t('servers.deselectAll') : t('servers.selectAll')}
          </Box>
        )}
        <Divider orientation="vertical" flexItem sx={{ height: 20 }} />
        {onBulkConnect && (
          <Button
            onClick={onBulkConnect}
            variant="outline"
            size="sm"
            leftIcon={<Wifi className="h-3.5 w-3.5" />}
          >
            {t('servers.connect')}
          </Button>
        )}
        {onBulkDisconnect && (
          <Button
            onClick={onBulkDisconnect}
            variant="outline"
            size="sm"
            leftIcon={<WifiOff className="h-3.5 w-3.5" />}
          >
            {t('servers.disconnect')}
          </Button>
        )}
        {onClearSelection && (
          <Button
            onClick={onClearSelection}
            variant="ghost"
            size="sm"
            leftIcon={<X className="h-3.5 w-3.5" />}
          >
            {t('common.clear')}
          </Button>
        )}
      </Paper>
    </Box>
  )
}

interface ServerGridViewProps {
  servers: ServerConnection[]
  searchTerm: string
  onEdit: (server: ServerConnection) => void
  onDelete: (serverId: string) => void
  onConnect: (serverId: string) => void
  onDisconnect?: (serverId: string) => void
  onInstallDocker?: (serverId: string) => Promise<void>
  onAddServer: () => void
  onClearSearch: () => void
  // Bulk selection props
  selectedIds?: Set<string>
  onSelectServer?: (serverId: string) => void
  onSelectAll?: () => void
  onClearSelection?: () => void
  onBulkConnect?: () => void
  onBulkDisconnect?: () => void
}

export function ServerGridView({
  servers,
  searchTerm,
  onEdit,
  onDelete,
  onConnect,
  onDisconnect,
  onInstallDocker,
  onAddServer,
  onClearSearch,
  selectedIds = new Set(),
  onSelectServer,
  onSelectAll,
  onClearSelection,
  onBulkConnect,
  onBulkDisconnect
}: ServerGridViewProps) {
  const { t } = useTranslation()
  const hasSelection = selectedIds.size > 0
  const allSelected = servers.length > 0 && selectedIds.size === servers.length

  if (servers.length > 0) {
    return (
      <Box>
        {/* Server Grid */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {servers.map((server) => (
            <ServerCard
              key={server.id}
              server={server}
              onEdit={onEdit}
              onDelete={onDelete}
              onConnect={onConnect}
              onDisconnect={onDisconnect}
              onInstallDocker={onInstallDocker}
              isSelected={selectedIds.has(server.id)}
              onSelect={onSelectServer}
            />
          ))}
        </Box>

        {/* Floating Bulk Action Bar - only shows when servers are selected */}
        {hasSelection && (
          <BulkActionBar
            selectedCount={selectedIds.size}
            allSelected={allSelected}
            onSelectAll={onSelectAll}
            onClearSelection={onClearSelection}
            onBulkConnect={onBulkConnect}
            onBulkDisconnect={onBulkDisconnect}
          />
        )}
      </Box>
    )
  }

  return (
    <Stack
      alignItems="center"
      justifyContent="center"
      sx={{ height: '100%', minHeight: 400, textAlign: 'center' }}
    >
      <Server className="h-16 w-16 text-muted-foreground mb-4" />
      <Typography variant="h6" fontWeight={600} gutterBottom>
        {searchTerm ? t('servers.noServersFound') : t('servers.noServers')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        {searchTerm
          ? t('servers.noServersFoundDescription')
          : t('servers.noServersDescription')
        }
      </Typography>
      {!searchTerm ? (
        <Button
          onClick={onAddServer}
          variant="primary"
          size="sm"
        >
          {t('servers.addServer')}
        </Button>
      ) : (
        <Button
          onClick={onClearSearch}
          variant="outline"
          size="sm"
        >
          {t('servers.clearSearch')}
        </Button>
      )}
    </Stack>
  )
}