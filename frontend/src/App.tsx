/**
 * Main Application Component
 * 
 * Root component that sets up routing and main application layout.
 * Provides the foundation for the Homelab Assistant UI.
 */

import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute, PublicRoute } from '@/components/auth/ProtectedRoute'
import { LoginPage, RegistrationPage, TermsOfServicePage, PrivacyPolicyPage } from '@/pages/login'
import { Dashboard } from '@/pages/dashboard'
import { ServersPage } from '@/pages/servers'
import { ApplicationsPage } from '@/pages/applications'
import { MarketplacePage } from '@/pages/marketplace'
import { SettingsPage } from '@/pages/settings'
import { LogsPage } from '@/pages/logs/LogsPage'

export function App() {
  return (
    <Routes>
      {/* Public routes - accessible without authentication */}
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <LoginPage />
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
                <Route path="/logs" element={<LogsPage />} />
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
