/**
 * DataTable Component
 *
 * Reusable table component for consistent styling across all pages.
 * Handles sorting, empty states, and row rendering.
 */

import { ReactNode, useState, useMemo, ElementType } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, LucideIcon } from 'lucide-react'
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@mui/material'
import { SxProps, Theme } from '@mui/material/styles'

// Column definition
export interface ColumnDef<T> {
  id: string
  header: ReactNode
  width?: number | string
  align?: 'left' | 'center' | 'right'
  sx?: SxProps<Theme>
  sortable?: boolean
  render: (item: T, index: number) => ReactNode
  cellSx?: SxProps<Theme>
}

// Table props
interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T>[]
  keyExtractor: (item: T) => string
  onRowClick?: (item: T) => void
  emptyTitle?: string
  emptyMessage?: string
  emptyIcon?: LucideIcon | ElementType
  emptyIconSize?: number
  defaultSortField?: string
  defaultSortDirection?: 'asc' | 'desc'
  sortFn?: (a: T, b: T, field: string, direction: 'asc' | 'desc') => number
}

// Sort button component
interface SortButtonProps {
  field: string
  currentField: string
  direction: 'asc' | 'desc'
  onSort: (field: string) => void
  children: ReactNode
}

function SortButton({ field, currentField, direction, onSort, children }: SortButtonProps) {
  const isActive = currentField === field
  return (
    <Button
      variant="text"
      size="small"
      onClick={() => onSort(field)}
      sx={{ minWidth: 'auto', p: 0, fontWeight: 500, fontSize: '0.75rem', color: 'text.secondary', textTransform: 'none', '&:hover': { color: 'text.primary', bgcolor: 'transparent' } }}
    >
      <span>{children}</span>
      <span style={{ fontSize: '0.75rem', marginLeft: 4 }}>{isActive ? (direction === 'asc' ? '↑' : '↓') : '↓'}</span>
    </Button>
  )
}

// Empty state component
interface EmptyStateProps {
  colSpan: number
  icon: LucideIcon | ElementType
  iconSize: number
  title: string
  message: string
}

function EmptyState({ colSpan, icon: Icon, iconSize, title, message }: EmptyStateProps) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan} sx={{ border: 0, height: 'calc(100vh - 300px)', verticalAlign: 'middle' }}>
        <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Box sx={{ mb: 2, color: 'text.secondary' }}><Icon size={iconSize} style={{ opacity: 0.5 }} /></Box>
          <Typography variant="h6" sx={{ mb: 1 }}>{title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 'md', mx: 'auto' }}>{message}</Typography>
        </Box>
      </TableCell>
    </TableRow>
  )
}

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  emptyTitle,
  emptyMessage,
  emptyIcon: EmptyIcon = Search,
  emptyIconSize = 64,
  defaultSortField,
  defaultSortDirection = 'desc',
  sortFn
}: DataTableProps<T>) {
  const { t } = useTranslation()
  const [sortField, setSortField] = useState(defaultSortField || '')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(defaultSortDirection)

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const sortedData = useMemo(() => {
    if (!sortField || !sortFn) return data
    return [...data].sort((a, b) => sortFn(a, b, sortField, sortDirection))
  }, [data, sortField, sortDirection, sortFn])

  return (
    <TableContainer
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 0,
        bgcolor: 'transparent',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ overflow: 'hidden', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Table sx={{ width: '100%', tableLayout: 'fixed' }} stickyHeader>
          <TableHead>
            <TableRow sx={{ bgcolor: 'background.paper' }}>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  sx={{
                    bgcolor: 'inherit',
                    width: column.width,
                    px: 1,
                    '&:first-of-type': { pl: 2 },
                    '&:last-of-type': { pr: 2 },
                    ...column.sx
                  }}
                >
                  {column.sortable ? (
                    <SortButton
                      field={column.id}
                      currentField={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                    >
                      {column.header}
                    </SortButton>
                  ) : (
                    <Typography
                      component="span"
                      sx={{
                        fontWeight: 500,
                        fontSize: '0.75rem',
                        color: 'text.secondary'
                      }}
                    >
                      {column.header}
                    </Typography>
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedData.length === 0 ? (
              <EmptyState
                colSpan={columns.length}
                icon={EmptyIcon}
                iconSize={emptyIconSize}
                title={emptyTitle || t('common.noData')}
                message={emptyMessage || t('common.noDataMessage')}
              />
            ) : (
              sortedData.map((item, index) => (
                <TableRow
                  key={keyExtractor(item)}
                  hover
                  onClick={() => onRowClick?.(item)}
                  sx={{
                    height: 32,
                    maxHeight: 32,
                    cursor: onRowClick ? 'pointer' : 'default',
                    bgcolor: index % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)',
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.05)'
                    },
                    '& td': { py: 0, height: 32, maxHeight: 32 }
                  }}
                >
                  {columns.map((column) => (
                    <TableCell
                      key={column.id}
                      align={column.align}
                      sx={{
                        px: 1,
                        '&:first-of-type': { pl: 2 },
                        '&:last-of-type': { pr: 2 },
                        ...column.cellSx
                      }}
                    >
                      {column.render(item, index)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Box>
    </TableContainer>
  )
}
