/**
 * Unit tests for Navigation Component
 * 
 * Tests navigation sidebar with routing and active states.
 * Covers navigation items, active states, and accessibility.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Navigation } from './Navigation'

vi.mock('@/hooks/useApplications', () => ({
  useApplications: vi.fn(() => ({
    apps: [],
    categories: [],
    filter: {},
    setFilter: vi.fn(),
    updateFilter: vi.fn(),
    isLoading: false,
    error: null,
    addApplication: vi.fn(),
    updateApplication: vi.fn(),
    deleteApplication: vi.fn(),
    installApplication: vi.fn(),
    refresh: vi.fn()
  }))
}))

describe('Navigation Component', () => {
  const renderNav = (route = '/') => render(
    <MemoryRouter initialEntries={[route]}>
      <Navigation />
    </MemoryRouter>
  )

  it('renders all navigation items with icons', () => {
    renderNav()

    const navItems = ['Dashboard', 'Servers', 'Applications', 'Logs']
    navItems.forEach(item => {
      expect(screen.getByText(item)).toBeInTheDocument()
      const link = screen.getByText(item).parentElement
      expect(link?.querySelector('svg')).toBeInTheDocument()
    })
  })

  it('shows correct active state for each route', () => {
    const routes = [
      { path: '/', active: 'Dashboard' },
      { path: '/servers', active: 'Servers' },
      { path: '/applications', active: 'Applications' },
      { path: '/logs', active: 'Logs' }
    ]

    routes.forEach(({ path, active }) => {
      const { unmount } = renderNav(path)
      const activeLink = screen.getAllByText(active)[0].parentElement
      expect(activeLink).toHaveClass('nav-active')
      unmount()
    })
  })

  it('has proper structure and styling', () => {
    renderNav()

    const aside = screen.getByRole('complementary')
    expect(aside).toHaveClass('w-64', 'border-r', 'flex', 'flex-col')

    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
  })

  it('renders correct href attributes', () => {
    renderNav()

    const links = [
      { text: 'Dashboard', href: '/' },
      { text: 'Servers', href: '/servers' },
      { text: 'Applications', href: '/applications' },
      { text: 'Logs', href: '/logs' }
    ]

    links.forEach(({ text, href }) => {
      expect(screen.getByText(text).closest('a')).toHaveAttribute('href', href)
    })
  })

  it('handles unknown routes without active state', () => {
    renderNav('/unknown-route')

    const navigationLinks = screen.getAllByRole('link')
    navigationLinks.forEach(link => {
      expect(link).not.toHaveClass('nav-active')
      expect(link).toHaveClass('text-gray-600')
    })
  })

  it('has proper visual hierarchy and maintains single active state', () => {
    renderNav('/applications')

    const activeLink = screen.getByText('Applications').parentElement
    expect(activeLink).toHaveClass('nav-active')

    // Check inactive items have muted styling
    const inactiveItems = ['Dashboard', 'Servers', 'Logs']
    inactiveItems.forEach(item => {
      const link = screen.getByText(item).parentElement
      expect(link).toHaveClass('text-gray-600')
      expect(link).not.toHaveClass('nav-active')
    })

    // Verify only one active item exists
    const activeLinks = screen.getAllByRole('link').filter(link => 
      link.classList.contains('nav-active')
    )
    expect(activeLinks).toHaveLength(1)
  })

  it('shows Applications submenu when on applications route', () => {
    renderNav('/applications')

    // Applications should be active and show submenu
    const applicationsLink = screen.getByText('Applications').parentElement
    expect(applicationsLink).toHaveClass('nav-active')

    // Submenu should be visible and "All Apps" should be active
    expect(screen.getByText(/All Apps \(\d+\)/)).toBeInTheDocument()
  })

  it('shows correct active state for "All Apps" when no category selected', () => {
    renderNav('/applications')

    // "All Apps" should be active when on base applications route
    const allAppsLink = screen.getByText(/All Apps \(\d+\)/).closest('a')
    expect(allAppsLink).toHaveClass('text-primary', 'bg-gray-100')
    expect(allAppsLink).not.toHaveClass('text-gray-500')
  })

  it('shows correct active state for category when category selected', () => {
    renderNav('/applications?category=media')

    // Applications should be active and show submenu
    const applicationsLink = screen.getByText('Applications').parentElement
    expect(applicationsLink).toHaveClass('nav-active')

    // "All Apps" should NOT be active when category is selected
    const allAppsLink = screen.getByText(/All Apps \(\d+\)/).closest('a')
    expect(allAppsLink).toHaveClass('text-gray-500')
    expect(allAppsLink).not.toHaveClass('text-primary', 'bg-gray-100')

    // The specific category should be active (assuming Media Server exists)
    const categoryLinks = screen.getAllByRole('link').filter(link => 
      link.textContent?.includes('(') && 
      link.textContent !== screen.getByText(/All Apps \(\d+\)/).textContent &&
      (link as HTMLAnchorElement).href?.includes('category=')
    )
    
    // At least one category should be active
    const activeCategoryLinks = categoryLinks.filter(link =>
      link.classList.contains('text-primary') && link.classList.contains('bg-gray-100')
    )
    expect(activeCategoryLinks.length).toBeGreaterThan(0)
  })

  it('maintains exclusive active states in submenu', () => {
    renderNav('/applications?category=media')

    // Only one submenu item should be active at a time
    const submenuLinks = screen.getAllByRole('link').filter(link => 
      link.textContent?.includes('(') && 
      ((link as HTMLAnchorElement).href?.includes('/applications') || (link as HTMLAnchorElement).href?.includes('category='))
    )
    
    const activeSubmenuLinks = submenuLinks.filter(link =>
      link.classList.contains('text-primary') && link.classList.contains('bg-gray-100')
    )
    
    // Exactly one submenu item should be active
    expect(activeSubmenuLinks).toHaveLength(1)
  })
})
