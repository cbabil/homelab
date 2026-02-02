/**
 * MUI Input Component Overrides
 *
 * TextField, OutlinedInput, InputBase, InputLabel, InputAdornment, FormHelperText
 * All transitions disabled for consistent behavior.
 */

import type { Components, Theme } from '@mui/material/styles'

export const getInputOverrides = (): Components<Theme> => ({
  // TextField - disable ALL transitions
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 10,
          transition: 'none',
        },
        '& .MuiInputLabel-root': {
          transition: 'none',
        },
        '& .MuiOutlinedInput-notchedOutline': {
          transition: 'none',
        },
        '& .MuiFormHelperText-root': {
          transition: 'none',
        },
      },
    },
    defaultProps: {
      variant: 'outlined',
      size: 'small',
    },
  },

  // OutlinedInput - disable transitions
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        transition: 'none',
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          transition: 'none',
        },
        '&.Mui-disabled': {
          transition: 'none',
        },
      },
      notchedOutline: {
        transition: 'none',
      },
      input: {
        transition: 'none',
      },
    },
  },

  // InputBase - disable transitions
  MuiInputBase: {
    styleOverrides: {
      root: {
        transition: 'none',
      },
      input: {
        transition: 'none',
      },
    },
  },

  // InputLabel - disable transitions
  MuiInputLabel: {
    styleOverrides: {
      root: {
        transition: 'none',
      },
    },
  },

  // InputAdornment - disable transitions
  MuiInputAdornment: {
    styleOverrides: {
      root: {
        transition: 'none',
        '& .MuiSvgIcon-root': {
          transition: 'none',
        },
      },
    },
  },

  // FormHelperText - disable transitions
  MuiFormHelperText: {
    styleOverrides: {
      root: {
        transition: 'none',
      },
    },
  },
})
