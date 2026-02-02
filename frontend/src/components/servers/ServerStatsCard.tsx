/**
 * Server Stats Card Component
 *
 * Reusable statistics card component for displaying server metrics.
 * Used in the statistics dashboard section.
 */

import { LucideIcon } from 'lucide-react'
import { Box, Card, Stack, Typography } from '@mui/material'

interface ServerStatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  iconColor: string
  bgColor: string
}

export function ServerStatsCard({
  title,
  value,
  icon: Icon,
  iconColor,
  bgColor
}: ServerStatsCardProps) {
  return (
    <Card
      sx={{
        p: 6,
        borderRadius: 3,
        boxShadow: 1,
        '&:hover': { boxShadow: 2 },
        transition: 'box-shadow 0.2s'
      }}
    >
      <Stack direction="row" spacing={4} alignItems="center">
        <Box
          sx={{
            p: 3,
            borderRadius: 3,
            bgcolor: bgColor
          }}
        >
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>
            {title}
          </Typography>
          <Typography variant="h3" fontWeight={700}>
            {value}
          </Typography>
        </Box>
      </Stack>
    </Card>
  )
}