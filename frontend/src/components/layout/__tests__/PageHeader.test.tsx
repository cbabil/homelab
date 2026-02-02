/**
 * PageHeader Test Suite
 *
 * Tests for the PageHeader component including rendering,
 * optional subtitle, children, and actions.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageHeader } from '../PageHeader'

describe('PageHeader', () => {
  describe('Rendering', () => {
    it('should render title', () => {
      render(<PageHeader title="Dashboard" />)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('should render title with h4 variant', () => {
      render(<PageHeader title="Settings" />)

      expect(screen.getByText('Settings').tagName).toBe('H4')
    })

    it('should render without subtitle by default', () => {
      render(<PageHeader title="Test Page" />)

      expect(screen.queryByText(/secondary/i)).not.toBeInTheDocument()
    })
  })

  describe('Subtitle', () => {
    it('should render subtitle when provided', () => {
      render(<PageHeader title="Servers" subtitle="Manage your servers" />)

      expect(screen.getByText('Manage your servers')).toBeInTheDocument()
    })

    it('should not render subtitle when not provided', () => {
      const { container } = render(<PageHeader title="Servers" />)

      // Only the title should exist
      const textElements = container.querySelectorAll('p')
      expect(textElements.length).toBe(0)
    })
  })

  describe('Children', () => {
    it('should render children content', () => {
      render(
        <PageHeader title="Applications">
          <span data-testid="child-content">Tab Navigation</span>
        </PageHeader>
      )

      expect(screen.getByTestId('child-content')).toBeInTheDocument()
    })

    it('should render multiple children', () => {
      render(
        <PageHeader title="Dashboard">
          <button>Tab 1</button>
          <button>Tab 2</button>
        </PageHeader>
      )

      expect(screen.getByRole('button', { name: 'Tab 1' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Tab 2' })).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should render actions when provided', () => {
      render(
        <PageHeader
          title="Servers"
          actions={<button>Add Server</button>}
        />
      )

      expect(screen.getByRole('button', { name: 'Add Server' })).toBeInTheDocument()
    })

    it('should render multiple actions', () => {
      render(
        <PageHeader
          title="Applications"
          actions={
            <>
              <button>Refresh</button>
              <button>Add App</button>
            </>
          }
        />
      )

      expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Add App' })).toBeInTheDocument()
    })

    it('should not render actions section when not provided', () => {
      const { container } = render(<PageHeader title="Test" />)

      // Only one Stack for title/children, not for actions
      const buttons = container.querySelectorAll('button')
      expect(buttons.length).toBe(0)
    })
  })

  describe('Complete Layout', () => {
    it('should render title, subtitle, children and actions together', () => {
      render(
        <PageHeader
          title="Marketplace"
          subtitle="Browse and install applications"
          actions={<button>Manage Repos</button>}
        >
          <span data-testid="filter-tabs">Filters</span>
        </PageHeader>
      )

      expect(screen.getByText('Marketplace')).toBeInTheDocument()
      expect(screen.getByText('Browse and install applications')).toBeInTheDocument()
      expect(screen.getByTestId('filter-tabs')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Manage Repos' })).toBeInTheDocument()
    })
  })
})
