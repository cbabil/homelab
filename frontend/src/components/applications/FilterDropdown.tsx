/**
 * Filter Dropdown Component
 * 
 * Dropdown interface for filtering applications by category, status, and other criteria.
 */

import { useState, useRef, useEffect } from 'react'
import { Filter, Check, X } from 'lucide-react'
import { AppCategory, AppFilter, AppStatus } from '@/types/app'

interface FilterDropdownProps {
  filter: AppFilter
  onFilterChange: (filter: AppFilter) => void
  categories: AppCategory[]
}

export function FilterDropdown({ filter, onFilterChange, categories }: FilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const statuses: AppStatus[] = ['available', 'installed', 'installing', 'updating', 'error']

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleCategoryChange = (categoryId: string) => {
    const newCategory = categoryId === filter.category ? undefined : categoryId
    onFilterChange({ ...filter, category: newCategory })
  }

  const handleStatusChange = (status: AppStatus) => {
    const newStatus = status === filter.status ? undefined : status
    onFilterChange({ ...filter, status: newStatus })
  }

  const clearAllFilters = () => {
    onFilterChange({ search: filter.search })
  }

  const hasActiveFilters = !!(filter.category || filter.status || filter.featured)

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-1.5 px-2.5 py-1.5 border rounded-md hover:bg-accent transition-colors shrink-0 ${
          hasActiveFilters ? 'border-primary bg-primary/10' : 'border-input'
        }`}
      >
        <Filter className="h-3.5 w-3.5" />
        <span className="text-xs">Filters</span>
        {hasActiveFilters && (
          <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full">
            {[filter.category, filter.status, filter.featured].filter(Boolean).length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-background border rounded-lg shadow-lg z-50 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm">Filter Applications</h3>
            {hasActiveFilters && (
              <button 
                onClick={clearAllFilters}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center space-x-1"
              >
                <X className="h-3 w-3" />
                <span>Clear all</span>
              </button>
            )}
          </div>

          {/* Categories */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-muted-foreground mb-2">CATEGORY</h4>
            <div className="space-y-1">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryChange(category.id)}
                  className="w-full flex items-center justify-between px-2 py-1 rounded hover:bg-accent text-xs"
                >
                  <span>{category.name}</span>
                  {filter.category === category.id && <Check className="h-3 w-3" />}
                </button>
              ))}
            </div>
          </div>

          {/* Status */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">STATUS</h4>
            <div className="space-y-1">
              {statuses.map(status => (
                <button
                  key={status}
                  onClick={() => handleStatusChange(status)}
                  className="w-full flex items-center justify-between px-2 py-1 rounded hover:bg-accent text-xs capitalize"
                >
                  <span>{status}</span>
                  {filter.status === status && <Check className="h-3 w-3" />}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
