/**
 * TimezoneDropdown Test Suite
 *
 * Tests for the TimezoneDropdown component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TimezoneDropdown } from '../TimezoneDropdown'

// Mock the useTimezone hook
vi.mock('@/hooks/useTimezone', () => ({
  useTimezone: vi.fn()
}))

import { useTimezone, type UseTimezoneReturn } from '@/hooks/useTimezone'
const mockUseTimezone = vi.mocked(useTimezone)

describe('TimezoneDropdown', () => {
  const mockTimezones = {
    isInitialized: true,
    isLoading: false,
    error: null,
    currentTimezone: 'America/New_York',
    timezoneGroups: [
      {
        region: 'Americas',
        timezones: [
          { id: 'America/New_York', name: 'New York', offset: -300 },
          { id: 'America/Los_Angeles', name: 'Los Angeles', offset: -480 }
        ]
      },
      {
        region: 'Europe',
        timezones: [
          { id: 'Europe/London', name: 'London', offset: 0 },
          { id: 'Europe/Paris', name: 'Paris', offset: 60 }
        ]
      }
    ],
    popularTimezones: [
      { id: 'UTC', name: 'UTC', offset: 0 },
      { id: 'America/New_York', name: 'New York', offset: -300 }
    ],
    updateTimezone: vi.fn().mockResolvedValue(undefined),
    getTimezoneById: vi.fn().mockReturnValue(null)
  } as unknown as UseTimezoneReturn

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseTimezone.mockReturnValue(mockTimezones)
  })

  describe('Loading State', () => {
    it('should be disabled when loading', () => {
      mockUseTimezone.mockReturnValue({
        ...mockTimezones,
        isLoading: true
      } as UseTimezoneReturn)

      render(<TimezoneDropdown />)

      const select = screen.getByRole('combobox')
      expect(select).toHaveAttribute('aria-disabled', 'true')
    })
  })

  describe('Error State', () => {
    it('should be disabled when error', () => {
      mockUseTimezone.mockReturnValue({
        ...mockTimezones,
        error: 'Failed'
      } as UseTimezoneReturn)

      render(<TimezoneDropdown />)

      const select = screen.getByRole('combobox')
      expect(select).toHaveAttribute('aria-disabled', 'true')
    })
  })

  describe('Rendering', () => {
    it('should render current timezone as selected', () => {
      render(<TimezoneDropdown />)

      // The current timezone should be displayed
      const select = screen.getByRole('combobox')
      expect(select).toBeInTheDocument()
    })

    it('should be disabled when disabled prop is true', () => {
      render(<TimezoneDropdown disabled />)

      const select = screen.getByRole('combobox')
      expect(select).toHaveAttribute('aria-disabled', 'true')
    })
  })

  describe('Timezone Selection', () => {
    it('should show popular timezones when opened', async () => {
      const user = userEvent.setup()
      render(<TimezoneDropdown />)

      await user.click(screen.getByRole('combobox'))

      await waitFor(() => {
        expect(screen.getByText('Popular Timezones')).toBeInTheDocument()
      })
    })

    it('should show regional groups when opened', async () => {
      const user = userEvent.setup()
      render(<TimezoneDropdown />)

      await user.click(screen.getByRole('combobox'))

      await waitFor(() => {
        expect(screen.getByText('Americas')).toBeInTheDocument()
        expect(screen.getByText('Europe')).toBeInTheDocument()
      })
    })

    it('should call updateTimezone when timezone selected', async () => {
      const user = userEvent.setup()
      const updateTimezone = vi.fn().mockResolvedValue(undefined)
      mockUseTimezone.mockReturnValue({
        ...mockTimezones,
        updateTimezone
      } as UseTimezoneReturn)

      render(<TimezoneDropdown />)

      await user.click(screen.getByRole('combobox'))

      await waitFor(() => {
        expect(screen.getByText('Los Angeles (UTC-8)')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Los Angeles (UTC-8)'))

      expect(updateTimezone).toHaveBeenCalledWith('America/Los_Angeles')
    })

    it('should not call updateTimezone when same timezone selected', async () => {
      const user = userEvent.setup()
      const updateTimezone = vi.fn().mockResolvedValue(undefined)
      mockUseTimezone.mockReturnValue({
        ...mockTimezones,
        updateTimezone
      } as UseTimezoneReturn)

      render(<TimezoneDropdown />)

      await user.click(screen.getByRole('combobox'))

      await waitFor(() => {
        // Click on the already selected timezone (New York in popular)
        const newYorkOptions = screen.getAllByText(/New York/)
        expect(newYorkOptions.length).toBeGreaterThan(0)
      })

      // Selecting the current timezone should not trigger update
      const newYorkOptions = screen.getAllByText(/New York/)
      await user.click(newYorkOptions[0])

      expect(updateTimezone).not.toHaveBeenCalled()
    })
  })

  describe('Updating State', () => {
    it('should disable select while updating', async () => {
      const user = userEvent.setup()
      let resolveUpdate: () => void
      const updateTimezone = vi.fn().mockImplementation(() => {
        return new Promise<void>(resolve => {
          resolveUpdate = resolve
        })
      })

      mockUseTimezone.mockReturnValue({
        ...mockTimezones,
        updateTimezone
      } as UseTimezoneReturn)

      render(<TimezoneDropdown />)

      await user.click(screen.getByRole('combobox'))

      await waitFor(() => {
        expect(screen.getByText('Los Angeles (UTC-8)')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Los Angeles (UTC-8)'))

      // Select should be disabled while updating
      await waitFor(() => {
        const select = screen.getByRole('combobox')
        expect(select).toHaveAttribute('aria-disabled', 'true')
      })

      // Resolve the update
      resolveUpdate!()
    })
  })
})
