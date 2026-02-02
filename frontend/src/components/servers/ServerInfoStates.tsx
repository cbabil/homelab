/**
 * Server Info States Component
 *
 * Loading and error state components for server information display.
 */

import { Loader2, Monitor } from 'lucide-react'
import { Box, Stack, Typography } from '@mui/material'

export function LoadingState() {
  return (
    <Stack direction="row" alignItems="center" justifyContent="center" spacing={1.5} sx={{ py: 2 }}>
      <Loader2 className="h-2.5 w-2.5 animate-spin text-muted-foreground" />
      <Typography sx={{ fontSize: 10, color: 'text.secondary' }}>Loading...</Typography>
    </Stack>
  )
}

export function ErrorState() {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
      <Box sx={{ textAlign: 'center' }}>
        <Monitor className="h-3 w-3 mx-auto text-muted-foreground/50" />
        <Typography sx={{ fontSize: 10, color: 'text.secondary', mt: 0.5 }}>Info unavailable</Typography>
      </Box>
    </Box>
  )
}