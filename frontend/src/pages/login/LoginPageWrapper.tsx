/**
 * Login Page Wrapper Component
 *
 * Wraps the LoginPage to check if system setup is needed.
 * Also handles auth redirect so LoginPage doesn't need useAuth.
 */

import { Navigate, useLocation } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'
import { useSystemSetup } from '@/hooks/useSystemSetup'
import { useAuth } from '@/providers/AuthProvider'
import { LoginPage } from './LoginPage'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPageWrapper() {
  const { needsSetup, isLoading, error } = useSystemSetup()
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  // Redirect if already authenticated
  const state = location.state as LocationState | null
  const from = state?.from?.pathname || '/'
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  // Show loading while checking setup status
  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
          background: (theme) =>
            theme.palette.mode === 'dark'
              ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
              : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress
            size={32}
            sx={{ mb: 2, color: 'primary.main' }}
          />
          <Typography variant="body2" color="text.secondary">
            Loading...
          </Typography>
        </Box>
      </Box>
    )
  }

  // If there's an error checking setup, show login page anyway
  if (error) {
    return <LoginPage />
  }

  // If system needs setup (no admin), redirect to setup page
  if (needsSetup) {
    return <Navigate to="/setup" replace />
  }

  // System is set up, show normal login page
  return <LoginPage />
}
