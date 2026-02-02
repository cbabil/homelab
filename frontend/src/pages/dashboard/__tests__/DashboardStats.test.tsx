/**
 * Unit tests for DashboardStats component
 *
 * Tests stat cards display with various data states.
 */

import React from 'react'
import { describe, it, expect } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardStats } from '../DashboardStats'
import { DashboardSummary } from '@/types/mcp'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

const mockDashboardData: DashboardSummary = {
  total_servers: 5,
  online_servers: 4,
  offline_servers: 1,
  total_apps: 10,
  running_apps: 8,
  stopped_apps: 1,
  error_apps: 1,
  avg_cpu_percent: 45.5,
  avg_memory_percent: 60.2,
  avg_disk_percent: 35.0,
  recent_activities: []
}

describe('DashboardStats', () => {
  it('should render all stat cards', () => {
    renderWithRouter(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('Servers')).toBeInTheDocument()
    expect(screen.getByText('Applications')).toBeInTheDocument()
    expect(screen.getByText('Running')).toBeInTheDocument()
    expect(screen.getByText('Issues')).toBeInTheDocument()
  })

  it('should display correct server count', () => {
    renderWithRouter(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('4 online, 1 offline')).toBeInTheDocument()
  })

  it('should display correct application count', () => {
    renderWithRouter(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('8 running, 1 stopped')).toBeInTheDocument()
  })

  it('should display running apps count', () => {
    renderWithRouter(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('All systems operational')).toBeInTheDocument()
  })

  it('should display issues count (stopped + errors)', () => {
    renderWithRouter(<DashboardStats data={mockDashboardData} />)

    // Issues = stopped_apps (1) + error_apps (1) = 2
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('1 error, 1 stopped')).toBeInTheDocument()
  })

  it('should display no servers configured when zero servers', () => {
    const dataWithNoServers: DashboardSummary = {
      ...mockDashboardData,
      total_servers: 0,
      online_servers: 0,
      offline_servers: 0
    }

    renderWithRouter(<DashboardStats data={dataWithNoServers} />)

    expect(screen.getByText('No servers configured')).toBeInTheDocument()
  })

  it('should display no apps deployed when zero apps', () => {
    const dataWithNoApps: DashboardSummary = {
      ...mockDashboardData,
      total_apps: 0,
      running_apps: 0,
      stopped_apps: 0,
      error_apps: 0
    }

    const { container } = renderWithRouter(<DashboardStats data={dataWithNoApps} />)

    // Check if the text exists anywhere in the component
    expect(container.textContent).toContain('No applications found')
  })

  it('should display "All clear" when no issues', () => {
    const dataWithNoIssues: DashboardSummary = {
      ...mockDashboardData,
      stopped_apps: 0,
      error_apps: 0
    }

    renderWithRouter(<DashboardStats data={dataWithNoIssues} />)

    expect(screen.getByText('All clear')).toBeInTheDocument()
  })

  it('should display stopped apps text when only stopped apps', () => {
    const dataWithStoppedOnly: DashboardSummary = {
      ...mockDashboardData,
      stopped_apps: 2,
      error_apps: 0
    }

    const { container } = renderWithRouter(<DashboardStats data={dataWithStoppedOnly} />)

    // Check if the text exists anywhere in the component
    expect(container.textContent).toContain('2 stopped')
  })

  it('should handle null data gracefully', () => {
    renderWithRouter(<DashboardStats data={null} />)

    // Should show zeros for all values
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(4)
  })

  it('should display no running applications text when none running', () => {
    const dataWithNoRunning: DashboardSummary = {
      ...mockDashboardData,
      running_apps: 0
    }

    renderWithRouter(<DashboardStats data={dataWithNoRunning} />)

    expect(screen.getByText('No running applications')).toBeInTheDocument()
  })
})
