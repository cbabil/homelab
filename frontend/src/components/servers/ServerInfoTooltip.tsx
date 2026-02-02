/**
 * Server Info Tooltip Component
 *
 * Shows server system information on hover over an info icon.
 */

import React, { useState } from 'react'
import { Info, Monitor, Cpu, Container, Loader2 } from 'lucide-react'
import { Box, IconButton, Paper, Stack, Typography } from '@mui/material'
import { SystemInfo } from '@/types/server'

interface ServerInfoTooltipProps {
  systemInfo: SystemInfo
  onInstallDocker?: () => Promise<void>
}

export function ServerInfoTooltip({ systemInfo, onInstallDocker }: ServerInfoTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isInstalling, setIsInstalling] = useState(false)

  const dockerNotInstalled = !systemInfo.docker_version ||
    systemInfo.docker_version.toLowerCase() === 'not installed'

  const handleInstallDocker = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!onInstallDocker || isInstalling) return
    setIsInstalling(true)
    try {
      await onInstallDocker()
    } finally {
      setIsInstalling(false)
    }
  }

  return (
    <Box
      sx={{ position: 'relative' }}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onClick={(e) => e.stopPropagation()}
    >
      <IconButton
        size="small"
        title="Server info"
        sx={{
          p: 0.5,
          borderRadius: 1,
          '&:hover': { bgcolor: 'action.hover' },
          transition: 'background-color 0.2s'
        }}
      >
        <Info className="h-3.5 w-3.5 text-muted-foreground" />
      </IconButton>

      {isOpen && (
        <Box sx={{ position: 'absolute', bottom: '100%', right: 0, mb: 2, zIndex: 50 }}>
          <Paper
            elevation={3}
            sx={{
              borderRadius: 2,
              p: 3,
              minWidth: 200
            }}
          >
            <Stack spacing={2}>
              <InfoRow icon={Monitor} label="OS" value={systemInfo.os} />
              <InfoRow icon={Cpu} label="Architecture" value={systemInfo.architecture} />

              <Stack direction="row" spacing={2} alignItems="center">
                <Container className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                <Typography variant="caption" color="text.secondary">Docker:</Typography>
                {dockerNotInstalled ? (
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="caption" sx={{ color: 'error.main', fontStyle: 'italic' }}>
                      Not installed
                    </Typography>
                    {onInstallDocker && (
                      <Box
                        component="button"
                        onClick={handleInstallDocker}
                        disabled={isInstalling}
                        sx={{
                          fontSize: 12,
                          color: 'primary.main',
                          '&:hover': { color: 'primary.dark' },
                          fontWeight: 500,
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 0,
                          '&:disabled': { opacity: 0.5, cursor: 'not-allowed' }
                        }}
                      >
                        {isInstalling ? (
                          <Stack direction="row" spacing={1} alignItems="center" component="span">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Installing...
                          </Stack>
                        ) : (
                          'Install'
                        )}
                      </Box>
                    )}
                  </Stack>
                ) : (
                  <Typography variant="caption" fontWeight={500}>{systemInfo.docker_version}</Typography>
                )}
              </Stack>
            </Stack>
          </Paper>
        </Box>
      )}
    </Box>
  )
}

function InfoRow({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>, label: string, value?: string }) {
  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <Icon className="h-3 w-3 text-muted-foreground flex-shrink-0" />
      <Typography variant="caption" color="text.secondary">{label}:</Typography>
      <Typography variant="caption" fontWeight={500} noWrap>{value || 'N/A'}</Typography>
    </Stack>
  )
}
