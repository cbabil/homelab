/**
 * Applications Page Header Component
 *
 * Header section with title, description, and Add App button for the Applications page.
 */

import { Plus } from 'lucide-react'
import { Box, Typography, Stack } from '@mui/material'
import { Button } from '@/components/ui/Button'

interface ApplicationsPageHeaderProps {
  onAddApp: () => void
}

export function ApplicationsPageHeader({ onAddApp }: ApplicationsPageHeaderProps) {
  return (
    <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="h4" component="h2">Applications</Typography>
        <Typography variant="body2" color="text.secondary" noWrap>
          Discover and deploy applications for your tomo infrastructure.
        </Typography>
      </Box>

      <Button
        onClick={onAddApp}
        variant="primary"
        size="sm"
        leftIcon={<Plus size={14} />}
        sx={{ flexShrink: 0 }}
      >
        Add App
      </Button>
    </Stack>
  )
}