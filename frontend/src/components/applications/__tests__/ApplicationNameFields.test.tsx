/**
 * ApplicationNameFields Test Suite
 *
 * Tests for the ApplicationNameFields form component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApplicationNameFields } from '../ApplicationNameFields'

describe('ApplicationNameFields', () => {
  const defaultProps = {
    formData: {},
    onChange: vi.fn()
  }

  describe('Rendering', () => {
    it('should render application name field', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByText('Application Name')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Enter application name')).toBeInTheDocument()
    })

    it('should render description field', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByText('Description')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Brief description of the application')).toBeInTheDocument()
    })

    it('should render version field', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByText('Version')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('1.0.0')).toBeInTheDocument()
    })

    it('should display form data values', () => {
      render(
        <ApplicationNameFields
          {...defaultProps}
          formData={{
            name: 'My App',
            description: 'Test description',
            version: '2.0.0'
          }}
        />
      )

      expect(screen.getByDisplayValue('My App')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test description')).toBeInTheDocument()
      expect(screen.getByDisplayValue('2.0.0')).toBeInTheDocument()
    })
  })

  describe('User Input', () => {
    it('should call onChange when name changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationNameFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('Enter application name'), 'New App')

      expect(onChange).toHaveBeenCalledWith('name', expect.any(String))
    })

    it('should call onChange when description changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationNameFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('Brief description of the application'), 'Desc')

      expect(onChange).toHaveBeenCalledWith('description', expect.any(String))
    })

    it('should call onChange when version changes', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<ApplicationNameFields {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('1.0.0'), '3')

      expect(onChange).toHaveBeenCalledWith('version', expect.any(String))
    })
  })

  describe('Required Fields', () => {
    it('should mark name as required', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByPlaceholderText('Enter application name')).toHaveAttribute('required')
    })

    it('should mark description as required', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByPlaceholderText('Brief description of the application')).toHaveAttribute('required')
    })

    it('should mark version as required', () => {
      render(<ApplicationNameFields {...defaultProps} />)

      expect(screen.getByPlaceholderText('1.0.0')).toHaveAttribute('required')
    })
  })
})
