/**
 * Installed Apps Table Header Components
 *
 * SortButton component for table column headers.
 */

import React from 'react'
import { Box } from '@mui/material'

export type SortField = 'appName' | 'appVersion' | 'appSource' | 'appCategory' | 'serverName' | 'status' | 'installedAt'
export type SortDirection = 'asc' | 'desc'

interface SortButtonProps {
  field: SortField
  currentField: SortField
  direction: SortDirection
  onSort: (field: SortField) => void
  children: React.ReactNode
}

export function SortButton({ field, currentField, direction, onSort, children }: SortButtonProps) {
  const isActive = currentField === field

  return (
    <Box
      component="button"
      type="button"
      onClick={(e) => {
        e.stopPropagation()
        onSort(field)
      }}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        fontSize: '0.75rem',
        fontWeight: 500,
        color: 'text.secondary',
        bgcolor: 'transparent',
        border: 'none',
        cursor: 'pointer',
        transition: 'color 0.2s',
        '&:hover': {
          color: 'text.primary'
        }
      }}
    >
      <span>{children}</span>
      <Box component="span" sx={{ fontSize: '0.75rem', ml: 0.5 }}>
        {isActive ? (direction === 'asc' ? '\u2191' : '\u2193') : ''}
      </Box>
    </Box>
  )
}
