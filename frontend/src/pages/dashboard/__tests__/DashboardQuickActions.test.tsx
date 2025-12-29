/**
 * Unit tests for DashboardQuickActions component
 *
 * Tests quick action buttons and navigation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import './setup'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import { DashboardQuickActions } from '../DashboardQuickActions'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn()
  }
})

const mockNavigate = vi.fn()

describe('DashboardQuickActions', () => {
  beforeEach(() => {
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
    mockNavigate.mockClear()
  })

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <DashboardQuickActions />
      </MemoryRouter>
    )
  }

  it('should render the title', () => {
    renderComponent()

    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
  })

  it('should display Manage Servers action', () => {
    renderComponent()

    expect(screen.getByText('Manage Servers')).toBeInTheDocument()
    expect(screen.getByText('View and configure servers')).toBeInTheDocument()
  })

  it('should display Browse Applications action', () => {
    renderComponent()

    expect(screen.getByText('Browse Applications')).toBeInTheDocument()
    expect(screen.getByText('Install and manage apps')).toBeInTheDocument()
  })

  it('should display App Marketplace action', () => {
    renderComponent()

    expect(screen.getByText('App Marketplace')).toBeInTheDocument()
    expect(screen.getByText('Discover new applications')).toBeInTheDocument()
  })

  it('should display Settings action', () => {
    renderComponent()

    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Configure preferences')).toBeInTheDocument()
  })

  it('should navigate to servers page on click', () => {
    renderComponent()

    fireEvent.click(screen.getByText('Manage Servers'))

    expect(mockNavigate).toHaveBeenCalledWith('/servers')
  })

  it('should navigate to applications page on click', () => {
    renderComponent()

    fireEvent.click(screen.getByText('Browse Applications'))

    expect(mockNavigate).toHaveBeenCalledWith('/applications')
  })

  it('should navigate to marketplace page on click', () => {
    renderComponent()

    fireEvent.click(screen.getByText('App Marketplace'))

    expect(mockNavigate).toHaveBeenCalledWith('/marketplace')
  })

  it('should navigate to settings page on click', () => {
    renderComponent()

    fireEvent.click(screen.getByText('Settings'))

    expect(mockNavigate).toHaveBeenCalledWith('/settings')
  })

  it('should render four action buttons', () => {
    renderComponent()

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(4)
  })
})
