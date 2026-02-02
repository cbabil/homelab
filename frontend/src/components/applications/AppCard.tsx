/**
 * Application Card Component
 *
 * Individual application card with deploy/manage actions.
 */

import { useState } from 'react'
import { Download, Trash2, Check, Package } from 'lucide-react'
import { Box, Typography, IconButton, Stack, Chip } from '@mui/material'
import { App } from '@/types/app'

// Check if a string is a valid image URL
function isValidIconUrl(icon: string | undefined): boolean {
  if (!icon) return false
  return icon.startsWith('http://') || icon.startsWith('https://') || icon.startsWith('data:image/')
}

interface AppCardProps {
  app: App
  isSelected?: boolean
  onToggleSelect?: (appId: string) => void
  onUninstall?: (appId: string, serverId?: string) => void
  onDeploy?: (appId: string) => void
}

interface AppCardActionsProps {
  isInstalled: boolean
  onDeploy: () => void
  onUninstall: () => void
}

function AppCardActions({ isInstalled, onDeploy, onUninstall }: AppCardActionsProps) {
  const actionButtonSx = {
    p: 0.25,
    borderRadius: 0.5,
    color: 'text.secondary'
  }

  if (isInstalled) {
    return (
      <>
        <Check className="h-3 w-3 text-green-500" />
        <IconButton
          size="small"
          onClick={(e) => { e.stopPropagation(); onUninstall() }}
          title="Uninstall"
          sx={{ ...actionButtonSx, '&:hover': { bgcolor: 'error.light', color: 'error.main' } }}
        >
          <Trash2 className="h-3 w-3" />
        </IconButton>
      </>
    )
  }

  return (
    <IconButton
      size="small"
      onClick={(e) => { e.stopPropagation(); onDeploy() }}
      title="Deploy"
      sx={{ ...actionButtonSx, '&:hover': { bgcolor: 'action.hover', color: 'primary.main' } }}
    >
      <Download className="h-3 w-3" />
    </IconButton>
  )
}

export function AppCard({ app, isSelected = false, onToggleSelect, onUninstall, onDeploy }: AppCardProps) {
  const [iconError, setIconError] = useState(false)

  const handleDeploy = () => {
    if (onDeploy) {
      onDeploy(app.id)
    }
  }

  const handleUninstall = () => {
    if (onUninstall) {
      onUninstall(app.id, app.connectedServerId ?? undefined)
    }
  }

  const isInstalled = app.status === 'installed'
  const hasValidIcon = isValidIconUrl(app.icon) && !iconError
  const canSelect = onToggleSelect !== undefined

  const handleCardClick = () => {
    if (canSelect) {
      onToggleSelect(app.id)
    }
  }

  // Status bar color: green for installed, gray for not installed
  const statusBarColor = isInstalled ? 'success.main' : 'grey.400'

  return (
    <Box
      onClick={handleCardClick}
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        aspectRatio: '1',
        p: 0.75,
        pt: 0,
        borderRadius: 1,
        border: 1,
        borderColor: isSelected ? 'primary.main' : 'divider',
        bgcolor: isSelected ? 'primary.light' : 'background.paper',
        boxShadow: 1,
        cursor: canSelect ? 'pointer' : 'default',
        overflow: 'hidden',
        ...(isSelected && {
          outline: 2,
          outlineColor: 'primary.main',
          outlineStyle: 'solid'
        }),
        ...(canSelect && {
          '&:hover': {
            borderColor: 'primary.main',
            opacity: 0.8
          }
        })
      }}
    >
      {/* Status bar at top */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          bgcolor: statusBarColor
        }}
      />
      {/* Top right: Status + Actions */}
      <Stack direction="row" spacing={0.25} sx={{ position: 'absolute', top: 6, right: 6, zIndex: 10 }}>
        <AppCardActions isInstalled={isInstalled} onDeploy={handleDeploy} onUninstall={handleUninstall} />
      </Stack>

      {/* Main content - centered vertically */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        {/* Icon */}
        <Box sx={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {hasValidIcon ? (
            <img
              src={app.icon}
              alt=""
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              onError={() => setIconError(true)}
              onLoad={(e) => {
                const img = e.target as HTMLImageElement
                if (img.naturalWidth === 0) setIconError(true)
              }}
            />
          ) : (
            <Package className="h-3.5 w-3.5 text-muted-foreground" />
          )}
        </Box>

        {/* Name + Version */}
        <Typography variant="caption" fontWeight={500} noWrap sx={{ width: '100%', textAlign: 'center', mt: 0.25 }}>
          {app.name}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '10px' }}>
          v{app.version}
        </Typography>
      </Box>

      {/* Category - at bottom */}
      <Chip
        label={app.category.name}
        size="small"
        sx={{
          fontSize: '10px',
          height: 18,
          bgcolor: 'primary.light',
          color: 'primary.main',
          maxWidth: '100%',
          '& .MuiChip-label': {
            px: 0.75,
            py: 0.25
          }
        }}
      />
    </Box>
  )
}