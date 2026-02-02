/**
 * Applications Empty State Component
 *
 * Empty state displayed when no applications match the current filters.
 */

import { Search } from 'lucide-react'
import { Box, Typography } from '@mui/material'

export function ApplicationsEmptyState() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        textAlign: 'center'
      }}
    >
      <Box sx={{ mb: 2, color: 'text.secondary' }}>
        <Search size={64} style={{ opacity: 0.5 }} />
      </Box>
      <Typography variant="h6" gutterBottom>
        No applications found
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Try adjusting your search terms or filters.
      </Typography>
    </Box>
  )
}