/**
 * Table Pagination Component
 *
 * Consistent pagination for tables across all pages.
 * Shows "Page X of Y" with Previous/Next buttons.
 */

import { Box, Stack } from '@mui/material'
import { Button } from '@/components/ui/Button'

interface TablePaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function TablePagination({ currentPage, totalPages, onPageChange }: TablePaginationProps) {
  const displayTotalPages = Math.max(1, totalPages)

  return (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="space-between"
      sx={{
        flexShrink: 0,
        pt: 2,
        pb: 1,
        mt: 'auto'
      }}
    >
      <Box component="span" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
        Page{' '}
        <Box component="span" sx={{ fontWeight: 600, color: 'text.primary' }}>
          {currentPage}
        </Box>{' '}
        of {displayTotalPages}
      </Box>
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.min(displayTotalPages, currentPage + 1))}
          disabled={currentPage >= displayTotalPages}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
        >
          Next
        </Button>
      </Stack>
    </Stack>
  )
}
