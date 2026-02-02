/**
 * NavigationItem Test Suite
 *
 * Tests for the NavigationItem component including rendering,
 * active states, badges, sub-items, and expand/collapse.
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { Home, Settings } from 'lucide-react'
import { NavigationItem } from '../NavigationItem'
import { NavItem, SubNavItem } from '@/hooks/useNavigation'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

const createNavItem = (overrides: Partial<NavItem> = {}): NavItem => ({
  id: 'test-item',
  label: 'Test Item',
  icon: Home,
  href: '/test',
  description: 'Test description',
  ...overrides
})

describe('NavigationItem', () => {
  describe('Rendering', () => {
    it('should render item label', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem({ label: 'Dashboard' })} isActive={false} />
      )

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('should render as link when no sub-items', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem({ href: '/servers' })} isActive={false} />
      )

      expect(screen.getByRole('link')).toHaveAttribute('href', '/servers')
    })

    it('should render with description as title', () => {
      renderWithRouter(
        <NavigationItem
          item={createNavItem({ description: 'Navigate to dashboard' })}
          isActive={false}
        />
      )

      expect(screen.getByTitle('Navigate to dashboard')).toBeInTheDocument()
    })
  })

  describe('Active State', () => {
    it('should apply active styles when isActive is true', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem()} isActive={true} />
      )

      const link = screen.getByRole('link')
      expect(link).toHaveClass('bg-primary')
    })

    it('should not apply active styles when isActive is false', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem()} isActive={false} />
      )

      const link = screen.getByRole('link')
      expect(link).not.toHaveClass('bg-primary')
    })
  })

  describe('Badge', () => {
    it('should render badge when provided', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem({ badge: 5 })} isActive={false} />
      )

      expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('should render string badge', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem({ badge: 'NEW' })} isActive={false} />
      )

      expect(screen.getByText('NEW')).toBeInTheDocument()
    })

    it('should not render badge when not provided', () => {
      renderWithRouter(
        <NavigationItem item={createNavItem()} isActive={false} />
      )

      expect(screen.queryByText(/\d+/)).not.toBeInTheDocument()
    })
  })

  describe('Sub-Items', () => {
    const itemWithSubItems = createNavItem({
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      subItems: [
        { label: 'General', href: '/settings/general' },
        { label: 'Security', href: '/settings/security', count: 3 }
      ]
    })

    it('should render as button when has sub-items', () => {
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} />
      )

      expect(screen.getByRole('button')).toBeInTheDocument()
      expect(screen.queryByRole('link', { name: 'Settings' })).not.toBeInTheDocument()
    })

    it('should have aria-expanded attribute', () => {
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} isExpanded={false} />
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'false')
    })

    it('should show aria-expanded true when expanded', () => {
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} isExpanded={true} />
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'true')
    })

    it('should render sub-items when expanded', () => {
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} isExpanded={true} />
      )

      expect(screen.getByRole('link', { name: /general/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /security/i })).toBeInTheDocument()
    })

    it('should render sub-item counts', () => {
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} isExpanded={true} />
      )

      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should call onToggle when clicked', async () => {
      const user = userEvent.setup()
      const onToggle = vi.fn()
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} onToggle={onToggle} />
      )

      await user.click(screen.getByRole('button'))

      expect(onToggle).toHaveBeenCalledTimes(1)
    })

    it('should call onSubItemClick when sub-item clicked', async () => {
      const user = userEvent.setup()
      const onSubItemClick = vi.fn()
      renderWithRouter(
        <NavigationItem
          item={itemWithSubItems}
          isActive={false}
          isExpanded={true}
          onSubItemClick={onSubItemClick}
        />
      )

      await user.click(screen.getByRole('link', { name: /general/i }))

      expect(onSubItemClick).toHaveBeenCalledWith(
        expect.objectContaining({ label: 'General', href: '/settings/general' })
      )
    })

    it('should highlight active sub-item', () => {
      const isActiveSubItem = (subItem: SubNavItem) => subItem.href === '/settings/security'
      renderWithRouter(
        <NavigationItem
          item={itemWithSubItems}
          isActive={false}
          isExpanded={true}
          isActiveSubItem={isActiveSubItem}
        />
      )

      const securityLink = screen.getByRole('link', { name: /security/i })
      expect(securityLink).toHaveClass('bg-primary')
    })
  })

  describe('Accessibility', () => {
    it('should have aria-controls for sub-items', () => {
      const itemWithSubItems = createNavItem({
        id: 'nav-test',
        subItems: [{ label: 'Sub', href: '/sub' }]
      })
      renderWithRouter(
        <NavigationItem item={itemWithSubItems} isActive={false} />
      )

      expect(screen.getByRole('button')).toHaveAttribute('aria-controls', 'nav-subitems-nav-test')
    })
  })

  describe('Memoization', () => {
    it('should have displayName', () => {
      expect(NavigationItem.displayName).toBe('NavigationItem')
    })
  })
})
