/**
 * Protected Route Component
 *
 * Route protection wrapper that handles authentication checks,
 * role-based access control, and secure redirects with loading states.
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Loader2, Shield, AlertCircle } from 'lucide-react'
import { useAuth } from '@/providers/AuthProvider'
import { User, ProtectedRouteConfig } from '@/types/auth'
import { Button } from '@/components/ui/Button'

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
  <div className="min-h-screen bg-background flex items-center justify-center">
    <div className="text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-2xl mb-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
      <h2 className="text-lg font-semibold text-foreground mb-2">
        Authenticating
      </h2>
      <p className="text-sm text-muted-foreground">
        Please wait while we verify your credentials...
      </p>
    </div>
  </div>
)

// Access denied screen for unauthorized users
const AccessDeniedScreen: React.FC<{
  message?: string
  onRetry?: () => void
}> = ({ message, onRetry }) => (
  <div className="min-h-screen bg-background flex items-center justify-center p-4">
    <div className="max-w-md w-full text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/50 rounded-2xl mb-4">
        <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
      </div>
      <h2 className="text-xl font-bold text-foreground mb-2">
        Access Denied
      </h2>
      <p className="text-muted-foreground mb-6">
        {message || 'You do not have permission to access this page.'}
      </p>
      {onRetry && (
        <Button
          variant="ghost"
          onClick={onRetry}
          leftIcon={<Shield className="w-4 h-4" />}
        >
          Try Again
        </Button>
      )}
    </div>
  </div>
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