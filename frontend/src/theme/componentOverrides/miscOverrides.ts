/**
 * MUI Miscellaneous Component Overrides
 *
 * Checkbox, Link, Chip, Alert, Tooltip, ListItemButton, Snackbar,
 * Skeleton, Tabs, Table, Switch, CssBaseline
 */

import type { Components, Theme } from '@mui/material/styles'

type ThemeMode = 'light' | 'dark'

export const getMiscOverrides = (mode: ThemeMode): Components<Theme> => ({
  // Checkbox - Outline style with purple checkmark
  MuiCheckbox: {
    styleOverrides: {
      root: {
        color: 'hsl(250 76% 72%)',
        '&.Mui-checked': {
          color: 'hsl(250 76% 72%)',
        },
        '&:hover': {
          backgroundColor: 'transparent',
        },
      },
    },
    defaultProps: {
      disableRipple: true,
    },
  },

  // Link - Purple with hover brighten, no underline
  MuiLink: {
    styleOverrides: {
      root: {
        color: 'hsl(250 76% 72%)',
        textDecoration: 'none',
        cursor: 'pointer',
        transition: 'color 0.15s ease',
        '&:hover': {
          color: 'hsl(250 85% 80%)',
          textDecoration: 'none',
        },
      },
    },
  },

  // Chip
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 8,
      },
    },
  },

  // Alert
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 10,
        transition: 'none',
      },
    },
  },

  // Tooltip
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        borderRadius: 8,
        fontSize: '0.8125rem',
      },
    },
  },

  // ListItemButton - Selected state uses primary color
  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        '&.Mui-selected': {
          backgroundColor: 'rgba(139, 124, 246, 0.12)',
          '&:hover': {
            backgroundColor: 'rgba(139, 124, 246, 0.16)',
          },
        },
      },
    },
  },

  // Snackbar (Toast)
  MuiSnackbar: {
    styleOverrides: {
      root: {
        '& .MuiPaper-root': {
          borderRadius: 10,
        },
      },
    },
  },

  // Skeleton
  MuiSkeleton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
      },
      rounded: {
        borderRadius: 12,
      },
    },
  },

  // Tabs
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 500,
        minHeight: 48,
      },
    },
  },

  // Table
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderBottom:
          mode === 'dark'
            ? '1px solid rgba(255, 255, 255, 0.08)'
            : '1px solid rgba(0, 0, 0, 0.08)',
      },
    },
  },

  // Switch
  MuiSwitch: {
    styleOverrides: {
      root: {
        padding: 8,
      },
      track: {
        borderRadius: 10,
      },
      thumb: {
        boxShadow: '0 2px 4px 0 rgba(0, 0, 0, 0.2)',
      },
    },
  },

  // CssBaseline - Global styles
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        scrollbarWidth: 'thin',
        '&::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor:
            mode === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'transparent',
        },
      },
    },
  },
})
