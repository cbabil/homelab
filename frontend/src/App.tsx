/**
 * Main Application Component
 *
 * Root component that sets up routing and main application layout.
 * Provides the foundation for the Tomo UI.
 *
 * Route-level code splitting via React.lazy reduces initial bundle size.
 * Auth-related pages (login, register) are eagerly loaded since they're the entry point.
 */

import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute, PublicRoute } from '@/components/auth/ProtectedRoute';

// Auth pages loaded eagerly (entry point for unauthenticated users)
import {
  LoginPageWrapper,
  RegistrationPage,
  TermsOfServicePage,
  PrivacyPolicyPage,
  ForgotPasswordPage,
} from '@/pages/login';
import { SetupPage } from '@/pages/setup';

// Protected pages loaded lazily (only needed after authentication)
const Dashboard = lazy(() =>
  import('@/pages/dashboard/Dashboard').then((m) => ({ default: m.Dashboard }))
);
const ServersPage = lazy(() =>
  import('@/pages/servers/ServersPage').then((m) => ({ default: m.ServersPage }))
);
const ApplicationsPage = lazy(() =>
  import('@/pages/applications/ApplicationsPage').then((m) => ({ default: m.ApplicationsPage }))
);
const MarketplacePage = lazy(() =>
  import('@/pages/marketplace/MarketplacePage').then((m) => ({ default: m.MarketplacePage }))
);
const SettingsPage = lazy(() =>
  import('@/pages/settings/SettingsPage').then((m) => ({ default: m.SettingsPage }))
);
const ProfilePage = lazy(() =>
  import('@/pages/profile/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);
const AuditLogsPage = lazy(() =>
  import('@/pages/logs/AuditLogsPage').then((m) => ({ default: m.AuditLogsPage }))
);
const AccessLogsPage = lazy(() =>
  import('@/pages/logs/AccessLogsPage').then((m) => ({ default: m.AccessLogsPage }))
);

function PageLoader() {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%',
        minHeight: 200,
      }}
    >
      <CircularProgress size={32} />
    </Box>
  );
}

export function App() {
  return (
    <Routes>
      {/* Public routes - accessible without authentication */}
      <Route path="/setup" element={<SetupPage />} />
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
      <Route path="/terms-of-service" element={<TermsOfServicePage />} />
      <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
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
              <Suspense fallback={<PageLoader />}>
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
              </Suspense>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
