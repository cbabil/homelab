/**
 * MUI Theme Configuration
 *
 * Single source of truth for all styling in the application.
 * This replaces Tailwind CSS - all colors, spacing, and components are defined here.
 */

import { createTheme } from '@mui/material/styles'
import { lightPalette, darkPalette } from './palette'
import { typography, spacing, shape } from './typography'
import { getComponentOverrides } from './componentOverrides'

// ============================================================================
// Create Themes
// ============================================================================

export const lightTheme = createTheme({
  palette: lightPalette,
  typography,
  spacing,
  shape,
  components: getComponentOverrides('light'),
})

export const darkTheme = createTheme({
  palette: darkPalette,
  typography,
  spacing,
  shape,
  components: getComponentOverrides('dark'),
})

// Export type for theme
export type AppTheme = typeof lightTheme
