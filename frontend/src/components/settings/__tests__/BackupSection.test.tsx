/**
 * BackupSection Test Suite
 *
 * Tests for the BackupSection component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BackupSection } from '../BackupSection'

// Mock the useBackupActions hook
vi.mock('@/hooks/useBackupActions', () => ({
  useBackupActions: vi.fn()
}))

import { useBackupActions } from '@/hooks/useBackupActions'
const mockUseBackupActions = vi.mocked(useBackupActions)

describe('BackupSection', () => {
  const defaultMockValues = {
    isExporting: false,
    isImporting: false,
    showRestoreOptions: false,
    restoreOptions: {
      includeSettings: true,
      includeServers: true,
      includeApplications: true,
      overwriteExisting: false
    },
    setRestoreOptions: vi.fn(),
    handleExport: vi.fn(),
    handleImport: vi.fn(),
    resetRestoreOptions: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseBackupActions.mockReturnValue(defaultMockValues)
  })

  describe('Rendering', () => {
    it('should render section title', () => {
      render(<BackupSection />)

      expect(screen.getByText('Data Backup')).toBeInTheDocument()
    })

    it('should render section description', () => {
      render(<BackupSection />)

      expect(
        screen.getByText('Backup or restore all settings, servers, and apps')
      ).toBeInTheDocument()
    })

    it('should render export button', () => {
      render(<BackupSection />)

      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    it('should render import button', () => {
      render(<BackupSection />)

      expect(screen.getByText('Import')).toBeInTheDocument()
    })
  })

  describe('Export Functionality', () => {
    it('should call handleExport when export button clicked', async () => {
      const user = userEvent.setup()
      const handleExport = vi.fn()
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        handleExport
      })

      render(<BackupSection />)

      await user.click(screen.getByText('Export'))

      expect(handleExport).toHaveBeenCalled()
    })

    it('should show exporting state', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        isExporting: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
    })

    it('should disable export button when exporting', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        isExporting: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Exporting...').closest('button')).toBeDisabled()
    })
  })

  describe('Import Functionality', () => {
    it('should call handleImport when import button clicked', async () => {
      const user = userEvent.setup()
      const handleImport = vi.fn()
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        handleImport
      })

      render(<BackupSection />)

      await user.click(screen.getByText('Import'))

      expect(handleImport).toHaveBeenCalled()
    })

    it('should show importing state', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        isImporting: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Importing...')).toBeInTheDocument()
    })

    it('should disable import button when importing', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        isImporting: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Importing...').closest('button')).toBeDisabled()
    })

    it('should disable import button when exporting', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        isExporting: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Import').closest('button')).toBeDisabled()
    })
  })

  describe('Restore Options', () => {
    it('should not show restore options by default', () => {
      render(<BackupSection />)

      expect(screen.queryByText('Import Options')).not.toBeInTheDocument()
    })

    it('should show restore options when showRestoreOptions is true', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        showRestoreOptions: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Import Options')).toBeInTheDocument()
    })

    it('should show cancel button when restore options visible', () => {
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        showRestoreOptions: true
      })

      render(<BackupSection />)

      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })

    it('should call resetRestoreOptions when cancel clicked', async () => {
      const user = userEvent.setup()
      const resetRestoreOptions = vi.fn()
      mockUseBackupActions.mockReturnValue({
        ...defaultMockValues,
        showRestoreOptions: true,
        resetRestoreOptions
      })

      render(<BackupSection />)

      await user.click(screen.getByText('Cancel'))

      expect(resetRestoreOptions).toHaveBeenCalled()
    })
  })
})
