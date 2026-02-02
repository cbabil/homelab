/**
 * Main entry point for the Tomo frontend application.
 * Sets up React app with routing and global providers.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MCPProvider } from '@/providers/MCPProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { NotificationProvider } from '@/providers/NotificationProvider'
import { AuthProvider } from '@/providers/AuthProvider'
import { SettingsProvider } from '@/providers/SettingsProvider'
import { ToastProvider } from '@/components/ui/Toast'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { App } from '@/App'
import '@/styles/globals.css'

// Initialize i18n before app renders
import '@/i18n'

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Initialize MCP client - uses relative URL for reverse proxy setup
// Override with VITE_MCP_SERVER_URL for development without proxy
const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL || '/mcp'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <SettingsProvider>
              <ToastProvider>
                <MCPProvider serverUrl={mcpServerUrl} transportType="http">
                  <NotificationProvider>
                    <ErrorBoundary>
                      <App />
                    </ErrorBoundary>
                  </NotificationProvider>
                </MCPProvider>
              </ToastProvider>
            </SettingsProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)