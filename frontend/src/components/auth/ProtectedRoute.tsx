/**
 * Protected Route Component
 *
 * Route protection wrapper that handles authentication checks,
 * role-based access control, and secure redirects with loading states.
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Shield, AlertCircle } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import MuiButton from '@mui/material/Button'
import { useAuth } from '@/providers/AuthProvider'
import { User, ProtectedRouteConfig } from '@/types/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
  config?: Partial<ProtectedRouteConfig>
  requireAuth?: boolean
  allowedRoles?: User['role'][]
  redirectTo?: string
  fallback?: React.ReactNode
}

// Loading screen component for authentication checks
const AuthLoadingScreen: React.FC = () => (
  <Box
    sx={{
      minHeight: '100vh',
      bgcolor: 'background.default',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <Box sx={{ textAlign: 'center' }}>
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 64,
          height: 64,
          bgcolor: 'primary.main',
          opacity: 0.1,
          borderRadius: 3,
          mb: 2,
        }}
      >
        <CircularProgress size={32} sx={{ color: 'primary.main' }} />
      </Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Authenticating
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Please wait while we verify your credentials...
      </Typography>
    </Box>
  </Box>
)

// Access denied screen for unauthorized users
const AccessDeniedScreen: React.FC<{
  message?: string
  onRetry?: () => void
}> = ({ message, onRetry }) => (
  <Box
    sx={{
      minHeight: '100vh',
      bgcolor: 'background.default',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: 2,
    }}
  >
    <Box sx={{ maxWidth: 448, width: '100%', textAlign: 'center' }}>
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 64,
          height: 64,
          bgcolor: (theme) =>
            theme.palette.mode === 'dark' ? 'rgba(239, 68, 68, 0.5)' : 'rgba(252, 165, 165, 1)',
          borderRadius: 3,
          mb: 2,
        }}
      >
        <AlertCircle size={32} color="currentColor" style={{ color: '#ef4444' }} />
      </Box>
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Access Denied
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {message || 'You do not have permission to access this page.'}
      </Typography>
      {onRetry && (
        <MuiButton
          variant="text"
          onClick={onRetry}
          startIcon={<Shield size={16} />}
        >
          Try Again
        </MuiButton>
      )}
    </Box>
  </Box>
)

export function ProtectedRoute({
  children,
  config,
  requireAuth = true,
  allowedRoles,
  redirectTo = '/login',
  fallback
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, error, refreshSession } = useAuth()
  const location = useLocation()

  // Merge props with config object
  const finalConfig: ProtectedRouteConfig = {
    requireAuth,
    redirectTo,
    allowedRoles,
    ...config
  }

  // Show loading screen while authentication is being determined
  if (isLoading) {
    return fallback || <AuthLoadingScreen />
  }

  // If authentication is required but user is not authenticated
  if (finalConfig.requireAuth && !isAuthenticated) {
    // Store the intended destination for redirect after login
    return (
      <Navigate 
        to={finalConfig.redirectTo || '/login'} 
        state={{ from: location }} 
        replace 
      />
    )
  }

  // If authentication is not required and user is not authenticated, allow access
  if (!finalConfig.requireAuth && !isAuthenticated) {
    return <>{children}</>
  }

  // If user is authenticated, check for role-based access
  if (isAuthenticated && user) {
    // Check if specific roles are required
    if (finalConfig.allowedRoles && finalConfig.allowedRoles.length > 0) {
      const hasRequiredRole = finalConfig.allowedRoles.includes(user.role)
      
      if (!hasRequiredRole) {
        const roleNames = finalConfig.allowedRoles.join(', ')
        return (
          <AccessDeniedScreen 
            message={`This page requires ${roleNames} role access. Your current role is: ${user.role}`}
            onRetry={() => window.location.reload()}
          />
        )
      }
    }

    // Check if user account is active
    if (!user.isActive) {
      return (
        <AccessDeniedScreen 
          message="Your account has been deactivated. Please contact your administrator."
        />
      )
    }

    // All checks passed, render the protected content
    return <>{children}</>
  }

  // Handle error states
  if (error) {
    return (
      <AccessDeniedScreen 
        message={`Authentication error: ${error}`}
        onRetry={refreshSession}
      />
    )
  }

  // Fallback case - should not normally reach here
  return (
    <Navigate 
      to={finalConfig.redirectTo || '/login'} 
      state={{ from: location }} 
      replace 
    />
  )
}

// Higher-order component for route protection
export function withProtectedRoute<P extends object>(
  Component: React.ComponentType<P>,
  config?: Partial<ProtectedRouteConfig>
) {
  return function ProtectedComponent(props: P) {
    return (
      <ProtectedRoute config={config}>
        <Component {...props} />
      </ProtectedRoute>
    )
  }
}

// Role-based route protection shortcuts
export function AdminRoute({ children, ...props }: Omit<ProtectedRouteProps, 'allowedRoles'>) {
  return (
    <ProtectedRoute {...props} allowedRoles={['admin']}>
      {children}
    </ProtectedRoute>
  )
}

export function UserRoute({ children, ...props }: Omit<ProtectedRouteProps, 'allowedRoles'>) {
  return (
    <ProtectedRoute {...props} allowedRoles={['user', 'admin']}>
      {children}
    </ProtectedRoute>
  )
}

// Public route that redirects authenticated users
export function PublicRoute({
  children,
  redirectTo = '/'
}: {
  children: React.ReactNode
  redirectTo?: string
}) {
  const { isAuthenticated } = useAuth()

  // If user is authenticated, redirect to protected area
  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  // User is not authenticated, show public content
  // No loading screen needed - let the page handle its own loading states
  return <>{children}</>
}