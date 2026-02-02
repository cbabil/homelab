/**
 * Select Component Test Suite
 *
 * Tests for the Select component including rendering,
 * option selection, validation states, and accessibility.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Select } from '../Select'

const defaultOptions = [
  { label: 'Option 1', value: 'opt1' },
  { label: 'Option 2', value: 'opt2' },
  { label: 'Option 3', value: 'opt3' }
]

describe('Select', () => {
  describe('Rendering', () => {
    it('should render select element', () => {
      render(<Select options={defaultOptions} />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should render all options', () => {
      render(<Select options={defaultOptions} />)

      expect(screen.getByRole('option', { name: 'Option 1' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Option 2' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Option 3' })).toBeInTheDocument()
    })

    it('should render with label', () => {
      render(<Select options={defaultOptions} label="Choose option" />)

      expect(screen.getByLabelText('Choose option')).toBeInTheDocument()
    })

    it('should render with selected value', () => {
      render(<Select options={defaultOptions} value="opt2" />)

      const select = screen.getByRole('combobox')
      expect(select).toHaveValue('opt2')
    })

    it('should render helper text', () => {
      render(<Select options={defaultOptions} helperText="Select one option" />)

      expect(screen.getByText('Select one option')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<Select options={defaultOptions} error="Selection required" />)

      expect(screen.getByText('Selection required')).toBeInTheDocument()
    })

    it('should show error instead of helper text', () => {
      render(
        <Select options={defaultOptions} error="Error" helperText="Helper" />
      )

      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.queryByText('Helper')).not.toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('should render small size', () => {
      render(<Select options={defaultOptions} size="sm" />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should render medium size (default)', () => {
      render(<Select options={defaultOptions} />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should render large size', () => {
      render(<Select options={defaultOptions} size="lg" />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })
  })

  describe('User Interaction', () => {
    it('should call onChange when option is selected', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<Select options={defaultOptions} onChange={onChange} />)

      await user.selectOptions(screen.getByRole('combobox'), 'opt2')

      expect(onChange).toHaveBeenCalled()
    })

    it('should update displayed value on selection', async () => {
      const user = userEvent.setup()
      render(<Select options={defaultOptions} defaultValue="opt1" />)

      const select = screen.getByRole('combobox')
      await user.selectOptions(select, 'opt3')

      expect(select).toHaveValue('opt3')
    })

    it('should be focusable', async () => {
      const user = userEvent.setup()
      render(<Select options={defaultOptions} />)

      const select = screen.getByRole('combobox')
      await user.click(select)

      expect(select).toHaveFocus()
    })

    it('should be disabled when disabled prop is true', () => {
      render(<Select options={defaultOptions} disabled />)

      expect(screen.getByRole('combobox')).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should associate label with select via htmlFor', () => {
      render(<Select options={defaultOptions} label="Category" />)

      const select = screen.getByLabelText('Category')
      expect(select).toHaveAttribute('id', 'category')
    })

    it('should use custom id when provided', () => {
      render(<Select options={defaultOptions} label="Category" id="custom-cat" />)

      const select = screen.getByLabelText('Category')
      expect(select).toHaveAttribute('id', 'custom-cat')
    })

    it('should have correct option values', () => {
      render(<Select options={defaultOptions} />)

      const options = screen.getAllByRole('option')
      expect(options[0]).toHaveValue('opt1')
      expect(options[1]).toHaveValue('opt2')
      expect(options[2]).toHaveValue('opt3')
    })
  })

  describe('Full Width', () => {
    it('should accept fullWidth prop', () => {
      render(<Select options={defaultOptions} fullWidth />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })
  })

  describe('Empty Options', () => {
    it('should render with empty options array', () => {
      render(<Select options={[]} />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
      expect(screen.queryAllByRole('option')).toHaveLength(0)
    })
  })
})
