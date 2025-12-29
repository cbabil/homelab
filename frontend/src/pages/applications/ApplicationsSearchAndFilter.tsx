/**
 * Applications Search and Filter Component
 *
 * Search input and filter controls for the Applications page.
 */

import { useState } from 'react'
import { Search } from 'ui-toolkit'
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
    <div className="flex items-center space-x-2">
      <Search
        value={searchValue}
        onChange={handleSearchChange}
        placeholder="Search applications..."
        className="flex-1 max-w-xs"
      />

      <FilterDropdown
        filter={filter}
        onFilterChange={onFilterChange}
        categories={categories}
      />
    </div>
  )
}
