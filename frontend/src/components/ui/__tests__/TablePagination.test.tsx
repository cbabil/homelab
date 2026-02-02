/**
 * TablePagination Test Suite
 *
 * Tests for the TablePagination component including rendering,
 * navigation, edge cases, and accessibility.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TablePagination } from '../TablePagination'

describe('TablePagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 10,
    onPageChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render page info', () => {
      render(<TablePagination {...defaultProps} />)

      // Check that all parts are present
      expect(screen.getByText(/page/i)).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText(/of 10/)).toBeInTheDocument()
    })

    it('should render Previous button', () => {
      render(<TablePagination {...defaultProps} />)

      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument()
    })

    it('should render Next button', () => {
      render(<TablePagination {...defaultProps} />)

      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    })

    it('should display current page', () => {
      render(<TablePagination {...defaultProps} currentPage={5} />)

      expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('should display total pages', () => {
      render(<TablePagination {...defaultProps} totalPages={25} />)

      expect(screen.getByText(/of 25/)).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('should call onPageChange with previous page when Previous clicked', async () => {
      const user = userEvent.setup()
      const onPageChange = vi.fn()
      render(<TablePagination {...defaultProps} currentPage={5} onPageChange={onPageChange} />)

      await user.click(screen.getByRole('button', { name: /previous/i }))

      expect(onPageChange).toHaveBeenCalledWith(4)
    })

    it('should call onPageChange with next page when Next clicked', async () => {
      const user = userEvent.setup()
      const onPageChange = vi.fn()
      render(<TablePagination {...defaultProps} currentPage={5} onPageChange={onPageChange} />)

      await user.click(screen.getByRole('button', { name: /next/i }))

      expect(onPageChange).toHaveBeenCalledWith(6)
    })
  })

  describe('Edge Cases', () => {
    it('should disable Previous button on first page', () => {
      render(<TablePagination {...defaultProps} currentPage={1} />)

      expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled()
    })

    it('should enable Previous button when not on first page', () => {
      render(<TablePagination {...defaultProps} currentPage={2} />)

      expect(screen.getByRole('button', { name: /previous/i })).not.toBeDisabled()
    })

    it('should disable Next button on last page', () => {
      render(<TablePagination {...defaultProps} currentPage={10} totalPages={10} />)

      expect(screen.getByRole('button', { name: /next/i })).toBeDisabled()
    })

    it('should enable Next button when not on last page', () => {
      render(<TablePagination {...defaultProps} currentPage={9} totalPages={10} />)

      expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled()
    })

    it('should not go below page 1 when Previous clicked on page 1', async () => {
      const onPageChange = vi.fn()
      render(<TablePagination {...defaultProps} currentPage={1} onPageChange={onPageChange} />)

      // Button is disabled, but let's verify the handler logic
      const prevButton = screen.getByRole('button', { name: /previous/i })
      expect(prevButton).toBeDisabled()
    })

    it('should not exceed total pages when Next clicked on last page', async () => {
      const onPageChange = vi.fn()
      render(<TablePagination {...defaultProps} currentPage={10} totalPages={10} onPageChange={onPageChange} />)

      const nextButton = screen.getByRole('button', { name: /next/i })
      expect(nextButton).toBeDisabled()
    })

    it('should handle zero total pages gracefully', () => {
      render(<TablePagination {...defaultProps} totalPages={0} />)

      // Component uses Math.max(1, totalPages) for display
      expect(screen.getByText(/of/)).toBeInTheDocument()
    })

    it('should handle single page', () => {
      render(<TablePagination {...defaultProps} currentPage={1} totalPages={1} />)

      expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /next/i })).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(<TablePagination {...defaultProps} />)

      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
    })

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup()
      const onPageChange = vi.fn()
      render(<TablePagination {...defaultProps} currentPage={5} onPageChange={onPageChange} />)

      // Tab to first button
      await user.tab()
      const prevButton = screen.getByRole('button', { name: /previous/i })
      expect(prevButton).toHaveFocus()

      await user.keyboard('{Enter}')
      expect(onPageChange).toHaveBeenCalledWith(4)
    })
  })
})
