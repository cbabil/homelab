/**
 * Applications Search and Filter Component
 * 
 * Search input and filter controls for the Applications page.
 */

import { Search } from 'lucide-react'
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
  return (
    <div className="flex items-center space-x-2">
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-muted-foreground h-3.5 w-3.5" />
        <input
          type="text"
          placeholder="Search applications..."
          className="w-full pl-8 pr-3 py-1.5 border border-input rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-primary/20 text-sm"
          onChange={(e) => onSearch(e.target.value)}
        />
      </div>
      
      <FilterDropdown 
        filter={filter} 
        onFilterChange={onFilterChange} 
        categories={categories}
      />
    </div>
  )
}
