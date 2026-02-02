/**
 * Unit tests for DashboardRecentActivity component
 *
 * Tests activity log display and formatting.
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardRecentActivity } from '../DashboardRecentActivity'
import { ActivityLog } from '@/types/mcp'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('DashboardRecentActivity', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-15T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const createActivity = (overrides: Partial<ActivityLog> = {}): ActivityLog => ({
    id: '1',
    activity_type: 'server_connect',
    description: 'Server connected',
    created_at: new Date().toISOString(),
    ...overrides
  })

  it('should render the title', () => {
    renderWithRouter(<DashboardRecentActivity activities={[]} />)

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('should show empty state when no activities', () => {
    renderWithRouter(<DashboardRecentActivity activities={[]} />)

    expect(screen.getByText('No recent activity')).toBeInTheDocument()
    expect(screen.getByText('Events will appear here as they occur')).toBeInTheDocument()
  })

  it('should display View all link', () => {
    renderWithRouter(<DashboardRecentActivity activities={[]} />)

    expect(screen.getByText('View all')).toBeInTheDocument()
  })

  it('should display activity description', () => {
    const activities = [createActivity({ description: 'Test server connected' })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Test server connected')).toBeInTheDocument()
  })

  it('should display activity type as badge', () => {
    const activities = [createActivity({ activity_type: 'server_connect' })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Server Connect')).toBeInTheDocument()
  })

  it('should display server_id when present', () => {
    const activities = [createActivity({ server_id: 'server-123' })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('server-123')).toBeInTheDocument()
  })

  it('should format time as "Just now" for recent activity', () => {
    const activities = [createActivity({ created_at: new Date().toISOString() })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Just now')).toBeInTheDocument()
  })

  it('should format time as minutes ago', () => {
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000)
    const activities = [createActivity({ created_at: tenMinutesAgo.toISOString() })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('10m ago')).toBeInTheDocument()
  })

  it('should format time as hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000)
    const activities = [createActivity({ created_at: twoHoursAgo.toISOString() })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('2h ago')).toBeInTheDocument()
  })

  it('should format time as days ago', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    const activities = [createActivity({ created_at: threeDaysAgo.toISOString() })]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('3d ago')).toBeInTheDocument()
  })

  it('should limit displayed activities to 8', () => {
    const activities = Array.from({ length: 15 }, (_, i) =>
      createActivity({ id: `${i}`, description: `Activity ${i}` })
    )

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Activity 0')).toBeInTheDocument()
    expect(screen.getByText('Activity 7')).toBeInTheDocument()
    expect(screen.queryByText('Activity 8')).not.toBeInTheDocument()
  })

  it('should handle different activity types', () => {
    const activities = [
      createActivity({ id: '1', activity_type: 'server_connect' }),
      createActivity({ id: '2', activity_type: 'app_install' }),
      createActivity({ id: '3', activity_type: 'error' })
    ]

    renderWithRouter(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Server Connect')).toBeInTheDocument()
    expect(screen.getByText('App Install')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
  })
})
