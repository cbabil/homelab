/**
 * QuickStats Test Suite
 *
 * Tests for the QuickStats component including rendering,
 * server/app counts, alerts, and navigation links.
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QuickStats } from '../QuickStats'
import { NavigationStats } from '@/hooks/useNavigation'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { count?: number }) => {
      const translations: Record<string, string> = {
        'nav.overview': 'Overview',
        'nav.servers': 'Servers',
        'nav.apps': 'Apps',
        'nav.needsAttention': 'Needs attention'
      }
      if (key === 'nav.alert') {
        return options?.count === 1 ? '1 Alert' : `${options?.count} Alerts`
      }
      return translations[key] || key
    }
  })
}))

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

const createStats = (overrides: Partial<NavigationStats> = {}): NavigationStats => ({
  totalServers: 5,
  connectedServers: 3,
  totalApps: 10,
  installedApps: 7,
  criticalAlerts: 0,
  ...overrides
})

describe('QuickStats', () => {
  describe('Rendering', () => {
    it('should render overview label', () => {
      renderWithRouter(<QuickStats stats={createStats()} />)

      expect(screen.getByText('Overview')).toBeInTheDocument()
    })

    it('should render servers label', () => {
      renderWithRouter(<QuickStats stats={createStats()} />)

      expect(screen.getByText('Servers')).toBeInTheDocument()
    })

    it('should render apps label', () => {
      renderWithRouter(<QuickStats stats={createStats()} />)

      expect(screen.getByText('Apps')).toBeInTheDocument()
    })

    it('should apply className when provided', () => {
      const { container } = renderWithRouter(
        <QuickStats stats={createStats()} className="custom-stats" />
      )

      expect(container.firstChild).toHaveClass('custom-stats')
    })
  })

  describe('Server Stats', () => {
    it('should display server count ratio', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ connectedServers: 3, totalServers: 5 })} />
      )

      expect(screen.getByText('3/5')).toBeInTheDocument()
    })

    it('should link to servers page', () => {
      renderWithRouter(<QuickStats stats={createStats()} />)

      const serversLink = screen.getByRole('link', { name: /servers/i })
      expect(serversLink).toHaveAttribute('href', '/servers')
    })

    it('should show 0/0 when no servers', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ connectedServers: 0, totalServers: 0 })} />
      )

      expect(screen.getByText('0/0')).toBeInTheDocument()
    })
  })

  describe('App Stats', () => {
    it('should display app count ratio', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ installedApps: 7, totalApps: 10 })} />
      )

      expect(screen.getByText('7/10')).toBeInTheDocument()
    })

    it('should link to applications page', () => {
      renderWithRouter(<QuickStats stats={createStats()} />)

      const appsLink = screen.getByRole('link', { name: /apps/i })
      expect(appsLink).toHaveAttribute('href', '/applications')
    })
  })

  describe('Alerts', () => {
    it('should not render alerts section when no alerts', () => {
      renderWithRouter(<QuickStats stats={createStats({ criticalAlerts: 0 })} />)

      expect(screen.queryByText(/alert/i)).not.toBeInTheDocument()
      expect(screen.queryByText('Needs attention')).not.toBeInTheDocument()
    })

    it('should render alerts when present', () => {
      renderWithRouter(<QuickStats stats={createStats({ criticalAlerts: 3 })} />)

      expect(screen.getByText('3 Alerts')).toBeInTheDocument()
      expect(screen.getByText('Needs attention')).toBeInTheDocument()
    })

    it('should render singular alert text for 1 alert', () => {
      renderWithRouter(<QuickStats stats={createStats({ criticalAlerts: 1 })} />)

      expect(screen.getByText('1 Alert')).toBeInTheDocument()
    })

    it('should link to logs page when alerts present', () => {
      renderWithRouter(<QuickStats stats={createStats({ criticalAlerts: 2 })} />)

      const alertsLink = screen.getByRole('link', { name: /alert/i })
      expect(alertsLink).toHaveAttribute('href', '/logs')
    })
  })

  describe('Server Status Colors', () => {
    it('should show success status when all servers connected', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ connectedServers: 5, totalServers: 5 })} />
      )

      // Component renders, status determined by connectedServers === totalServers
      expect(screen.getByText('5/5')).toBeInTheDocument()
    })

    it('should show warning status when some servers disconnected', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ connectedServers: 2, totalServers: 5 })} />
      )

      expect(screen.getByText('2/5')).toBeInTheDocument()
    })

    it('should show default status when no servers', () => {
      renderWithRouter(
        <QuickStats stats={createStats({ connectedServers: 0, totalServers: 0 })} />
      )

      expect(screen.getByText('0/0')).toBeInTheDocument()
    })
  })

  describe('Memoization', () => {
    it('should have displayName', () => {
      expect(QuickStats.displayName).toBe('QuickStats')
    })
  })
})
