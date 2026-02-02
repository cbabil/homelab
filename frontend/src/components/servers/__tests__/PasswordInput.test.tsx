/**
 * PasswordInput Test Suite
 *
 * Tests for the PasswordInput component with show/hide functionality.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PasswordInput } from '../PasswordInput'

describe('PasswordInput', () => {
  const defaultProps = {
    label: 'Password',
    value: '',
    onChange: vi.fn(),
    placeholder: 'Enter password'
  }

  describe('Rendering', () => {
    it('should render label', () => {
      render(<PasswordInput {...defaultProps} />)

      expect(screen.getByText('Password')).toBeInTheDocument()
    })

    it('should render input with placeholder', () => {
      render(<PasswordInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Enter password')).toBeInTheDocument()
    })

    it('should display current value', () => {
      render(<PasswordInput {...defaultProps} value="secret123" />)

      expect(screen.getByDisplayValue('secret123')).toBeInTheDocument()
    })

    it('should render visibility toggle button', () => {
      render(<PasswordInput {...defaultProps} />)

      expect(screen.getByRole('button')).toBeInTheDocument()
    })
  })

  describe('Password Visibility', () => {
    it('should have password type by default', () => {
      render(<PasswordInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Enter password')).toHaveAttribute('type', 'password')
    })

    it('should toggle to text type when visibility button clicked', async () => {
      const user = userEvent.setup()
      render(<PasswordInput {...defaultProps} />)

      await user.click(screen.getByRole('button'))

      expect(screen.getByPlaceholderText('Enter password')).toHaveAttribute('type', 'text')
    })

    it('should toggle back to password type on second click', async () => {
      const user = userEvent.setup()
      render(<PasswordInput {...defaultProps} />)

      await user.click(screen.getByRole('button'))
      await user.click(screen.getByRole('button'))

      expect(screen.getByPlaceholderText('Enter password')).toHaveAttribute('type', 'password')
    })
  })

  describe('User Input', () => {
    it('should call onChange when user types', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PasswordInput {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('Enter password'), 'a')

      expect(onChange).toHaveBeenCalledWith('a')
    })

    it('should call onChange for each character', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<PasswordInput {...defaultProps} onChange={onChange} />)

      await user.type(screen.getByPlaceholderText('Enter password'), 'abc')

      expect(onChange).toHaveBeenCalledTimes(3)
    })
  })

  describe('Required Attribute', () => {
    it('should not be required by default', () => {
      render(<PasswordInput {...defaultProps} />)

      expect(screen.getByPlaceholderText('Enter password')).not.toHaveAttribute('required')
    })

    it('should be required when required prop is true', () => {
      render(<PasswordInput {...defaultProps} required />)

      expect(screen.getByPlaceholderText('Enter password')).toHaveAttribute('required')
    })
  })
})
