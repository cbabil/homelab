/**
 * Unit tests for DashboardResourceUsage component
 *
 * Tests resource usage bars and status display.
 */

import { describe, it, expect, vi } from 'vitest'
import './setup'
import { render, screen } from '@testing-library/react'
import { DashboardResourceUsage } from '../DashboardResourceUsage'
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

describe('DashboardResourceUsage', () => {
  it('should render the resource usage title', () => {
    render(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Resource Usage')).toBeInTheDocument()
  })

  it('should display CPU usage', () => {
    render(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('CPU Usage')).toBeInTheDocument()
    expect(screen.getByText('45.5%')).toBeInTheDocument()
  })

  it('should display Memory usage', () => {
    render(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Memory Usage')).toBeInTheDocument()
    expect(screen.getByText('60.2%')).toBeInTheDocument()
  })

  it('should display Disk usage', () => {
    render(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('Disk Usage')).toBeInTheDocument()
    expect(screen.getByText('35.0%')).toBeInTheDocument()
  })

  it('should display all three resource types', () => {
    render(<DashboardResourceUsage data={mockDashboardData} />)

    expect(screen.getByText('CPU Usage')).toBeInTheDocument()
    expect(screen.getByText('Memory Usage')).toBeInTheDocument()
    expect(screen.getByText('Disk Usage')).toBeInTheDocument()
  })

  it('should format percentages with one decimal place', () => {
    const preciseData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 45.567,
      avg_memory_percent: 60.234,
      avg_disk_percent: 35.891
    }

    render(<DashboardResourceUsage data={preciseData} />)

    expect(screen.getByText('45.6%')).toBeInTheDocument()
    expect(screen.getByText('60.2%')).toBeInTheDocument()
    expect(screen.getByText('35.9%')).toBeInTheDocument()
  })

  it('should show empty state when data is null', () => {
    render(<DashboardResourceUsage data={null} />)

    expect(screen.getByText('No resource data available.')).toBeInTheDocument()
    expect(screen.getByText('Connect a server to see resource metrics.')).toBeInTheDocument()
  })

  it('should show empty state when all values are zero', () => {
    const zeroData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 0,
      avg_memory_percent: 0,
      avg_disk_percent: 0
    }

    render(<DashboardResourceUsage data={zeroData} />)

    expect(screen.getByText('No resource data available.')).toBeInTheDocument()
  })

  it('should clamp values to 0-100 range', () => {
    const outOfRangeData: DashboardSummary = {
      ...mockDashboardData,
      avg_cpu_percent: 150,
      avg_memory_percent: -10,
      avg_disk_percent: 50
    }

    render(<DashboardResourceUsage data={outOfRangeData} />)

    // Values should be clamped to valid percentages
    expect(screen.getByText('100.0%')).toBeInTheDocument()
    expect(screen.getByText('0.0%')).toBeInTheDocument()
    expect(screen.getByText('50.0%')).toBeInTheDocument()
  })
})
