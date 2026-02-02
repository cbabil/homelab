/**
 * ThemeSwitcher Test Suite
 *
 * Tests for the ThemeSwitcher component including rendering,
 * theme toggling, and accessibility.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeSwitcher } from '../ThemeSwitcher'

// Mock the ThemeProvider
const mockSetTheme = vi.fn()
let mockTheme = 'dark'

vi.mock('@/providers/ThemeProvider', () => ({
  useTheme: () => ({
    theme: mockTheme,
    setTheme: mockSetTheme
  })
}))

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockTheme = 'dark'
  })

  describe('Rendering', () => {
    it('should render theme toggle button', () => {
      render(<ThemeSwitcher />)

      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should show Sun icon in dark mode', () => {
      mockTheme = 'dark'
      render(<ThemeSwitcher />)

      // Button should exist with title for light mode switch
      expect(screen.getByTitle('Switch to light mode')).toBeInTheDocument()
    })

    it('should show Moon icon in light mode', () => {
      mockTheme = 'light'
      render(<ThemeSwitcher />)

      // Button should exist with title for dark mode switch
      expect(screen.getByTitle('Switch to dark mode')).toBeInTheDocument()
    })
  })

  describe('Theme Toggling', () => {
    it('should call setTheme with light when in dark mode', async () => {
      const user = userEvent.setup()
      mockTheme = 'dark'
      render(<ThemeSwitcher />)

      await user.click(screen.getByRole('button'))

      expect(mockSetTheme).toHaveBeenCalledWith('light')
    })

    it('should call setTheme with dark when in light mode', async () => {
      const user = userEvent.setup()
      mockTheme = 'light'
      render(<ThemeSwitcher />)

      await user.click(screen.getByRole('button'))

      expect(mockSetTheme).toHaveBeenCalledWith('dark')
    })
  })

  describe('Accessibility', () => {
    it('should have descriptive title in dark mode', () => {
      mockTheme = 'dark'
      render(<ThemeSwitcher />)

      expect(screen.getByTitle('Switch to light mode')).toBeInTheDocument()
    })

    it('should have descriptive title in light mode', () => {
      mockTheme = 'light'
      render(<ThemeSwitcher />)

      expect(screen.getByTitle('Switch to dark mode')).toBeInTheDocument()
    })

    it('should be keyboard focusable', async () => {
      const user = userEvent.setup()
      render(<ThemeSwitcher />)

      await user.tab()

      expect(screen.getByRole('button')).toHaveFocus()
    })
  })
})
