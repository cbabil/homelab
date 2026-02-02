/**
 * MUI Theme Palette Definitions
 *
 * Color palettes for light and dark themes.
 * Tomo brand color: Purple (#8B7CF6)
 */

/**
 * Tomo Purple - derived from logo (#8B7CF6)
 *
 * Primary brand color used for:
 * - Primary buttons (outline style)
 * - Links and interactive elements
 * - Selected/active states
 * - Icons
 */
export const tomoPurple = {
  main: 'hsl(250 76% 72%)', // #8B7CF6 - primary brand color
  light: 'hsl(250 85% 80%)', // Hover/bright state
  dark: 'hsl(250 76% 62%)', // Darker variant for pressed states
  contrastText: '#ffffff',
}

/**
 * Light theme color palette
 *
 * Background: Pure white (#ffffff)
 * Text: Slate gray scale (#0f172a primary, #64748b secondary)
 * Accent colors use muted, non-fluorescent tones
 */
export const lightPalette = {
  mode: 'light' as const,
  primary: tomoPurple,
  secondary: {
    main: '#64748b',
    light: '#94a3b8',
    dark: '#475569',
    contrastText: '#ffffff',
  },
  background: {
    default: '#ffffff',
    paper: '#ffffff',
  },
  text: {
    primary: '#0f172a',
    secondary: '#64748b',
    disabled: '#94a3b8',
  },
  divider: 'rgba(0, 0, 0, 0.08)',
  error: {
    main: '#c53030', // Muted brick red
    light: '#e57373', // Soft coral for backgrounds
    dark: '#9b2c2c', // Deep red for hover/pressed states
    contrastText: '#ffffff',
  },
  warning: {
    main: '#f59e0b',
    light: '#fcd34d',
    dark: '#d97706',
    contrastText: '#000000',
  },
  success: {
    main: '#22c55e',
    light: '#86efac',
    dark: '#16a34a',
    contrastText: '#ffffff',
  },
  info: {
    main: '#3b82f6',
    light: '#93c5fd',
    dark: '#2563eb',
    contrastText: '#ffffff',
  },
  action: {
    hover: 'rgba(0, 0, 0, 0.04)',
    selected: 'rgba(139, 124, 246, 0.08)',
    disabled: 'rgba(0, 0, 0, 0.26)',
    disabledBackground: 'rgba(0, 0, 0, 0.12)',
  },
  grey: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
}

/**
 * Dark theme color palette
 *
 * Background: Slate 900/800 (#0f172a, #1e293b)
 * Text: Light slate (#f1f5f9 primary, #94a3b8 secondary)
 * Accent colors adjusted for dark backgrounds
 */
export const darkPalette = {
  mode: 'dark' as const,
  primary: tomoPurple, // Same purple for brand consistency
  secondary: {
    main: '#94a3b8',
    light: '#cbd5e1',
    dark: '#64748b',
    contrastText: '#0f172a',
  },
  background: {
    default: '#0f172a', // Slate 900
    paper: '#1e293b', // Slate 800
  },
  text: {
    primary: '#f1f5f9',
    secondary: '#94a3b8',
    disabled: '#64748b',
  },
  divider: 'rgba(255, 255, 255, 0.08)',
  error: {
    main: '#e57373', // Muted coral red
    light: '#ef9a9a', // Light coral for subtle backgrounds
    dark: '#c53030', // Brick red for hover/pressed states
    contrastText: '#000000',
  },
  warning: {
    main: '#fbbf24',
    light: '#fcd34d',
    dark: '#f59e0b',
    contrastText: '#000000',
  },
  success: {
    main: '#4ade80',
    light: '#86efac',
    dark: '#22c55e',
    contrastText: '#000000',
  },
  info: {
    main: '#60a5fa',
    light: '#93c5fd',
    dark: '#3b82f6',
    contrastText: '#000000',
  },
  action: {
    hover: 'rgba(255, 255, 255, 0.08)',
    selected: 'rgba(139, 124, 246, 0.16)',
    disabled: 'rgba(255, 255, 255, 0.3)',
    disabledBackground: 'rgba(255, 255, 255, 0.12)',
  },
  grey: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
}
