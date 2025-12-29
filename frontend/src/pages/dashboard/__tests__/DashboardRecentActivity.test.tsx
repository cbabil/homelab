/**
 * Unit tests for DashboardRecentActivity component
 *
 * Tests activity log display and formatting.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { DashboardRecentActivity } from '../DashboardRecentActivity'
import { ActivityLog } from '@/types/mcp'

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
    render(<DashboardRecentActivity activities={[]} />)

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('should show empty state when no activities', () => {
    render(<DashboardRecentActivity activities={[]} />)

    expect(screen.getByText('No recent activity')).toBeInTheDocument()
    expect(screen.getByText('System events will appear here as they occur.')).toBeInTheDocument()
  })

  it('should display activity count badge', () => {
    const activities = [createActivity({ id: '1' }), createActivity({ id: '2' })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('2 events')).toBeInTheDocument()
  })

  it('should display activity description', () => {
    const activities = [createActivity({ description: 'Test server connected' })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Test server connected')).toBeInTheDocument()
  })

  it('should display activity type as badge', () => {
    const activities = [createActivity({ activity_type: 'server_connect' })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('server connect')).toBeInTheDocument()
  })

  it('should display server_id when present', () => {
    const activities = [createActivity({ server_id: 'server-123' })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('server-123')).toBeInTheDocument()
  })

  it('should format time as "Just now" for recent activity', () => {
    const activities = [createActivity({ created_at: new Date().toISOString() })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Just now')).toBeInTheDocument()
  })

  it('should format time as minutes ago', () => {
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000)
    const activities = [createActivity({ created_at: tenMinutesAgo.toISOString() })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('10m ago')).toBeInTheDocument()
  })

  it('should format time as hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000)
    const activities = [createActivity({ created_at: twoHoursAgo.toISOString() })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('2h ago')).toBeInTheDocument()
  })

  it('should format time as days ago', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    const activities = [createActivity({ created_at: threeDaysAgo.toISOString() })]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('3d ago')).toBeInTheDocument()
  })

  it('should limit displayed activities to 10', () => {
    const activities = Array.from({ length: 15 }, (_, i) =>
      createActivity({ id: `${i}`, description: `Activity ${i}` })
    )

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('Activity 0')).toBeInTheDocument()
    expect(screen.getByText('Activity 9')).toBeInTheDocument()
    expect(screen.queryByText('Activity 10')).not.toBeInTheDocument()
  })

  it('should handle different activity types', () => {
    const activities = [
      createActivity({ id: '1', activity_type: 'server_connect' }),
      createActivity({ id: '2', activity_type: 'app_install' }),
      createActivity({ id: '3', activity_type: 'error' })
    ]

    render(<DashboardRecentActivity activities={activities} />)

    expect(screen.getByText('server connect')).toBeInTheDocument()
    expect(screen.getByText('app install')).toBeInTheDocument()
    expect(screen.getByText('error')).toBeInTheDocument()
  })
})
