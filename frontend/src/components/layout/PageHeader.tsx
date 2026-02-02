/**
 * Page Header Component
 *
 * Consistent page header with title and optional subtitle.
 * Used across all pages for unified typography.
 */

import { ReactNode } from 'react'
import { Box, Stack, Typography } from '@mui/material'

interface PageHeaderProps {
  title: string
  subtitle?: string
  /** Content between title and actions (e.g., tabs) */
  children?: ReactNode
  /** Actions on the right side */
  actions?: ReactNode
}

export function PageHeader({ title, subtitle, children, actions }: PageHeaderProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
      <Stack direction="row" alignItems="center" spacing={2}>
        <Box sx={{ flexShrink: 0 }}>
          <Typography variant="h4" fontWeight={700} letterSpacing="-0.02em">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        {children}
      </Stack>
      {actions && (
        <Stack direction="row" alignItems="center" spacing={1}>
          {actions}
        </Stack>
      )}
    </Box>
  )
}
