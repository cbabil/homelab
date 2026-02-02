/**
 * AppLayout Test Suite
 *
 * Tests for the AppLayout component including rendering,
 * skip link accessibility, and layout structure.
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AppLayout } from '../AppLayout'

// Mock child components to isolate AppLayout testing
vi.mock('../Navigation', () => ({
  Navigation: () => <nav data-testid="navigation">Navigation</nav>
}))

vi.mock('../Header', () => ({
  Header: () => <header data-testid="header">Header</header>
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('AppLayout', () => {
  describe('Rendering', () => {
    it('should render children content', () => {
      renderWithRouter(
        <AppLayout>
          <div data-testid="page-content">Page Content</div>
        </AppLayout>
      )

      expect(screen.getByTestId('page-content')).toBeInTheDocument()
    })

    it('should render Header component', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      expect(screen.getByTestId('header')).toBeInTheDocument()
    })

    it('should render Navigation component', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      expect(screen.getByTestId('navigation')).toBeInTheDocument()
    })

    it('should render multiple children', () => {
      renderWithRouter(
        <AppLayout>
          <div data-testid="child-1">First</div>
          <div data-testid="child-2">Second</div>
        </AppLayout>
      )

      expect(screen.getByTestId('child-1')).toBeInTheDocument()
      expect(screen.getByTestId('child-2')).toBeInTheDocument()
    })
  })

  describe('Skip Link', () => {
    it('should render skip to main content link', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      expect(screen.getByText('Skip to main content')).toBeInTheDocument()
    })

    it('should have href pointing to main-content', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      const skipLink = screen.getByText('Skip to main content')
      expect(skipLink).toHaveAttribute('href', '#main-content')
    })

    it('should be keyboard focusable', async () => {
      const user = userEvent.setup()
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      await user.tab()

      // Skip link should be first focusable element
      const skipLink = screen.getByText('Skip to main content')
      expect(skipLink).toHaveFocus()
    })
  })

  describe('Main Content Area', () => {
    it('should have main element with id', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toHaveAttribute('id', 'main-content')
    })

    it('should have tabIndex for focus management', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      const main = screen.getByRole('main')
      expect(main).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('Layout Structure', () => {
    it('should contain all layout elements', () => {
      const { container } = renderWithRouter(
        <AppLayout>
          <div data-testid="content">Content</div>
        </AppLayout>
      )

      // Verify structure exists
      expect(container.querySelector('header')).toBeInTheDocument()
      expect(container.querySelector('nav')).toBeInTheDocument()
      expect(container.querySelector('main')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper landmark structure', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      // Main landmark exists
      expect(screen.getByRole('main')).toBeInTheDocument()
    })

    it('should have accessible skip link for keyboard navigation', () => {
      renderWithRouter(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      const skipLink = screen.getByText('Skip to main content')
      expect(skipLink.tagName).toBe('A')
    })
  })
})
