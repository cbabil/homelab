/**
 * Shared Settings Components
 * 
 * Common UI components used across settings tabs.
 */

import React from 'react'
import { Box, Stack, Typography } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'

// Re-export specialized components
export { SortableHeader } from './components/SortableHeader'
export { SessionTable } from './components/SessionTable'
export { SessionTableHeader } from './components/SessionTableHeader'
export { SessionRow } from './components/SessionRow'

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  /** Accessible label for the toggle - required for screen readers */
  'aria-label'?: string
  /** ID of element that labels this toggle */
  'aria-labelledby'?: string
  id?: string
}

export function Toggle({
  checked,
  onChange,
  disabled = false,
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledBy,
  id
}: ToggleProps) {
  const buttonSx: SxProps<Theme> = {
    position: 'relative',
    display: 'inline-flex',
    height: 16,
    width: 32,
    flexShrink: 0,
    borderRadius: '9999px',
    border: 2,
    borderColor: 'transparent',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    bgcolor: checked ? 'primary.main' : 'grey.300',
    '&:focus-visible': {
      outline: 'none',
      boxShadow: (theme) => `0 0 0 2px ${theme.palette.primary.main}`
    }
  }

  const thumbSx: SxProps<Theme> = {
    pointerEvents: 'none',
    display: 'inline-block',
    height: 12,
    width: 12,
    transform: checked ? 'translateX(16px)' : 'translateX(0)',
    borderRadius: '50%',
    bgcolor: 'common.white',
    boxShadow: 1,
    transition: 'transform 200ms ease-in-out'
  }

  return (
    <Box
      id={id}
      component="button"
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledBy}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      sx={buttonSx}
    >
      <Box
        aria-hidden="true"
        sx={thumbSx}
      />
    </Box>
  )
}

interface SettingRowProps {
  label: string
  description?: string
  children: React.ReactNode
  /** Optional ID for the setting row label - useful for aria-labelledby */
  labelId?: string
}

const settingRowStyles: Record<string, SxProps<Theme>> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    py: 1,
    gap: 2
  },
  labelContainer: {
    flexShrink: 0
  },
  label: {
    fontSize: '0.875rem',
    fontWeight: 500
  },
  description: {
    fontSize: '0.75rem',
    color: 'text.secondary',
    mt: 0.25
  },
  childrenContainer: {
    flex: 1,
    display: 'flex',
    justifyContent: 'flex-end',
    minWidth: 0
  }
}

export function SettingRow({ label, description, children, labelId }: SettingRowProps) {
  // Generate stable ID from label if not provided
  const id = labelId || `setting-${label.toLowerCase().replace(/\s+/g, '-')}`

  return (
    <Stack direction="row" sx={settingRowStyles.container}>
      <Box sx={settingRowStyles.labelContainer}>
        <Typography id={id} sx={settingRowStyles.label}>{label}</Typography>
        {description && (
          <Typography id={`${id}-desc`} sx={settingRowStyles.description}>{description}</Typography>
        )}
      </Box>
      <Box sx={settingRowStyles.childrenContainer}>
        {children}
      </Box>
    </Stack>
  )
}