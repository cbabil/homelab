/**
 * CategoryGrid Test Suite
 *
 * Tests for the CategoryGrid component with category filtering.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Database, Globe, Shield } from 'lucide-react'
import { CategoryGrid } from '../CategoryGrid'
import { AppCategory } from '@/types/app'

describe('CategoryGrid', () => {
  const categories: AppCategory[] = [
    { id: 'database', name: 'Databases', description: 'Database applications', icon: Database, color: 'blue' },
    { id: 'web', name: 'Web Apps', description: 'Web applications', icon: Globe, color: 'green' },
    { id: 'security', name: 'Security', description: 'Security applications', icon: Shield, color: 'red' }
  ]

  const defaultProps = {
    categories,
    selectedCategory: null,
    onCategorySelect: vi.fn(),
    appCounts: { database: 5, web: 10, security: 3 },
    totalApps: 18
  }

  describe('Rendering', () => {
    it('should render All Apps button', () => {
      render(<CategoryGrid {...defaultProps} />)

      expect(screen.getByText('All Apps')).toBeInTheDocument()
    })

    it('should render total apps count', () => {
      render(<CategoryGrid {...defaultProps} totalApps={25} />)

      expect(screen.getByText('25 available')).toBeInTheDocument()
    })

    it('should render all category buttons', () => {
      render(<CategoryGrid {...defaultProps} />)

      expect(screen.getByText('Databases')).toBeInTheDocument()
      expect(screen.getByText('Web Apps')).toBeInTheDocument()
      expect(screen.getByText('Security')).toBeInTheDocument()
    })

    it('should render category app counts', () => {
      render(<CategoryGrid {...defaultProps} />)

      expect(screen.getByText('5 apps')).toBeInTheDocument()
      expect(screen.getByText('10 apps')).toBeInTheDocument()
      expect(screen.getByText('3 apps')).toBeInTheDocument()
    })

    it('should show 0 apps for categories with no count', () => {
      render(
        <CategoryGrid
          {...defaultProps}
          appCounts={{}}
        />
      )

      // All categories should show 0 apps
      expect(screen.getAllByText('0 apps')).toHaveLength(3)
    })
  })

  describe('Selection', () => {
    it('should highlight All Apps when no category selected', () => {
      render(<CategoryGrid {...defaultProps} selectedCategory={null} />)

      // All Apps button should have selected styling
      const allAppsButton = screen.getByText('All Apps').closest('button')
      expect(allAppsButton).toBeInTheDocument()
    })

    it('should highlight selected category', () => {
      render(<CategoryGrid {...defaultProps} selectedCategory="database" />)

      const databaseButton = screen.getByText('Databases').closest('button')
      expect(databaseButton).toBeInTheDocument()
    })

    it('should call onCategorySelect with null when All Apps clicked', async () => {
      const user = userEvent.setup()
      const onCategorySelect = vi.fn()
      render(<CategoryGrid {...defaultProps} onCategorySelect={onCategorySelect} />)

      await user.click(screen.getByText('All Apps'))

      expect(onCategorySelect).toHaveBeenCalledWith(null)
    })

    it('should call onCategorySelect with category id when category clicked', async () => {
      const user = userEvent.setup()
      const onCategorySelect = vi.fn()
      render(<CategoryGrid {...defaultProps} onCategorySelect={onCategorySelect} />)

      await user.click(screen.getByText('Databases'))

      expect(onCategorySelect).toHaveBeenCalledWith('database')
    })
  })
})
