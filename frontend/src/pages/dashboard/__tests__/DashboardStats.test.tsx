/**
 * Unit tests for DashboardStats component
 *
 * Tests stat cards display with various data states.
 */

import { describe, it, expect, vi } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { DashboardStats } from '../DashboardStats'
import { DashboardSummary } from '@/types/mcp'

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
    render(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('Total Servers')).toBeInTheDocument()
    expect(screen.getByText('Total Applications')).toBeInTheDocument()
    expect(screen.getByText('Running Apps')).toBeInTheDocument()
    expect(screen.getByText('Issues')).toBeInTheDocument()
  })

  it('should display correct server count', () => {
    render(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('4 online, 1 offline')).toBeInTheDocument()
  })

  it('should display correct application count', () => {
    render(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('8 running, 1 stopped')).toBeInTheDocument()
  })

  it('should display running apps count', () => {
    render(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Healthy')).toBeInTheDocument()
  })

  it('should display issues count (stopped + errors)', () => {
    render(<DashboardStats data={mockDashboardData} />)

    // Issues = stopped_apps (1) + error_apps (1) = 2
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('Errors')).toBeInTheDocument()
  })

  it('should display online badge when servers are online', () => {
    render(<DashboardStats data={mockDashboardData} />)

    expect(screen.getByText('4 Online')).toBeInTheDocument()
  })

  it('should display offline badge when no servers are online', () => {
    const dataWithOfflineServers: DashboardSummary = {
      ...mockDashboardData,
      online_servers: 0,
      offline_servers: 5
    }

    render(<DashboardStats data={dataWithOfflineServers} />)

    expect(screen.getByText('5 Offline')).toBeInTheDocument()
  })

  it('should display "All Clear" when no issues', () => {
    const dataWithNoIssues: DashboardSummary = {
      ...mockDashboardData,
      stopped_apps: 0,
      error_apps: 0
    }

    render(<DashboardStats data={dataWithNoIssues} />)

    expect(screen.getByText('All Clear')).toBeInTheDocument()
  })

  it('should display "Stopped" badge when only stopped apps', () => {
    const dataWithStoppedOnly: DashboardSummary = {
      ...mockDashboardData,
      stopped_apps: 2,
      error_apps: 0
    }

    render(<DashboardStats data={dataWithStoppedOnly} />)

    expect(screen.getByText('Stopped')).toBeInTheDocument()
  })

  it('should handle null data gracefully', () => {
    render(<DashboardStats data={null} />)

    // Should show zeros for all values
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(4)
  })

  it('should not display Healthy badge when no running apps', () => {
    const dataWithNoRunning: DashboardSummary = {
      ...mockDashboardData,
      running_apps: 0
    }

    render(<DashboardStats data={dataWithNoRunning} />)

    expect(screen.queryByText('Healthy')).not.toBeInTheDocument()
  })
})
