/**
 * Main Application Component
 * 
 * Root component that sets up routing and main application layout.
 * Provides the foundation for the Tomo UI.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute, PublicRoute } from '@/components/auth/ProtectedRoute'
import { LoginPageWrapper, RegistrationPage, TermsOfServicePage, PrivacyPolicyPage, ForgotPasswordPage } from '@/pages/login'
import { SetupPage } from '@/pages/setup'
import { Dashboard } from '@/pages/dashboard'
import { ServersPage } from '@/pages/servers'
import { ApplicationsPage } from '@/pages/applications'
import { MarketplacePage } from '@/pages/marketplace'
import { SettingsPage } from '@/pages/settings'
import { ProfilePage } from '@/pages/profile'
import { AuditLogsPage } from '@/pages/logs/AuditLogsPage'
import { AccessLogsPage } from '@/pages/logs/AccessLogsPage'

export function App() {
  return (
    <Routes>
      {/* Public routes - accessible without authentication */}
      <Route
        path="/setup"
        element={<SetupPage />}
      />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPageWrapper />
          </PublicRoute>
        }
      />
      <Route 
        path="/register" 
        element={
          <PublicRoute>
            <RegistrationPage />
          </PublicRoute>
        } 
      />
      <Route 
        path="/terms-of-service" 
        element={<TermsOfServicePage />}
      />
      <Route
        path="/privacy-policy"
        element={<PrivacyPolicyPage />}
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <ForgotPasswordPage />
          </PublicRoute>
        }
      />

      {/* Protected routes - require authentication */}
      <Route 
        path="/*" 
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/servers" element={<ServersPage />} />
                <Route path="/applications" element={<ApplicationsPage />} />
                <Route path="/marketplace" element={<MarketplacePage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/logs" element={<Navigate to="/logs/access" replace />} />
                <Route path="/logs/access" element={<AccessLogsPage />} />
                <Route path="/logs/audit" element={<AuditLogsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/help" element={<Dashboard />} />
                <Route path="*" element={<Dashboard />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } 
      />
    </Routes>
  )
}
