/**
 * Server Search Bar Component
 *
 * Enhanced search input with modern styling and result counter.
 * Positioned prominently at the top of server cards section.
 */

import { Search } from 'lucide-react'
import { Box, InputBase } from '@mui/material'

interface ServerSearchBarProps {
  searchTerm: string
  onSearchChange: (term: string) => void
}

export function ServerSearchBar({
  searchTerm,
  onSearchChange
}: ServerSearchBarProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 6,
        p: 6,
        bgcolor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        borderRadius: 3,
        backdropFilter: 'blur(4px)',
        opacity: 0.3
      }}
    >
      <Box sx={{ position: 'relative', flex: 1, maxWidth: 800 }}>
        <Box
          sx={{
            position: 'absolute',
            left: 16,
            top: '50%',
            transform: 'translateY(-50%)',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <Search className="h-5 w-5 text-muted-foreground" />
        </Box>
        <InputBase
          type="text"
          placeholder="Search servers by name, host, or username..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          sx={{
            width: '100%',
            pl: 12,
            pr: 4,
            py: 3.5,
            fontSize: 18,
            border: 2,
            borderColor: 'divider',
            borderRadius: 3,
            bgcolor: 'background.default',
            opacity: 0.8,
            '&:focus-within': {
              outline: 'none',
              boxShadow: (theme) => `0 0 0 2px ${theme.palette.primary.main}30`,
              borderColor: 'primary.main'
            },
            transition: 'all 0.2s',
            boxShadow: 1,
            '&:hover': {
              boxShadow: 2
            },
            '& input::placeholder': {
              color: 'text.secondary',
              opacity: 0.7
            }
          }}
        />
      </Box>
    </Box>
  )
}