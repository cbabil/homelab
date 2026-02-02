/**
 * MUI Surface Component Overrides
 *
 * Card, Dialog, Paper, Menu, AppBar, Drawer
 */

import type { Components, Theme } from '@mui/material/styles'

type ThemeMode = 'light' | 'dark'

export const getSurfaceOverrides = (mode: ThemeMode): Components<Theme> => ({
  // Card
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 16,
        boxShadow:
          mode === 'dark'
            ? 'none'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        backgroundImage: 'none',
        transition: 'none',
        ...(mode === 'dark' && {
          backgroundColor: '#1e293b',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }),
      },
    },
  },

  // Dialog
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: 16,
        backgroundImage: 'none',
        boxShadow:
          mode === 'dark'
            ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
            : '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        ...(mode === 'dark' && {
          backgroundColor: '#1e293b',
        }),
      },
    },
  },

  // Paper
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
      },
      rounded: {
        borderRadius: 12,
      },
    },
  },

  // Menu
  MuiMenu: {
    styleOverrides: {
      paper: {
        borderRadius: 12,
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
      },
    },
  },

  // AppBar
  MuiAppBar: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
        boxShadow: 'none',
        borderBottom:
          mode === 'dark'
            ? '1px solid rgba(255, 255, 255, 0.08)'
            : '1px solid rgba(0, 0, 0, 0.08)',
      },
    },
  },

  // Drawer
  MuiDrawer: {
    styleOverrides: {
      paper: {
        backgroundImage: 'none',
        borderRight:
          mode === 'dark'
            ? '1px solid rgba(255, 255, 255, 0.08)'
            : '1px solid rgba(0, 0, 0, 0.08)',
      },
    },
  },
})
