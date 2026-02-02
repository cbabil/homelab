/**
 * ApplicationMetaFields Test Suite
 *
 * Tests for the ApplicationMetaFields form component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Database, Globe } from 'lucide-react'
import { ApplicationMetaFields } from '../ApplicationMetaFields'
import { AppCategory } from '@/types/app'

describe('ApplicationMetaFields', () => {
  const categories: AppCategory[] = [
    { id: 'database', name: 'Databases', description: 'Database applications', icon: Database, color: 'blue' },
    { id: 'web', name: 'Web Apps', description: 'Web applications', icon: Globe, color: 'green' }
  ]

  const defaultProps = {
    formData: {},
    onChange: vi.fn(),
    onCategoryChange: vi.fn(),
    categories
  }

  describe('Rendering', () => {
    it('should render category select', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByText('Category')).toBeInTheDocument()
    })

    it('should render tags field', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByText('Tags')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('web, docker, self-hosted')).toBeInTheDocument()
    })

    it('should render author field', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByText('Author')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Author name')).toBeInTheDocument()
    })

    it('should render license field', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByText('License')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('MIT, GPL-3.0, etc.')).toBeInTheDocument()
    })

    it('should show tags helper text', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByText('Separate tags with commas')).toBeInTheDocument()
    })

    it('should display form data values', () => {
      render(
        <ApplicationMetaFields
          {...defaultProps}
          formData={{
            category: { id: 'database', name: 'Databases', description: 'Database applications', icon: Database, color: 'blue' },
            tags: ['tag1', 'tag2'],
            author: 'John Doe',
            license: 'MIT'
          }}
        />
      )

      expect(screen.getByDisplayValue('tag1, tag2')).toBeInTheDocument()
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument()
      expect(screen.getByDisplayValue('MIT')).toBeInTheDocument()
    })
  })

  describe('Category Selection', () => {
    it('should show category options in select', async () => {
      const user = userEvent.setup()
      render(<ApplicationMetaFields {...defaultProps} />)

      // Open the select
      const selectButton = screen.getByRole('combobox')
      await user.click(selectButton)

      // Check options are visible
      const listbox = screen.getByRole('listbox')
      expect(within(listbox).getByText('Databases')).toBeInTheDocument()
      expect(within(listbox).getByText('Web Apps')).toBeInTheDocument()
    })

    it('should call onCategoryChange when category selected', async () => {
      const user = userEvent.setup()
      const onCategoryChange = vi.fn()
      render(<ApplicationMetaFields {...defaultProps} onCategoryChange={onCategoryChange} />)

      const selectButton = screen.getByRole('combobox')
      await user.click(selectButton)
      await user.click(screen.getByText('Databases'))

      expect(onCategoryChange).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'database', name: 'Databases' })
      )
    })
  })

  describe('Tags Input', () => {
    it('should call onChange with parsed tags array', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationMetaFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('web, docker, self-hosted'), 'web, docker')

      // Should be called multiple times as user types
      expect(onChange).toHaveBeenCalledWith('tags', expect.any(Array))
    })
  })

  describe('User Input', () => {
    it('should call onChange when author changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationMetaFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('Author name'), 'Jane')

      expect(onChange).toHaveBeenCalledWith('author', expect.any(String))
    })

    it('should call onChange when license changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationMetaFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('MIT, GPL-3.0, etc.'), 'Apache')

      expect(onChange).toHaveBeenCalledWith('license', expect.any(String))
    })
  })

  describe('Required Fields', () => {
    it('should mark author as required', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByPlaceholderText('Author name')).toHaveAttribute('required')
    })

    it('should mark license as required', () => {
      render(<ApplicationMetaFields {...defaultProps} />)

      expect(screen.getByPlaceholderText('MIT, GPL-3.0, etc.')).toHaveAttribute('required')
    })
  })
})
