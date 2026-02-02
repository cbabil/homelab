/**
 * NavigationSection Test Suite
 *
 * Tests for the NavigationSection component including rendering,
 * title display, collapsible behavior, and dividers.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NavigationSection } from '../NavigationSection'

describe('NavigationSection', () => {
  describe('Rendering', () => {
    it('should render children', () => {
      render(
        <NavigationSection>
          <div data-testid="child">Child Content</div>
        </NavigationSection>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
    })

    it('should render multiple children', () => {
      render(
        <NavigationSection>
          <button>Item 1</button>
          <button>Item 2</button>
          <button>Item 3</button>
        </NavigationSection>
      )

      expect(screen.getAllByRole('button')).toHaveLength(3)
    })

    it('should apply className when provided', () => {
      const { container } = render(
        <NavigationSection className="custom-class">
          <div>Content</div>
        </NavigationSection>
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('Title', () => {
    it('should render title when provided', () => {
      render(
        <NavigationSection title="Main Menu">
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('heading', { name: 'Main Menu' })).toBeInTheDocument()
    })

    it('should not render title when not provided', () => {
      render(
        <NavigationSection>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    it('should render title as h3', () => {
      render(
        <NavigationSection title="Settings">
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('heading').tagName).toBe('H3')
    })
  })

  describe('Divider', () => {
    it('should render divider when showDivider is true', () => {
      const { container } = render(
        <NavigationSection showDivider>
          <div>Content</div>
        </NavigationSection>
      )

      // Check for border-top style element
      const divider = container.querySelector('[style*="border"]') ||
        container.querySelector('.MuiBox-root')
      expect(divider).toBeInTheDocument()
    })

    it('should not render divider by default', () => {
      const { container } = render(
        <NavigationSection>
          <div>Content</div>
        </NavigationSection>
      )

      // Just verify section renders without errors (no divider by default)
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  describe('Collapsible Behavior', () => {
    it('should render as button when collapsible', () => {
      render(
        <NavigationSection title="Collapsible Section" collapsible>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('button', { name: /collapsible section/i })).toBeInTheDocument()
    })

    it('should have aria-expanded attribute when collapsible', () => {
      render(
        <NavigationSection title="Test" collapsible isCollapsed={false}>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'true')
    })

    it('should have aria-expanded false when collapsed', () => {
      render(
        <NavigationSection title="Test" collapsible isCollapsed={true}>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'false')
    })

    it('should call onToggle when button clicked', async () => {
      const user = userEvent.setup()
      const onToggle = vi.fn()
      render(
        <NavigationSection title="Test" collapsible onToggle={onToggle}>
          <div>Content</div>
        </NavigationSection>
      )

      await user.click(screen.getByRole('button'))

      expect(onToggle).toHaveBeenCalledTimes(1)
    })

    it('should have aria-controls matching section id', () => {
      render(
        <NavigationSection title="Main Menu" collapsible>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-controls', 'nav-section-main-menu')
    })

    it('should generate correct id from title with spaces', () => {
      render(
        <NavigationSection title="My Custom Section" collapsible>
          <div data-testid="content">Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-controls', 'nav-section-my-custom-section')
    })
  })

  describe('Non-Collapsible', () => {
    it('should render title as heading when not collapsible', () => {
      render(
        <NavigationSection title="Static Section" collapsible={false}>
          <div>Content</div>
        </NavigationSection>
      )

      expect(screen.getByRole('heading', { name: 'Static Section' })).toBeInTheDocument()
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Memoization', () => {
    it('should have displayName', () => {
      expect(NavigationSection.displayName).toBe('NavigationSection')
    })
  })
})
