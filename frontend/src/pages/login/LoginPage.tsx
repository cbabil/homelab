/**
 * Login Page Component
 * 
 * Comprehensive login page with form validation, security features,
 * and excellent user experience. Refactored to maintain 100-line limit per CLAUDE.md rules.
 */

import React from 'react'
import { Navigate, useLocation, Link } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { useAuth } from '@/providers/AuthProvider'
import { LoginForm } from './LoginForm'

export function LoginPage() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  
  // Redirect to intended destination after login
  const from = (location.state as any)?.from?.pathname || '/'

  // If already authenticated, redirect to intended destination
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Welcome Back
          </h1>
          <p className="text-muted-foreground">
            Sign in to your Homelab Assistant
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-card/50 backdrop-blur border border-border/50 rounded-2xl p-6 shadow-xl">
          <LoginForm />
        </div>

        {/* Registration Link */}
        <div className="text-center mt-6">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link 
              to="/register" 
              className="text-primary hover:text-primary/80 transition-colors font-medium"
            >
              Create one
            </Link>
          </p>
        </div>

        {/* Footer */}
        <div className="text-center mt-4">
          <p className="text-sm text-muted-foreground">
            Homelab Assistant v1.0 - Secure Access
          </p>
        </div>
      </div>
    </div>
  )
}