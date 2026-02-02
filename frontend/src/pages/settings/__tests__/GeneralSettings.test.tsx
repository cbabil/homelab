/**
 * GeneralSettings Test Suite
 *
 * Tests for the GeneralSettings component including
 * language, timezone, and application settings.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

// Store mock implementations in a mutable object
const { mocks } = vi.hoisted(() => {
  const mocks = {
    updateSettings: vi.fn(),
    settings: {
      ui: {
        language: 'en',
        refreshRate: 60,
        defaultPage: 'dashboard'
      }
    }
  }
  return { mocks }
})

// Mock SettingsProvider
vi.mock('@/providers/SettingsProvider', () => ({
  useSettingsContext: () => ({
    settings: mocks.settings,
    updateSettings: mocks.updateSettings
  })
}))

// Mock SettingsSavingContext
vi.mock('../SettingsSavingContext', () => ({
  useSettingsSaving: () => ({
    isSaving: false,
    setIsSaving: vi.fn()
  })
}))

// Mock TimezoneDropdown
vi.mock('@/components/settings/TimezoneDropdown', () => ({
  TimezoneDropdown: () => <div data-testid="timezone-dropdown">Timezone</div>
}))

import { GeneralSettings } from '../GeneralSettings'

describe('GeneralSettings', () => {
  beforeEach(() => {
    mocks.updateSettings = vi.fn()
    mocks.settings = {
      ui: {
        language: 'en',
        refreshRate: 60,
        defaultPage: 'dashboard'
      }
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render language & region section', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText('Language & Region')).toBeInTheDocument()
      })

      expect(screen.getByText('Language')).toBeInTheDocument()
      // Timezone appears twice (label + component), use getAllByText
      expect(screen.getAllByText('Timezone').length).toBeGreaterThan(0)
    })

    it('should render application section', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText('Application')).toBeInTheDocument()
      })

      expect(screen.getByText('Auto-refresh interval')).toBeInTheDocument()
      expect(screen.getByText('Default page')).toBeInTheDocument()
    })
  })

  describe('UI Structure', () => {
    it('should have language dropdown with options', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText('Language')).toBeInTheDocument()
      })

      // MUI Select renders a combobox
      const selects = screen.getAllByRole('combobox')
      expect(selects.length).toBeGreaterThan(0)
    })

    it('should render timezone dropdown component', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByTestId('timezone-dropdown')).toBeInTheDocument()
      })
    })

    it('should render auto-refresh dropdown', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText('Auto-refresh interval')).toBeInTheDocument()
      })

      // Verify the description is shown
      expect(screen.getByText('How often to refresh dashboard data')).toBeInTheDocument()
    })

    it('should render default page dropdown', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText('Default page')).toBeInTheDocument()
      })

      // Verify the description is shown
      expect(screen.getByText('Page to show after login')).toBeInTheDocument()
    })
  })

  describe('Settings Descriptions', () => {
    it('should have language description', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText(/Display language for the interface/i)).toBeInTheDocument()
      })
    })

    it('should have language region description', async () => {
      render(<GeneralSettings />)

      await waitFor(() => {
        expect(screen.getByText(/Configure display language and regional preferences/i)).toBeInTheDocument()
      })
    })
  })
})
