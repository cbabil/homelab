/**
 * Application Layout Component
 *
 * Main layout wrapper that provides navigation and header.
 * Implements the overall UI structure for the application.
 */

import { ReactNode } from 'react'
import { Box, Stack } from '@mui/material'
import { Navigation } from './Navigation'
import { Header } from './Header'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <Stack sx={{ height: '100vh', bgcolor: 'background.default' }}>
      {/* Skip to main content link for keyboard users */}
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: -9999,
          top: 'auto',
          width: 1,
          height: 1,
          overflow: 'hidden',
          '&:focus': {
            position: 'absolute',
            top: 16,
            left: 16,
            zIndex: 60,
            px: 2,
            py: 1,
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            borderRadius: 2,
            fontWeight: 500,
            outline: 'none',
            boxShadow: (theme) => `0 0 0 2px ${theme.palette.primary.main}`,
            width: 'auto',
            height: 'auto',
            overflow: 'visible'
          }
        }}
      >
        Skip to main content
      </Box>

      <Header />

      <Stack direction="row" sx={{ flex: 1, minHeight: 0 }}>
        <Navigation />

        <Box
          component="main"
          id="main-content"
          tabIndex={-1}
          sx={{
            flex: 1,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Box
            sx={{
              p: 3,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0
            }}
          >
            {children}
          </Box>
        </Box>
      </Stack>
    </Stack>
  )
}