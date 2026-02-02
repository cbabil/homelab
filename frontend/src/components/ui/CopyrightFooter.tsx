/**
 * Copyright Footer Component
 *
 * Reusable footer component that displays copyright information.
 * App name is configured via VITE_APP_NAME environment variable.
 */

import Typography from '@mui/material/Typography'

const APP_NAME = import.meta.env.VITE_APP_NAME || 'Tomo'

export function CopyrightFooter() {
  const currentYear = new Date().getFullYear()

  return (
    <Typography
      variant="caption"
      color="text.secondary"
      align="center"
      component="p"
      sx={{ display: 'block' }}
    >
      &copy; {currentYear} {APP_NAME}. All rights reserved.
    </Typography>
  )
}
