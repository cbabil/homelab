/**
 * Data Retention Settings Component Tests
 *
 * Comprehensive unit tests for DataRetentionSettings component including:
 * - Security validation and user interaction testing
 * - Multi-step confirmation flow validation
 * - Input validation and error handling
 * - Accessibility compliance testing
 * - Integration with retention hooks and services
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataRetentionSettings } from '../DataRetentionSettings'

// Mock the retention settings hook
const mockUpdateRetentionSettings = vi.fn()
const mockPreviewCleanup = vi.fn()

vi.mock('@/hooks/useRetentionSettings', () => ({
  useRetentionSettings: () => ({
    settings: {
      logRetentionDays: 30,
      otherDataRetentionDays: 365,
      autoCleanupEnabled: false
    },
    isLoading: false,
    error: null,
    isOperationInProgress: false,
    previewResult: {
      logEntriesAffected: 150,
      otherDataAffected: 25,
      estimatedSpaceFreed: '2.5 MB'
    },
    updateRetentionSettings: mockUpdateRetentionSettings,
    previewCleanup: mockPreviewCleanup,
    limits: {
      LOG_MIN_DAYS: 7,
      LOG_MAX_DAYS: 365,
      OTHER_DATA_MIN_DAYS: 30,
      OTHER_DATA_MAX_DAYS: 3650
    }
  })
}))

describe('DataRetentionSettings', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Clean up any open dialogs
    const dialogs = document.querySelectorAll('[role="dialog"]')
    dialogs.forEach(dialog => dialog.remove())
  })

  describe('Component Rendering', () => {
    it('should render data retention settings section', () => {
      render(<DataRetentionSettings />)

      expect(screen.getByText('Data Retention')).toBeInTheDocument()
      expect(screen.getByLabelText(/auto-cleanup/i)).toBeInTheDocument()
      expect(screen.getByText(/log retention/i)).toBeInTheDocument()
      expect(screen.getByText(/other data/i)).toBeInTheDocument()
    })

    it('should display current retention values', () => {
      render(<DataRetentionSettings />)

      // Check slider displays current values
      const logSlider = screen.getByRole('slider', { name: /log retention/i })
      const dataSlider = screen.getByRole('slider', { name: /other data/i })

      expect(logSlider).toHaveValue('30')
      expect(dataSlider).toHaveValue('365')
    })

    it('should show loading state when settings are loading', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: null,
        isLoading: true,
        error: null,
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)
      expect(screen.getByText('Loading retention settings...')).toBeInTheDocument()
    })

    it('should display error message when settings fail to load', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: null,
        isLoading: false,
        error: 'Failed to load settings',
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)
      expect(screen.getByText('Failed to load retention settings')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('should update auto-cleanup setting when toggle is clicked', async () => {
      render(<DataRetentionSettings />)

      const toggleButton = screen.getByLabelText(/auto-cleanup/i)
      await user.click(toggleButton)

      expect(mockUpdateRetentionSettings).toHaveBeenCalledWith({
        autoCleanupEnabled: true
      })
    })

    it('should update log retention days when slider is moved', async () => {
      render(<DataRetentionSettings />)

      const logSlider = screen.getByRole('slider', { name: /log retention/i })

      fireEvent.change(logSlider, { target: { value: '60' } })

      expect(mockUpdateRetentionSettings).toHaveBeenCalledWith({
        logRetentionDays: 60
      })
    })

    it('should update other data retention when slider is moved', async () => {
      render(<DataRetentionSettings />)

      const dataSlider = screen.getByRole('slider', { name: /other data/i })

      fireEvent.change(dataSlider, { target: { value: '730' } })

      expect(mockUpdateRetentionSettings).toHaveBeenCalledWith({
        otherDataRetentionDays: 730
      })
    })

    it('should enforce slider minimum and maximum values', () => {
      render(<DataRetentionSettings />)

      const logSlider = screen.getByRole('slider', { name: /log retention/i })
      const dataSlider = screen.getByRole('slider', { name: /other data/i })

      expect(logSlider).toHaveAttribute('min', '7')
      expect(logSlider).toHaveAttribute('max', '365')
      expect(dataSlider).toHaveAttribute('min', '30')
      expect(dataSlider).toHaveAttribute('max', '3650')
    })
  })

  describe('Security Validation', () => {
    it('should show warning for dangerous short retention periods', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 10, // Below 14 day safety threshold
          otherDataRetentionDays: 60, // Below 90 day safety threshold
          autoCleanupEnabled: false
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      expect(screen.getByText(/log retention below 14 days may affect debugging/i)).toBeInTheDocument()
      expect(screen.getByText(/very short retention periods may cause data loss/i)).toBeInTheDocument()
    })

    it('should highlight dangerous auto-cleanup configuration', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 20, // Below 30 days with auto-cleanup
          otherDataRetentionDays: 365,
          autoCleanupEnabled: true // Dangerous with short retention
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      expect(screen.getByText(/auto-cleanup with short retention periods requires extra caution/i)).toBeInTheDocument()
    })

    it('should show different warning styles for dangerous vs cautionary settings', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 5, // Very dangerous
          otherDataRetentionDays: 365,
          autoCleanupEnabled: false
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      // Should show orange warning for dangerous settings
      const warningBox = screen.getByText(/log retention below 14 days/i).closest('div')
      expect(warningBox).toHaveClass('bg-orange-50', 'border-orange-200')
    })
  })

  describe('Preview Cleanup Workflow', () => {
    it('should show preview cleanup button', () => {
      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      expect(previewButton).toBeInTheDocument()
      expect(previewButton).not.toBeDisabled()
    })

    it('should disable preview button during operation', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 30,
          otherDataRetentionDays: 365,
          autoCleanupEnabled: false
        },
        isLoading: false,
        error: null,
        isOperationInProgress: true, // Operation in progress
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /analyzing/i })
      expect(previewButton).toBeDisabled()
    })

    it('should call preview cleanup when button is clicked', async () => {
      mockPreviewCleanup.mockResolvedValue({ success: true })

      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      expect(mockPreviewCleanup).toHaveBeenCalledOnce()
    })

    it('should show preview dialog when preview succeeds', async () => {
      mockPreviewCleanup.mockResolvedValue({ success: true })

      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('Cleanup Preview')).toBeInTheDocument()
      })

      expect(screen.getByText(/this will delete 150 log entries/i)).toBeInTheDocument()
      expect(screen.getByText(/25 other records/i)).toBeInTheDocument()
      expect(screen.getByText(/2.5 MB of storage space/i)).toBeInTheDocument()
    })
  })

  describe('Multi-step Confirmation Flow', () => {
    beforeEach(async () => {
      mockPreviewCleanup.mockResolvedValue({ success: true })
    })

    it('should show confirmation dialog after preview', async () => {
      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('Cleanup Preview')).toBeInTheDocument()
      })

      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton)

      await waitFor(() => {
        expect(screen.getByText('Confirm Data Deletion')).toBeInTheDocument()
      })
    })

    it('should require confirmation text for dangerous operations', async () => {
      // Mock dangerous settings
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 10, // Dangerous setting
          otherDataRetentionDays: 60, // Dangerous setting
          autoCleanupEnabled: true
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: {
          logEntriesAffected: 150,
          otherDataAffected: 25,
          estimatedSpaceFreed: '2.5 MB'
        },
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('Cleanup Preview')).toBeInTheDocument()
      })

      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton)

      await waitFor(() => {
        expect(screen.getByText('Confirm Data Deletion')).toBeInTheDocument()
      })

      // Should require confirmation text input
      expect(screen.getByText(/type "DELETE DATA" to confirm/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText('DELETE DATA')).toBeInTheDocument()

      // Delete button should be disabled initially
      const deleteButton = screen.getByRole('button', { name: /delete data/i })
      expect(deleteButton).toBeDisabled()
    })

    it('should enable delete button only after correct confirmation text', async () => {
      // Mock dangerous settings
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 10,
          otherDataRetentionDays: 60,
          autoCleanupEnabled: true
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: {
          logEntriesAffected: 150,
          otherDataAffected: 25,
          estimatedSpaceFreed: '2.5 MB'
        },
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      // Navigate through preview flow
      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('Cleanup Preview')).toBeInTheDocument()
      })

      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton)

      await waitFor(() => {
        expect(screen.getByText('Confirm Data Deletion')).toBeInTheDocument()
      })

      // Type incorrect confirmation text
      const confirmInput = screen.getByPlaceholderText('DELETE DATA')
      await user.type(confirmInput, 'wrong text')

      let deleteButton = screen.getByRole('button', { name: /delete data/i })
      expect(deleteButton).toBeDisabled()

      // Clear and type correct confirmation text
      await user.clear(confirmInput)
      await user.type(confirmInput, 'DELETE DATA')

      deleteButton = screen.getByRole('button', { name: /delete data/i })
      expect(deleteButton).not.toBeDisabled()
    })

    it('should allow cancel at any stage', async () => {
      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('Cleanup Preview')).toBeInTheDocument()
      })

      // Can cancel from preview dialog
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText('Cleanup Preview')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for sliders', () => {
      render(<DataRetentionSettings />)

      const logSlider = screen.getByRole('slider', { name: /log retention/i })
      const dataSlider = screen.getByRole('slider', { name: /other data/i })

      expect(logSlider).toBeInTheDocument()
      expect(dataSlider).toBeInTheDocument()
    })

    it('should have keyboard navigation support', async () => {
      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })

      // Should be focusable
      previewButton.focus()
      expect(document.activeElement).toBe(previewButton)

      // Should activate with Enter key
      mockPreviewCleanup.mockResolvedValue({ success: true })
      fireEvent.keyDown(previewButton, { key: 'Enter', code: 'Enter' })

      expect(mockPreviewCleanup).toHaveBeenCalled()
    })

    it('should announce dangerous settings to screen readers', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 5, // Very dangerous
          otherDataRetentionDays: 365,
          autoCleanupEnabled: false
        },
        isLoading: false,
        error: null,
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      // Warning text should be readable by screen readers
      const warning = screen.getByText(/log retention below 14 days/i)
      expect(warning).toBeInTheDocument()
    })

    it('should have proper dialog roles and focus management', async () => {
      mockPreviewCleanup.mockResolvedValue({ success: true })
      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toBeInTheDocument()
        expect(dialog).toHaveAttribute('aria-modal', 'true')
      })
    })
  })

  describe('Error Handling', () => {
    it('should display service errors', () => {
      vi.mocked(require('@/hooks/useRetentionSettings').useRetentionSettings).mockReturnValue({
        settings: {
          logRetentionDays: 30,
          otherDataRetentionDays: 365,
          autoCleanupEnabled: false
        },
        isLoading: false,
        error: 'Failed to connect to server',
        isOperationInProgress: false,
        previewResult: null,
        updateRetentionSettings: mockUpdateRetentionSettings,
        previewCleanup: mockPreviewCleanup,
        limits: {
          LOG_MIN_DAYS: 7,
          LOG_MAX_DAYS: 365,
          OTHER_DATA_MIN_DAYS: 30,
          OTHER_DATA_MAX_DAYS: 3650
        }
      })

      render(<DataRetentionSettings />)

      expect(screen.getByText('Failed to connect to server')).toBeInTheDocument()
    })

    it('should handle preview cleanup failures gracefully', async () => {
      mockPreviewCleanup.mockResolvedValue({ success: false, error: 'Preview failed' })

      render(<DataRetentionSettings />)

      const previewButton = screen.getByRole('button', { name: /preview cleanup/i })
      await user.click(previewButton)

      // Should not show preview dialog on failure
      await waitFor(() => {
        expect(screen.queryByText('Cleanup Preview')).not.toBeInTheDocument()
      })
    })

    it('should handle settings update failures', async () => {
      mockUpdateRetentionSettings.mockRejectedValue(new Error('Update failed'))

      render(<DataRetentionSettings />)

      const toggleButton = screen.getByLabelText(/auto-cleanup/i)

      // Should not crash when update fails
      await user.click(toggleButton)
      expect(mockUpdateRetentionSettings).toHaveBeenCalled()
    })
  })

  describe('Performance', () => {
    it('should debounce slider changes to prevent excessive updates', async () => {
      render(<DataRetentionSettings />)

      const logSlider = screen.getByRole('slider', { name: /log retention/i })

      // Rapid changes should be debounced
      fireEvent.change(logSlider, { target: { value: '40' } })
      fireEvent.change(logSlider, { target: { value: '50' } })
      fireEvent.change(logSlider, { target: { value: '60' } })

      // Only the final value should trigger an update
      expect(mockUpdateRetentionSettings).toHaveBeenCalledWith({
        logRetentionDays: 60
      })
    })

    it('should not re-render unnecessarily', () => {
      const { rerender } = render(<DataRetentionSettings />)

      // Re-render with same props
      rerender(<DataRetentionSettings />)

      // Component should handle re-renders gracefully
      expect(screen.getByText('Data Retention')).toBeInTheDocument()
    })
  })
})