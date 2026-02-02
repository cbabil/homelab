/**
 * Error Boundary Component
 *
 * Catches JavaScript errors in child component tree and displays
 * a fallback UI instead of crashing the whole app.
 */

import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Box, Stack } from '@mui/material'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })

    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }

    // Call optional error handler
    this.props.onError?.(error, errorInfo)
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleGoHome = (): void => {
    window.location.href = '/'
  }

  renderErrorDetails(): ReactNode {
    if (!import.meta.env.DEV || !this.state.error) {
      return null
    }

    return (
      <Box
        sx={{
          bgcolor: 'action.hover',
          borderRadius: 2,
          p: 2,
          mb: 3,
          textAlign: 'left'
        }}
      >
        <Box
          component="p"
          sx={{
            fontSize: '0.875rem',
            fontFamily: 'monospace',
            color: 'error.main',
            wordBreak: 'break-all'
          }}
        >
          {this.state.error.message}
        </Box>
        {this.state.errorInfo?.componentStack && (
          <Box
            component="pre"
            sx={{
              fontSize: '0.75rem',
              color: 'text.secondary',
              mt: 1,
              overflow: 'auto',
              maxHeight: 128
            }}
          >
            {this.state.errorInfo.componentStack}
          </Box>
        )}
      </Box>
    )
  }

  renderActionButtons(): ReactNode {
    return (
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={1.5}
        sx={{ justifyContent: 'center' }}
      >
        <Box
          component="button"
          onClick={this.handleReload}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            px: 2,
            py: 1,
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            borderRadius: 2,
            border: 'none',
            cursor: 'pointer',
            '&:hover': { bgcolor: 'primary.dark' },
            transition: 'background-color 0.2s'
          }}
        >
          <RefreshCw style={{ width: 16, height: 16 }} />
          Refresh Page
        </Box>

        <Box
          component="button"
          onClick={this.handleGoHome}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            px: 2,
            py: 1,
            bgcolor: 'action.hover',
            color: 'text.secondary',
            borderRadius: 2,
            border: 'none',
            cursor: 'pointer',
            '&:hover': { bgcolor: 'action.selected' },
            transition: 'background-color 0.2s'
          }}
        >
          <Home style={{ width: 16, height: 16 }} />
          Go Home
        </Box>
      </Stack>
    )
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Box
          sx={{
            minHeight: '100vh',
            bgcolor: 'background.default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 2
          }}
        >
          <Box sx={{ maxWidth: 448, width: '100%', textAlign: 'center' }}>
            <Box
              sx={{
                bgcolor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderRadius: 4,
                p: 4,
                boxShadow: 3
              }}
            >
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: 'error.main',
                  opacity: 0.1,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 3
                }}
              >
                <AlertTriangle style={{ width: 32, height: 32, color: 'var(--mui-palette-error-main)' }} />
              </Box>

              <Box
                component="h1"
                sx={{ fontSize: '1.5rem', fontWeight: 700, color: 'text.primary', mb: 1 }}
              >
                Something went wrong
              </Box>

              <Box component="p" sx={{ color: 'text.secondary', mb: 3 }}>
                An unexpected error occurred. Please try refreshing the page or go back to the home page.
              </Box>

              {this.renderErrorDetails()}
              {this.renderActionButtons()}
            </Box>
          </Box>
        </Box>
      )
    }

    return this.props.children
  }
}
