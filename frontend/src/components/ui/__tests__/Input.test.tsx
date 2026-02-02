/**
 * Input Component Test Suite
 *
 * Tests for the Input and Textarea components including rendering,
 * validation states, accessibility, and user interactions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input, Textarea } from '../Input'

describe('Input', () => {
  describe('Rendering', () => {
    it('should render input element', () => {
      render(<Input />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render with label', () => {
      render(<Input label="Username" />)

      expect(screen.getByLabelText('Username')).toBeInTheDocument()
    })

    it('should render with placeholder', () => {
      render(<Input placeholder="Enter username" />)

      expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument()
    })

    it('should render with value', () => {
      render(<Input value="test value" readOnly />)

      expect(screen.getByDisplayValue('test value')).toBeInTheDocument()
    })

    it('should render helper text', () => {
      render(<Input helperText="Must be at least 3 characters" />)

      expect(screen.getByText('Must be at least 3 characters')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<Input error="This field is required" />)

      expect(screen.getByText('This field is required')).toBeInTheDocument()
    })

    it('should have aria-invalid when error is present', () => {
      render(<Input error="Error message" />)

      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
    })

    it('should show error role alert', () => {
      render(<Input error="Error message" label="Field" />)

      expect(screen.getByRole('alert')).toHaveTextContent('Error message')
    })

    it('should hide helper text when error is present', () => {
      render(<Input error="Error" helperText="Helper" />)

      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.queryByText('Helper')).not.toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('should render small size', () => {
      render(<Input size="sm" data-testid="input" />)

      expect(screen.getByTestId('input')).toBeInTheDocument()
    })

    it('should render medium size (default)', () => {
      render(<Input data-testid="input" />)

      expect(screen.getByTestId('input')).toBeInTheDocument()
    })

    it('should render large size', () => {
      render(<Input size="lg" data-testid="input" />)

      expect(screen.getByTestId('input')).toBeInTheDocument()
    })
  })

  describe('Icons', () => {
    it('should render left icon', () => {
      render(<Input leftIcon={<span data-testid="left-icon">L</span>} />)

      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    })

    it('should render right icon', () => {
      render(<Input rightIcon={<span data-testid="right-icon">R</span>} />)

      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })

    it('should render both icons', () => {
      render(
        <Input
          leftIcon={<span data-testid="left-icon">L</span>}
          rightIcon={<span data-testid="right-icon">R</span>}
        />
      )

      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })
  })

  describe('User Interaction', () => {
    it('should call onChange when typing', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<Input onChange={onChange} />)

      await user.type(screen.getByRole('textbox'), 'hello')

      expect(onChange).toHaveBeenCalled()
    })

    it('should be focusable', async () => {
      const user = userEvent.setup()
      render(<Input />)

      const input = screen.getByRole('textbox')
      await user.click(input)

      expect(input).toHaveFocus()
    })

    it('should be disabled when disabled prop is true', () => {
      render(<Input disabled />)

      expect(screen.getByRole('textbox')).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should associate label with input via htmlFor', () => {
      render(<Input label="Email" />)

      const input = screen.getByLabelText('Email')
      expect(input).toHaveAttribute('id', 'email')
    })

    it('should use custom id when provided', () => {
      render(<Input label="Email" id="custom-email" />)

      const input = screen.getByLabelText('Email')
      expect(input).toHaveAttribute('id', 'custom-email')
    })

    it('should have aria-describedby for error', () => {
      render(<Input label="Field" error="Error message" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'field-error')
    })

    it('should have aria-describedby for helper text', () => {
      render(<Input label="Field" helperText="Helper text" />)

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'field-helper')
    })

    it('should have aria-required when required', () => {
      render(<Input required />)

      expect(screen.getByRole('textbox')).toHaveAttribute('aria-required', 'true')
    })
  })

  describe('Full Width', () => {
    it('should apply full width styling', () => {
      const { container } = render(<Input fullWidth />)

      // The wrapper Stack should have full width
      expect(container.firstChild).toBeInTheDocument()
    })
  })
})

describe('Textarea', () => {
  describe('Rendering', () => {
    it('should render textarea element', () => {
      render(<Textarea />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render with label', () => {
      render(<Textarea label="Description" />)

      expect(screen.getByLabelText('Description')).toBeInTheDocument()
    })

    it('should render with placeholder', () => {
      render(<Textarea placeholder="Enter description" />)

      expect(screen.getByPlaceholderText('Enter description')).toBeInTheDocument()
    })

    it('should display value', () => {
      render(<Textarea value="test content" readOnly />)

      expect(screen.getByDisplayValue('test content')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<Textarea error="Description is required" />)

      expect(screen.getByText('Description is required')).toBeInTheDocument()
    })

    it('should display helper text', () => {
      render(<Textarea helperText="Maximum 500 characters" />)

      expect(screen.getByText('Maximum 500 characters')).toBeInTheDocument()
    })
  })

  describe('User Interaction', () => {
    it('should call onChange when typing', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<Textarea onChange={onChange} />)

      await user.type(screen.getByRole('textbox'), 'hello')

      expect(onChange).toHaveBeenCalled()
    })

    it('should be disabled when disabled prop is true', () => {
      render(<Textarea disabled />)

      expect(screen.getByRole('textbox')).toBeDisabled()
    })
  })
})
