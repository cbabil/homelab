/**
 * MUI Button Component Overrides
 *
 * Primary button uses OUTLINE style (matches logo aesthetic)
 */

import type { Components, Theme } from '@mui/material/styles'

type ThemeMode = 'light' | 'dark'

export const getButtonOverrides = (mode: ThemeMode): Components<Theme> => ({
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        padding: '10px 24px',
        fontSize: '0.9375rem',
        fontWeight: 500,
        boxShadow: 'none',
        transition: 'none',
        '&:hover': {
          boxShadow: 'none',
        },
        '&:focus': {
          outline: 'none',
          boxShadow: 'none',
        },
        '&:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
        '&.Mui-disabled': {
          transition: 'none',
        },
      },
      // Primary button = Outline style (purple border, transparent bg)
      containedPrimary: {
        backgroundColor: 'transparent',
        border: '2px solid hsl(250 76% 72%)',
        color: 'hsl(250 76% 72%)',
        '&:hover': {
          backgroundColor: 'transparent',
          border: '2px solid hsl(250 76% 72%)',
          color: 'hsl(250 85% 80%)',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
        '&:disabled': {
          opacity: 0.5,
          border: '2px solid hsl(250 76% 72%)',
          color: 'hsl(250 76% 72%)',
        },
      },
      // Outlined variant
      outlined: {
        borderWidth: 2,
        '&:hover': {
          borderWidth: 2,
          backgroundColor: 'transparent',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
      },
      outlinedPrimary: {
        borderColor: 'hsl(250 76% 72%)',
        color: 'hsl(250 76% 72%)',
        '&:hover': {
          borderColor: 'hsl(250 76% 72%)',
          color: 'hsl(250 85% 80%)',
          backgroundColor: 'transparent',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
      },
      // Outlined inherit - muted purple border
      outlinedInherit: {
        borderColor: 'hsl(250 45% 58%)',
        color: 'hsl(250 45% 58%)',
        '&:hover': {
          borderColor: 'hsl(250 60% 68%)',
          color: 'hsl(250 60% 68%)',
          backgroundColor: 'transparent',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
      },
      // Text button
      text: {
        '&:hover': {
          backgroundColor:
            mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
      },
      // Sizes
      sizeSmall: {
        padding: '6px 16px',
        fontSize: '0.8125rem',
      },
      sizeLarge: {
        padding: '12px 32px',
        fontSize: '1rem',
      },
    },
    defaultProps: {
      disableElevation: true,
    },
  },

  // IconButton - Purple with no background on hover
  MuiIconButton: {
    styleOverrides: {
      root: {
        borderRadius: 10,
        color: 'hsl(250 76% 72%)',
        '&:hover': {
          backgroundColor: 'transparent',
          color: 'hsl(250 85% 80%)',
        },
        '&:focus, &:focus-visible': {
          outline: 'none',
          boxShadow: 'none',
        },
      },
      colorPrimary: {
        color: 'hsl(250 76% 72%)',
        '&:hover': {
          backgroundColor: 'transparent',
          color: 'hsl(250 85% 80%)',
        },
      },
    },
  },
})
