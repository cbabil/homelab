/**
 * Sortable Header Component
 * 
 * Reusable sortable table header with visual indicators.
 */

import { ChevronUp, ChevronDown } from 'lucide-react'
import { Box, Stack, TableCell } from '@mui/material'
import type { SxProps, Theme } from '@mui/material'
import type { SortKey } from '../types'

const styles: Record<string, SxProps<Theme>> = {
  header: {
    px: 2,
    py: 1.5,
    textAlign: 'left',
    fontSize: '0.75rem',
    fontWeight: 500,
    color: 'text.secondary',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    cursor: 'pointer',
    userSelect: 'none',
    transition: 'color 0.2s',
    '&:hover': {
      color: 'text.primary'
    }
  },
  iconContainer: {
    display: 'flex',
    flexDirection: 'column'
  }
}

interface SortableHeaderProps {
  label: string
  sortKey: SortKey
  currentSort: SortKey
  sortOrder: 'asc' | 'desc'
  onSort: (key: SortKey) => void
}

export function SortableHeader({
  label,
  sortKey,
  currentSort,
  sortOrder,
  onSort
}: SortableHeaderProps) {
  const isActive = currentSort === sortKey

  return (
    <TableCell
      sx={styles.header}
      onClick={() => onSort(sortKey)}
    >
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <span>{label}</span>
        <Box sx={styles.iconContainer}>
          <ChevronUp
            style={{
              height: 12,
              width: 12,
              color: isActive && sortOrder === 'asc' ? 'var(--mui-palette-primary-main)' : 'rgba(0, 0, 0, 0.26)'
            }}
          />
          <ChevronDown
            style={{
              height: 12,
              width: 12,
              marginTop: -4,
              color: isActive && sortOrder === 'desc' ? 'var(--mui-palette-primary-main)' : 'rgba(0, 0, 0, 0.26)'
            }}
          />
        </Box>
      </Stack>
    </TableCell>
  )
}