/**
 * Test Utilities
 *
 * Provides test wrappers with all necessary providers for component testing.
 * Includes AuthProvider, NotificationProvider, MCPProvider, and router setup.
 */

import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/providers/AuthProvider'
import { NotificationProvider } from '@/providers/NotificationProvider'
import { MCPProvider } from '@/providers/MCPProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { ToastProvider } from '@/components/ui/Toast'

// All providers wrapper
function AllProvidersWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <MCPProvider serverUrl="http://localhost:8000">
            <NotificationProvider>
              <AuthProvider>
                {children}
              </AuthProvider>
            </NotificationProvider>
          </MCPProvider>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

// Auth and notification providers only (for components that don't need MCP)
function AuthProvidersWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <NotificationProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </NotificationProvider>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

// Custom render with all providers
function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProvidersWrapper, ...options })
}

// Custom render with auth providers only
function renderWithAuthProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AuthProvidersWrapper, ...options })
}

// Export utilities
export {
  renderWithProviders,
  renderWithAuthProviders,
  AllProvidersWrapper,
  AuthProvidersWrapper
}

// Re-export everything from testing-library
export * from '@testing-library/react'