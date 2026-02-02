/**
 * Applications Search and Filter Component
 *
 * Search input and filter controls for the Applications page.
 */

import { useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'
import { TextField, InputAdornment, Stack } from '@mui/material'
import { AppCategory, AppFilter } from '@/types/app'
import { FilterDropdown } from '@/components/applications/FilterDropdown'

interface ApplicationsSearchAndFilterProps {
  filter: AppFilter
  onFilterChange: (filter: AppFilter) => void
  onSearch: (value: string) => void
  categories: AppCategory[]
}

export function ApplicationsSearchAndFilter({
  filter,
  onFilterChange,
  onSearch,
  categories
}: ApplicationsSearchAndFilterProps) {
  const [searchValue, setSearchValue] = useState(filter.search || '')

  const handleSearchChange = (value: string) => {
    setSearchValue(value)
    onSearch(value)
  }

  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      <TextField
        size="small"
        value={searchValue}
        onChange={(e) => handleSearchChange(e.target.value)}
        placeholder="Search applications..."
        sx={{ flex: 1, maxWidth: 320 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon size={16} />
            </InputAdornment>
          ),
        }}
      />

      <FilterDropdown
        filter={filter}
        onFilterChange={onFilterChange}
        categories={categories}
      />
    </Stack>
  )
}
