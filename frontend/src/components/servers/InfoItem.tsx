/**
 * Info Item Component
 *
 * Displays individual server information items with icon and label/value pairs.
 */

import { type ComponentType } from 'react'
import { Box, Stack, Typography } from '@mui/material'

interface InfoItemProps {
  icon: ComponentType<{ className?: string }>
  label: string
  value?: string
  className?: string
}

export function InfoItem({ icon: Icon, label, value, className }: InfoItemProps) {
  const getNotAvailableMessage = (label: string) => {
    if (label.includes('Docker')) return 'Docker not installed'
    if (label.includes('OS')) return 'OS information unavailable'
    if (label.includes('Architecture')) return 'Architecture unavailable'
    if (label.includes('Uptime')) return 'Uptime unavailable'
    if (label.includes('Kernel')) return 'Kernel info unavailable'
    return 'Not available'
  }

  return (
    <Stack
      direction="row"
      spacing={1.5}
      alignItems="center"
      className={className}
    >
      <Icon className="h-2.5 w-2.5 text-muted-foreground flex-shrink-0" />
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography
          sx={{
            fontSize: 10,
            color: 'text.secondary',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            lineHeight: 1
          }}
        >
          {label}
        </Typography>
        <Typography
          sx={{
            fontSize: 10,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            lineHeight: 1.2,
            fontWeight: value ? 500 : 400,
            color: value ? 'text.primary' : 'text.secondary',
            fontStyle: value ? 'normal' : 'italic'
          }}
        >
          {value || getNotAvailableMessage(label)}
        </Typography>
      </Box>
    </Stack>
  )
}