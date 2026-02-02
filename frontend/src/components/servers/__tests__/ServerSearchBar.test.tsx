/**
 * ServerSearchBar Test Suite
 *
 * Tests for the ServerSearchBar component including
 * rendering, user input, and search functionality.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ServerSearchBar } from '../ServerSearchBar'

describe('ServerSearchBar', () => {
  const defaultProps = {
    searchTerm: '',
    onSearchChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render search input', () => {
      render(<ServerSearchBar {...defaultProps} />)

      expect(screen.getByPlaceholderText(/search servers/i)).toBeInTheDocument()
    })

    it('should display current search term', () => {
      render(<ServerSearchBar {...defaultProps} searchTerm="test-server" />)

      expect(screen.getByDisplayValue('test-server')).toBeInTheDocument()
    })

    it('should render with placeholder text', () => {
      render(<ServerSearchBar {...defaultProps} />)

      expect(screen.getByPlaceholderText('Search servers by name, host, or username...')).toBeInTheDocument()
    })
  })

  describe('User Input', () => {
    it('should call onSearchChange when user types', async () => {
      const user = userEvent.setup()
      const onSearchChange = vi.fn()
      render(<ServerSearchBar {...defaultProps} onSearchChange={onSearchChange} />)

      await user.type(screen.getByPlaceholderText(/search servers/i), 'test')

      expect(onSearchChange).toHaveBeenCalled()
    })

    it('should call onSearchChange with current value', async () => {
      const user = userEvent.setup()
      const onSearchChange = vi.fn()
      render(<ServerSearchBar {...defaultProps} onSearchChange={onSearchChange} />)

      await user.type(screen.getByPlaceholderText(/search servers/i), 'a')

      expect(onSearchChange).toHaveBeenCalledWith('a')
    })

    it('should call onSearchChange for each character', async () => {
      const user = userEvent.setup()
      const onSearchChange = vi.fn()
      render(<ServerSearchBar {...defaultProps} onSearchChange={onSearchChange} />)

      await user.type(screen.getByPlaceholderText(/search servers/i), 'abc')

      expect(onSearchChange).toHaveBeenCalledTimes(3)
    })
  })
})
