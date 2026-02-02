/**
 * Button Test Suite
 *
 * Tests for the custom Button component with MUI integration.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Settings } from 'lucide-react'
import { Button } from '../Button'

describe('Button', () => {
  describe('Rendering', () => {
    it('should render button with children', () => {
      render(<Button>Click me</Button>)

      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
    })

    it('should render button with left icon', () => {
      render(
        <Button leftIcon={<Settings data-testid="left-icon" />}>Settings</Button>
      )

      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    it('should render button with right icon', () => {
      render(
        <Button rightIcon={<Settings data-testid="right-icon" />}>Settings</Button>
      )

      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })

    it('should render button with both icons', () => {
      render(
        <Button
          leftIcon={<Settings data-testid="left-icon" />}
          rightIcon={<Settings data-testid="right-icon" />}
        >
          Settings
        </Button>
      )

      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    })
  })

  describe('Variants', () => {
    it('should render primary variant by default', () => {
      render(<Button>Primary</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-contained')
    })

    it('should render secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-contained')
    })

    it('should render outline variant', () => {
      render(<Button variant="outline">Outline</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-outlined')
    })

    it('should render ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-text')
    })

    it('should render destructive variant', () => {
      render(<Button variant="destructive">Delete</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-contained')
    })
  })

  describe('Sizes', () => {
    it('should render small size', () => {
      render(<Button size="sm">Small</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-sizeSmall')
    })

    it('should render medium size by default', () => {
      render(<Button>Medium</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-sizeMedium')
    })

    it('should render large size', () => {
      render(<Button size="lg">Large</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-sizeLarge')
    })

    it('should render icon size', () => {
      render(<Button size="icon"><Settings /></Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-sizeSmall')
    })
  })

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      render(<Button loading>Loading</Button>)

      expect(screen.getByLabelText('Loading')).toBeInTheDocument()
      expect(screen.queryByText('Loading')).not.toBeInTheDocument()
    })

    it('should be disabled when loading', () => {
      render(<Button loading>Loading</Button>)

      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should not show icons when loading', () => {
      render(
        <Button
          loading
          leftIcon={<Settings data-testid="left-icon" />}
        >
          Loading
        </Button>
      )

      expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>)

      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should not call onClick when disabled', () => {
      const onClick = vi.fn()
      render(<Button disabled onClick={onClick}>Disabled</Button>)

      // Disabled buttons have pointer-events: none, so we verify disabled state
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(onClick).not.toHaveBeenCalled()
    })
  })

  describe('Interactions', () => {
    it('should call onClick when clicked', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<Button onClick={onClick}>Click me</Button>)

      await user.click(screen.getByRole('button'))

      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('should support form submission', () => {
      render(
        <form>
          <Button type="submit">Submit</Button>
        </form>
      )

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')
    })
  })

  describe('Full Width', () => {
    it('should render full width when fullWidth is true', () => {
      render(<Button fullWidth>Full Width</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('MuiButton-fullWidth')
    })
  })

  describe('Ref Forwarding', () => {
    it('should forward ref to button element', () => {
      const ref = vi.fn()
      render(<Button ref={ref}>Button</Button>)

      expect(ref).toHaveBeenCalled()
      expect(ref.mock.calls[0][0]).toBeInstanceOf(HTMLButtonElement)
    })
  })
})
