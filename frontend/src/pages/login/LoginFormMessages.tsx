/**
 * Login Form Messages Component
 *
 * Simple error text for the login form.
 * No background, no animations - just text.
 * Always reserves space to prevent layout shift.
 */

import Typography from '@mui/material/Typography'

interface LoginFormMessagesProps {
  submitError?: string
}

export function LoginFormMessages({ submitError }: LoginFormMessagesProps) {
  return (
    <Typography
      color="error"
      variant="body2"
      align="center"
      sx={{
        mb: 1,
        minHeight: '1.5em',
        visibility: submitError ? 'visible' : 'hidden'
      }}
    >
      {submitError || ' '}
    </Typography>
  )
}