/**
 * Search Input Component
 *
 * Reusable search input with consistent styling across the app.
 */

import { Search } from 'lucide-react'
import { Box, InputBase } from '@mui/material'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  width?: number
}

export function SearchInput({ value, onChange, placeholder = 'Search...', width = 220 }: SearchInputProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: 'transparent',
        px: 1.5,
        '&:focus-within': { borderColor: 'primary.main' }
      }}
    >
      <Search style={{ width: 12, height: 12, color: 'gray', flexShrink: 0 }} />
      <InputBase
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        sx={{
          width,
          ml: 1,
          py: 0.25,
          fontSize: '0.75rem'
        }}
      />
    </Box>
  )
}
