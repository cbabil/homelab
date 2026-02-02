/**
 * SearchInput Test Suite
 *
 * Tests for the SearchInput component including rendering,
 * user input handling, and placeholder customization.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchInput } from '../SearchInput'

describe('SearchInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render search input', () => {
      render(<SearchInput {...defaultProps} />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render with default placeholder', () => {
      render(<SearchInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
    })

    it('should render with custom placeholder', () => {
      render(<SearchInput {...defaultProps} placeholder="Find servers..." />)

      expect(screen.getByPlaceholderText('Find servers...')).toBeInTheDocument()
    })

    it('should display current value', () => {
      render(<SearchInput {...defaultProps} value="test query" />)

      expect(screen.getByDisplayValue('test query')).toBeInTheDocument()
    })
  })

  describe('User Interaction', () => {
    it('should call onChange when user types', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<SearchInput value="" onChange={onChange} />)

      const input = screen.getByRole('textbox')
      await user.type(input, 'a')

      expect(onChange).toHaveBeenCalledWith('a')
    })

    it('should call onChange for each character typed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<SearchInput value="" onChange={onChange} />)

      const input = screen.getByRole('textbox')
      await user.type(input, 'abc')

      expect(onChange).toHaveBeenCalledTimes(3)
    })

    it('should allow clearing the input', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<SearchInput value="test" onChange={onChange} />)

      const input = screen.getByRole('textbox')
      await user.clear(input)

      expect(onChange).toHaveBeenCalledWith('')
    })
  })

  describe('Accessibility', () => {
    it('should be focusable', async () => {
      const user = userEvent.setup()
      render(<SearchInput {...defaultProps} />)

      const input = screen.getByRole('textbox')
      await user.click(input)

      expect(input).toHaveFocus()
    })

    it('should have type="text"', () => {
      render(<SearchInput {...defaultProps} />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('type', 'text')
    })
  })
})
