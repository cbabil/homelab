/**
 * Server Info Display Component
 *
 * Compact server system information display with loading states.
 * Optimized for minimal vertical space usage.
 */

import { useState } from 'react'
import { Cpu, Clock, Container, Monitor, Download, Loader2 } from 'lucide-react'
import { Box, Stack } from '@mui/material'
import { SystemInfo, ServerStatus } from '@/types/server'
import { InfoItem } from './InfoItem'
import { LoadingState, ErrorState } from './ServerInfoStates'
import { formatUptime } from './ServerInfoUtils'

interface DockerInfoProps {
  dockerVersion?: string
  onInstallDocker?: () => Promise<void>
}

function DockerInfo({ dockerVersion, onInstallDocker }: DockerInfoProps) {
  const [isInstalling, setIsInstalling] = useState(false)

  const dockerNotInstalled = !dockerVersion ||
    dockerVersion.toLowerCase() === 'not installed'

  const handleInstallDocker = async () => {
    if (!onInstallDocker || isInstalling) return
    setIsInstalling(true)
    try {
      await onInstallDocker()
    } finally {
      setIsInstalling(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
      <Container style={{ width: 10, height: 10, flexShrink: 0 }} />
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Box component="p" sx={{ fontSize: 10, color: 'text.secondary', lineHeight: 1 }}>
          Docker
        </Box>
        {dockerNotInstalled ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              component="p"
              sx={{
                fontSize: 10,
                fontWeight: 400,
                color: 'error.main',
                fontStyle: 'italic',
                lineHeight: 1.2
              }}
            >
              Not installed
            </Box>
            {onInstallDocker && (
              <Box
                component="button"
                onClick={handleInstallDocker}
                disabled={isInstalling}
                sx={{
                  fontSize: 10,
                  color: 'primary.main',
                  '&:hover': { color: 'primary.dark' },
                  fontWeight: 500,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                  '&:disabled': { opacity: 0.5, cursor: 'not-allowed' }
                }}
              >
                {isInstalling ? (
                  <>
                    <Loader2 className="h-2.5 w-2.5 animate-spin" />
                    Installing...
                  </>
                ) : (
                  <>
                    <Download className="h-2.5 w-2.5" />
                    Install
                  </>
                )}
              </Box>
            )}
          </Box>
        ) : (
          <Box
            component="p"
            sx={{
              fontSize: 10,
              fontWeight: 500,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              lineHeight: 1.2
            }}
          >
            {dockerVersion}
          </Box>
        )}
      </Box>
    </Box>
  )
}

interface ServerInfoDisplayProps {
  systemInfo?: SystemInfo
  status: ServerStatus
  className?: string
  onInstallDocker?: () => Promise<void>
}

export function ServerInfoDisplay({ systemInfo, status, className, onInstallDocker }: ServerInfoDisplayProps) {
  // Show loading state when preparing
  if (status === 'preparing') {
    return (
      <Box
        className={className}
        sx={{
          borderRadius: 1,
          border: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          opacity: 0.5
        }}
      >
        <LoadingState />
      </Box>
    )
  }

  // Show error state when no system info is available and status indicates a problem
  if (!systemInfo && (status === 'error' || status === 'disconnected')) {
    return (
      <Box
        className={className}
        sx={{
          borderRadius: 1,
          border: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          opacity: 0.5
        }}
      >
        <ErrorState />
      </Box>
    )
  }

  // Don't render anything if no system info and status is not problematic
  if (!systemInfo) {
    return null
  }

  return (
    <Box
      className={className}
      sx={{
        borderRadius: 1,
        border: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
        opacity: 0.5,
        p: 2
      }}
    >
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={3}>
          <Box sx={{ flex: 1 }}>
            <InfoItem
              icon={Monitor}
              label="OS"
              value={systemInfo.os}
            />
          </Box>

          <Box sx={{ flex: 1 }}>
            <InfoItem
              icon={Cpu}
              label="Arch"
              value={systemInfo.architecture}
            />
          </Box>
        </Stack>

        <Stack direction="row" spacing={3}>
          <Box sx={{ flex: 1 }}>
            <InfoItem
              icon={Clock}
              label="Uptime"
              value={formatUptime(systemInfo.uptime)}
            />
          </Box>

          <Box sx={{ flex: 1 }}>
            <DockerInfo
              dockerVersion={systemInfo.docker_version}
              onInstallDocker={onInstallDocker}
            />
          </Box>
        </Stack>
      </Stack>
    </Box>
  )
}