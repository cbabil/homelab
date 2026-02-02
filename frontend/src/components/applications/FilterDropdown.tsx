/**
 * Filter Dropdown Component
 *
 * Dropdown interface for filtering applications by category, status, and other criteria.
 */

import React, { useState, useRef, useEffect } from 'react'
import { Filter, Check, X } from 'lucide-react'
import { Box, Typography, Stack, Chip } from '@mui/material'
import { Button } from '@/components/ui/Button'
import { AppCategory, AppFilter, AppStatus } from '@/types/app'

interface FilterDropdownProps {
  filter: AppFilter
  onFilterChange: (filter: AppFilter) => void
  categories: AppCategory[]
}

const STATUSES: AppStatus[] = ['available', 'installed', 'installing', 'updating', 'error']

const filterButtonStyle = {
  width: '100%',
  justifyContent: 'space-between',
  height: 'auto',
  px: 1,
  py: 0.5,
  fontSize: '0.75rem',
  fontWeight: 400
}

interface FilterSectionProps {
  title: string
  children: React.ReactNode
  hasBottomMargin?: boolean
}

function FilterSection({ title, children, hasBottomMargin = false }: FilterSectionProps) {
  return (
    <Box sx={{ mb: hasBottomMargin ? 2 : 0 }}>
      <Typography variant="caption" fontWeight={500} color="text.secondary" sx={{ mb: 1, display: 'block' }}>
        {title}
      </Typography>
      <Stack spacing={0.5}>{children}</Stack>
    </Box>
  )
}

interface FilterOptionButtonProps {
  label: string
  isSelected: boolean
  onClick: () => void
  capitalize?: boolean
}

function FilterOptionButton({ label, isSelected, onClick, capitalize = false }: FilterOptionButtonProps) {
  return (
    <Button
      onClick={onClick}
      variant="ghost"
      size="sm"
      sx={{
        ...filterButtonStyle,
        textTransform: capitalize ? 'capitalize' : undefined
      }}
    >
      <span>{label}</span>
      {isSelected && <Check className="h-3 w-3" />}
    </Button>
  )
}

interface FilterDropdownContentProps {
  filter: AppFilter
  categories: AppCategory[]
  hasActiveFilters: boolean
  onCategoryChange: (categoryId: string) => void
  onStatusChange: (status: AppStatus) => void
  onClearAll: () => void
}

function FilterDropdownContent({
  filter,
  categories,
  hasActiveFilters,
  onCategoryChange,
  onStatusChange,
  onClearAll
}: FilterDropdownContentProps) {
  return (
    <Box sx={{
      position: 'absolute',
      right: 0,
      top: '100%',
      mt: 0.5,
      width: 288,
      bgcolor: 'background.paper',
      border: 1,
      borderColor: 'divider',
      borderRadius: 1,
      boxShadow: 3,
      zIndex: 50,
      p: 2
    }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
        <Typography variant="body2" fontWeight={500}>Filter Applications</Typography>
        {hasActiveFilters && (
          <Button
            onClick={onClearAll}
            variant="ghost"
            size="sm"
            sx={{
              height: 'auto',
              p: 0,
              fontSize: '0.75rem',
              color: 'text.secondary',
              '&:hover': { color: 'text.primary', bgcolor: 'transparent' }
            }}
          >
            <X className="h-3 w-3" />
            <span>Clear all</span>
          </Button>
        )}
      </Stack>

      <FilterSection title="CATEGORY" hasBottomMargin>
        {categories.map(category => (
          <FilterOptionButton
            key={category.id}
            label={category.name}
            isSelected={filter.category === category.id}
            onClick={() => onCategoryChange(category.id)}
          />
        ))}
      </FilterSection>

      <FilterSection title="STATUS">
        {STATUSES.map(status => (
          <FilterOptionButton
            key={status}
            label={status}
            isSelected={filter.status === status}
            onClick={() => onStatusChange(status)}
            capitalize
          />
        ))}
      </FilterSection>
    </Box>
  )
}

export function FilterDropdown({ filter, onFilterChange, categories }: FilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

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
  const activeFilterCount = [filter.category, filter.status, filter.featured].filter(Boolean).length

  return (
    <Box sx={{ position: 'relative' }} ref={dropdownRef}>
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        size="sm"
        sx={{
          flexShrink: 0,
          borderColor: hasActiveFilters ? 'primary.main' : undefined,
          bgcolor: hasActiveFilters ? 'primary.light' : undefined
        }}
      >
        <Filter className="h-3.5 w-3.5" />
        <Typography variant="caption">Filters</Typography>
        {hasActiveFilters && (
          <Chip
            label={activeFilterCount}
            size="small"
            sx={{
              height: 18,
              fontSize: '0.75rem',
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              '& .MuiChip-label': { px: 0.75, py: 0 }
            }}
          />
        )}
      </Button>

      {isOpen && (
        <FilterDropdownContent
          filter={filter}
          categories={categories}
          hasActiveFilters={hasActiveFilters}
          onCategoryChange={handleCategoryChange}
          onStatusChange={handleStatusChange}
          onClearAll={clearAllFilters}
        />
      )}
    </Box>
  )
}
