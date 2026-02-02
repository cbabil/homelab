/**
 * useBackupActions Hook Tests
 *
 * Unit tests for backup export and restore functionality.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useBackupActions } from '../useBackupActions'
import { tomoBackupService } from '@/services/tomoBackupService'
import { useToast } from '@/components/ui/Toast'

// Mock dependencies
vi.mock('@/services/tomoBackupService', () => ({
  tomoBackupService: {
    createBackup: vi.fn(),
    restoreFromFile: vi.fn()
  }
}))

vi.mock('@/components/ui/Toast', () => ({
  useToast: vi.fn()
}))

// Mock MCP Provider
vi.mock('@/providers/MCPProvider', () => ({
  useMCP: () => ({
    client: {
      callTool: vi.fn().mockResolvedValue({ success: true }),
      isConnected: () => true
    },
    isConnected: true,
    error: null
  })
}))

const mockUseToast = vi.mocked(useToast)
const mockBackupService = vi.mocked(tomoBackupService)

describe('useBackupActions', () => {
  let mockAddToast: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockAddToast = vi.fn()
    mockUseToast.mockReturnValue({ addToast: mockAddToast } as any)
  })

  describe('initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useBackupActions())

      expect(result.current.isExporting).toBe(false)
      expect(result.current.isImporting).toBe(false)
      expect(result.current.showRestoreOptions).toBe(false)
      expect(result.current.restoreOptions).toEqual({
        includeSettings: true,
        includeServers: true,
        includeApplications: true,
        overwriteExisting: false
      })
    })
  })

  describe('handleExport', () => {
    it('should export backup successfully', async () => {
      mockBackupService.createBackup.mockResolvedValue({
        success: true,
        filename: 'tomo-backup-2026-01-14.json',
        message: 'Backup created'
      })

      const { result } = renderHook(() => useBackupActions())

      await act(async () => {
        await result.current.handleExport()
      })

      expect(mockBackupService.createBackup).toHaveBeenCalled()
      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'success',
        title: 'Backup Exported',
        message: 'Successfully created backup: tomo-backup-2026-01-14.json',
        duration: 3000
      })
    })

    it('should handle export failure from service', async () => {
      mockBackupService.createBackup.mockResolvedValue({
        success: false,
        filename: '',
        message: 'No data to backup'
      })

      const { result } = renderHook(() => useBackupActions())

      await act(async () => {
        await result.current.handleExport()
      })

      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Export Failed',
        message: 'No data to backup',
        duration: 4000
      })
    })

    it('should handle export exception', async () => {
      mockBackupService.createBackup.mockRejectedValue(new Error('Storage quota exceeded'))

      const { result } = renderHook(() => useBackupActions())

      await act(async () => {
        await result.current.handleExport()
      })

      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Export Failed',
        message: 'Storage quota exceeded',
        duration: 4000
      })
    })

    it('should set isExporting during export', async () => {
      let resolveBackup: (value: any) => void
      mockBackupService.createBackup.mockReturnValue(
        new Promise((resolve) => {
          resolveBackup = resolve
        })
      )

      const { result } = renderHook(() => useBackupActions())

      let exportPromise: Promise<void>
      act(() => {
        exportPromise = result.current.handleExport()
      })

      expect(result.current.isExporting).toBe(true)

      await act(async () => {
        resolveBackup!({ success: true, filename: 'test.json', message: '' })
        await exportPromise!
      })

      expect(result.current.isExporting).toBe(false)
    })
  })

  describe('handleImport', () => {
    it('should show restore options on first call', async () => {
      const { result } = renderHook(() => useBackupActions())

      await act(async () => {
        await result.current.handleImport()
      })

      expect(result.current.showRestoreOptions).toBe(true)
      expect(mockBackupService.restoreFromFile).not.toHaveBeenCalled()
    })

    it('should restore backup on second call', async () => {
      mockBackupService.restoreFromFile.mockResolvedValue({
        success: true,
        message: 'Restored',
        restored: {
          settings: true,
          servers: 2,
          applications: 3
        },
        skipped: {
          servers: 0,
          applications: 0
        },
        errors: []
      })

      const { result } = renderHook(() => useBackupActions())

      // First call - show options
      await act(async () => {
        await result.current.handleImport()
      })

      expect(result.current.showRestoreOptions).toBe(true)

      // Second call - perform restore
      await act(async () => {
        await result.current.handleImport()
      })

      expect(mockBackupService.restoreFromFile).toHaveBeenCalledWith(
        expect.anything(), // mcpClient
        expect.anything(), // existingServers
        {
          includeSettings: true,
          includeServers: true,
          includeApplications: true,
          overwriteExisting: false
        }
      )

      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'success',
        title: 'Backup Restored',
        message: 'Successfully restored: Settings, 2 servers, 3 apps',
        duration: 4000
      })
    })

    it('should handle restore failure', async () => {
      mockBackupService.restoreFromFile.mockResolvedValue({
        success: false,
        message: 'Invalid backup format',
        restored: { settings: false, servers: 0, applications: 0 },
        skipped: { servers: 0, applications: 0 },
        errors: ['Invalid backup format']
      })

      const { result } = renderHook(() => useBackupActions())

      // First call - show options
      await act(async () => {
        await result.current.handleImport()
      })

      // Second call - perform restore
      await act(async () => {
        await result.current.handleImport()
      })

      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Restore Failed',
        message: 'Invalid backup format',
        duration: 4000
      })
    })

    it('should handle restore exception', async () => {
      mockBackupService.restoreFromFile.mockRejectedValue(new Error('File not found'))

      const { result } = renderHook(() => useBackupActions())

      // First call - show options
      await act(async () => {
        await result.current.handleImport()
      })

      // Second call - perform restore
      await act(async () => {
        await result.current.handleImport()
      })

      expect(mockAddToast).toHaveBeenCalledWith({
        type: 'error',
        title: 'Import Failed',
        message: 'File not found',
        duration: 4000
      })
    })

    it('should set isImporting during restore', async () => {
      let resolveRestore: (value: any) => void
      mockBackupService.restoreFromFile.mockReturnValue(
        new Promise((resolve) => {
          resolveRestore = resolve
        })
      )

      const { result } = renderHook(() => useBackupActions())

      // Show options first
      await act(async () => {
        await result.current.handleImport()
      })

      let importPromise: Promise<void>
      act(() => {
        importPromise = result.current.handleImport()
      })

      expect(result.current.isImporting).toBe(true)

      await act(async () => {
        resolveRestore!({
          success: true,
          message: '',
          restored: { settings: true, servers: 0, applications: 0 },
          skipped: { servers: 0, applications: 0 },
          errors: []
        })
        await importPromise!
      })

      expect(result.current.isImporting).toBe(false)
    })
  })

  describe('resetRestoreOptions', () => {
    it('should reset restore options to defaults', async () => {
      const { result } = renderHook(() => useBackupActions())

      // Show options and modify them
      await act(async () => {
        await result.current.handleImport()
      })

      act(() => {
        result.current.setRestoreOptions({
          includeSettings: false,
          includeServers: false,
          includeApplications: true,
          overwriteExisting: true
        })
      })

      expect(result.current.showRestoreOptions).toBe(true)
      expect(result.current.restoreOptions.includeSettings).toBe(false)

      // Reset
      act(() => {
        result.current.resetRestoreOptions()
      })

      expect(result.current.showRestoreOptions).toBe(false)
      expect(result.current.restoreOptions).toEqual({
        includeSettings: true,
        includeServers: true,
        includeApplications: true,
        overwriteExisting: false
      })
    })
  })

  describe('setRestoreOptions', () => {
    it('should update restore options', () => {
      const { result } = renderHook(() => useBackupActions())

      act(() => {
        result.current.setRestoreOptions({
          includeSettings: true,
          includeServers: false,
          includeApplications: false,
          overwriteExisting: true
        })
      })

      expect(result.current.restoreOptions).toEqual({
        includeSettings: true,
        includeServers: false,
        includeApplications: false,
        overwriteExisting: true
      })
    })
  })
})
