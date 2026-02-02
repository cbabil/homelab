/**
 * Unit tests for DashboardResourceUsage component
 *
 * Tests resource usage circular gauges and status display.
 */

import React from 'react'
import { describe, it, expect } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardResourceUsage } from '../DashboardResourceUsage'
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

describe('DashboardResourceUsage', () => {
  it('should render the resource usage title', () => {
    renderWithRouter(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Resource Usage')).toBeInTheDocument()
  })

  it('should display CPU gauge', () => {
    renderWithRouter(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('CPU')).toBeInTheDocument()
    expect(screen.getByText('46%')).toBeInTheDocument()
  })

  it('should display Memory gauge', () => {
    renderWithRouter(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Memory')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('should display Disk gauge', () => {
    renderWithRouter(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Disk')).toBeInTheDocument()
    expect(screen.getByText('35%')).toBeInTheDocument()
  })

  it('should display all three resource gauges', () => {
    renderWithRouter(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('CPU')).toBeInTheDocument()
    expect(screen.getByText('Memory')).toBeInTheDocument()
    expect(screen.getByText('Disk')).toBeInTheDocument()
  })

  it('should show Normal status for low values', () => {
    const lowData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 30,
      avg_memory_percent: 40,
      avg_disk_percent: 50
    }

    renderWithRouter(<DashboardResourceUsage data={lowData} />)

    // All values under 70% should show Normal
    const normalLabels = screen.getAllByText('Normal')
    expect(normalLabels.length).toBe(3)
  })

  it('should show High status for warning values', () => {
    const warningData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 75,
      avg_memory_percent: 80,
      avg_disk_percent: 85
    }

    renderWithRouter(<DashboardResourceUsage data={warningData} />)

    // Values 70-89% should show High
    const highLabels = screen.getAllByText('High')
    expect(highLabels.length).toBe(3)
  })

  it('should show Critical status for high values', () => {
    const criticalData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 95,
      avg_memory_percent: 92,
      avg_disk_percent: 98
    }

    renderWithRouter(<DashboardResourceUsage data={criticalData} />)

    // Values 90%+ should show Critical
    const criticalLabels = screen.getAllByText('Critical')
    expect(criticalLabels.length).toBe(3)
  })

  it('should show empty state when data is null', () => {
    renderWithRouter(<DashboardResourceUsage data={null} />)

    expect(screen.getByText('No metrics available')).toBeInTheDocument()
    expect(screen.getByText('Connect servers to view resource usage')).toBeInTheDocument()
  })

  it('should show empty state when all values are zero', () => {
    const zeroData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 0,
      avg_memory_percent: 0,
      avg_disk_percent: 0
    }

    renderWithRouter(<DashboardResourceUsage data={zeroData} />)

    expect(screen.getByText('No metrics available')).toBeInTheDocument()
  })

  it('should clamp values to 0-100 range', () => {
    const outOfRangeData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 150,
      avg_memory_percent: -10,
      avg_disk_percent: 50
    }

    renderWithRouter(<DashboardResourceUsage data={outOfRangeData} />)

    // Values should be clamped to valid percentages
    expect(screen.getByText('100%')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })
})
