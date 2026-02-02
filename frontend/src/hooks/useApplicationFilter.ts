/**
 * Application Filter Hook
 *
 * Manages application filter state with sanitization and comparison.
 */

import { useState, useCallback } from 'react'
import { AppFilter } from '@/types/app'

export function useApplicationFilter(initialFilter: AppFilter = {}) {
  const [currentFilter, setCurrentFilter] = useState<AppFilter>(initialFilter)

  const sanitizeFilter = useCallback((filter: AppFilter): AppFilter => {
    const sanitized: AppFilter = {}
    if (filter.category) sanitized.category = filter.category
    if (filter.status) sanitized.status = filter.status
    if (filter.search && filter.search.trim().length > 0) sanitized.search = filter.search.trim()
    if (filter.featured !== undefined) sanitized.featured = filter.featured
    if (filter.tags && filter.tags.length > 0) sanitized.tags = filter.tags
    if (filter.sortBy) sanitized.sortBy = filter.sortBy
    if (filter.sortOrder) sanitized.sortOrder = filter.sortOrder
    return sanitized
  }, [])

  const filtersEqual = useCallback((a: AppFilter, b: AppFilter) => {
    return JSON.stringify(a) === JSON.stringify(b)
  }, [])

  const setFilter = useCallback((nextFilter: AppFilter) => {
    setCurrentFilter(prev => {
      const sanitized = sanitizeFilter(nextFilter)
      return filtersEqual(prev, sanitized) ? prev : sanitized
    })
  }, [filtersEqual, sanitizeFilter])

  const updateFilter = useCallback((updates: Partial<AppFilter>) => {
    setCurrentFilter(prev => {
      const sanitized = sanitizeFilter({ ...prev, ...updates })
      return filtersEqual(prev, sanitized) ? prev : sanitized
    })
  }, [filtersEqual, sanitizeFilter])

  return {
    currentFilter,
    setFilter,
    updateFilter,
    sanitizeFilter
  }
}
