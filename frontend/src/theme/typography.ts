/**
 * MUI Theme Typography Settings
 *
 * Font family and text style definitions.
 */

export const typography = {
  fontFamily: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  button: {
    textTransform: 'none' as const,
    fontWeight: 500,
  },
  h1: {
    fontWeight: 700,
    fontSize: '2.25rem',
    lineHeight: 1.2,
  },
  h2: {
    fontWeight: 700,
    fontSize: '1.875rem',
    lineHeight: 1.3,
  },
  h3: {
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.4,
  },
  h4: {
    fontWeight: 600,
    fontSize: '1.25rem',
    lineHeight: 1.4,
  },
  h5: {
    fontWeight: 600,
    fontSize: '1.125rem',
    lineHeight: 1.5,
  },
  h6: {
    fontWeight: 600,
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
  },
}

// Spacing (matches Tailwind's spacing scale)
export const spacing = 8 // Base unit: 8px (p-1 = 8px, p-2 = 16px, etc.)

// Shape
export const shape = {
  borderRadius: 12, // Default border radius (rounded-lg equivalent)
}
