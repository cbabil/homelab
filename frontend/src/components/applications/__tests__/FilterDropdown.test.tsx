/**
 * FilterDropdown Test Suite
 *
 * Tests for the FilterDropdown component with category and status filters.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Database, Globe } from 'lucide-react'
import { FilterDropdown } from '../FilterDropdown'
import { AppCategory, AppFilter } from '@/types/app'

describe('FilterDropdown', () => {
  const categories: AppCategory[] = [
    { id: 'database', name: 'Databases', description: 'Database applications', icon: Database, color: 'blue' },
    { id: 'web', name: 'Web Apps', description: 'Web applications', icon: Globe, color: 'green' }
  ]

  const defaultFilter: AppFilter = {
    search: ''
  }

  const defaultProps = {
    filter: defaultFilter,
    onFilterChange: vi.fn(),
    categories
  }

  describe('Rendering', () => {
    it('should render filter button', () => {
      render(<FilterDropdown {...defaultProps} />)

      expect(screen.getByText('Filters')).toBeInTheDocument()
    })

    it('should not show badge when no filters active', () => {
      render(<FilterDropdown {...defaultProps} />)

      expect(screen.queryByText('1')).not.toBeInTheDocument()
    })

    it('should show badge with count when filters active', () => {
      render(
        <FilterDropdown
          {...defaultProps}
          filter={{ search: '', category: 'database' }}
        />
      )

      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('should show badge with 2 when multiple filters active', () => {
      render(
        <FilterDropdown
          {...defaultProps}
          filter={{ search: '', category: 'database', status: 'installed' }}
        />
      )

      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  describe('Dropdown Behavior', () => {
    it('should open dropdown when button clicked', async () => {
      const user = userEvent.setup()
      render(<FilterDropdown {...defaultProps} />)

      await user.click(screen.getByText('Filters'))

      expect(screen.getByText('Filter Applications')).toBeInTheDocument()
    })

    it('should show categories in dropdown', async () => {
      const user = userEvent.setup()
      render(<FilterDropdown {...defaultProps} />)

      await user.click(screen.getByText('Filters'))

      expect(screen.getByText('Databases')).toBeInTheDocument()
      expect(screen.getByText('Web Apps')).toBeInTheDocument()
    })

    it('should show status options in dropdown', async () => {
      const user = userEvent.setup()
      render(<FilterDropdown {...defaultProps} />)

      await user.click(screen.getByText('Filters'))

      expect(screen.getByText('available')).toBeInTheDocument()
      expect(screen.getByText('installed')).toBeInTheDocument()
      expect(screen.getByText('error')).toBeInTheDocument()
    })

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup()
      render(
        <div>
          <FilterDropdown {...defaultProps} />
          <div data-testid="outside">Outside</div>
        </div>
      )

      await user.click(screen.getByText('Filters'))
      expect(screen.getByText('Filter Applications')).toBeInTheDocument()

      await user.click(screen.getByTestId('outside'))
      expect(screen.queryByText('Filter Applications')).not.toBeInTheDocument()
    })
  })

  describe('Filter Actions', () => {
    it('should call onFilterChange when category selected', async () => {
      const user = userEvent.setup()
      const onFilterChange = vi.fn()
      render(<FilterDropdown {...defaultProps} onFilterChange={onFilterChange} />)

      await user.click(screen.getByText('Filters'))
      await user.click(screen.getByText('Databases'))

      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'database' })
      )
    })

    it('should toggle category off when clicking same category', async () => {
      const user = userEvent.setup()
      const onFilterChange = vi.fn()
      render(
        <FilterDropdown
          {...defaultProps}
          filter={{ search: '', category: 'database' }}
          onFilterChange={onFilterChange}
        />
      )

      await user.click(screen.getByText('Filters'))
      await user.click(screen.getByText('Databases'))

      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ category: undefined })
      )
    })

    it('should call onFilterChange when status selected', async () => {
      const user = userEvent.setup()
      const onFilterChange = vi.fn()
      render(<FilterDropdown {...defaultProps} onFilterChange={onFilterChange} />)

      await user.click(screen.getByText('Filters'))
      await user.click(screen.getByText('installed'))

      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'installed' })
      )
    })

    it('should show clear all button when filters active', async () => {
      const user = userEvent.setup()
      render(
        <FilterDropdown
          {...defaultProps}
          filter={{ search: '', category: 'database' }}
        />
      )

      await user.click(screen.getByText('Filters'))

      expect(screen.getByText('Clear all')).toBeInTheDocument()
    })

    it('should clear all filters when clear all clicked', async () => {
      const user = userEvent.setup()
      const onFilterChange = vi.fn()
      render(
        <FilterDropdown
          {...defaultProps}
          filter={{ search: 'test', category: 'database', status: 'installed' }}
          onFilterChange={onFilterChange}
        />
      )

      await user.click(screen.getByText('Filters'))
      await user.click(screen.getByText('Clear all'))

      expect(onFilterChange).toHaveBeenCalledWith({ search: 'test' })
    })
  })
})
