/**
 * useApplications Hook Tests
 *
 * Unit tests for the applications management hook including
 * fetching, filtering, and state management.
 */

import { describe, it, expect, beforeEach, vi, Mock } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useApplications } from '../useApplications'
import { useApplicationsService } from '../useDataServices'
import { useApplicationFilter } from '../useApplicationFilter'
import { useApplicationOperations } from '../useApplicationOperations'

// Mock dependencies
vi.mock('../useDataServices')
vi.mock('../useApplicationFilter')
vi.mock('../useApplicationOperations')
vi.mock('@/services/systemLogger', () => ({
  applicationLogger: {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn()
  }
}))

const mockUseApplicationsService = vi.mocked(useApplicationsService)
const mockUseApplicationFilter = vi.mocked(useApplicationFilter)
const mockUseApplicationOperations = vi.mocked(useApplicationOperations)

const mockApps = [
  {
    id: 'plex',
    name: 'Plex',
    description: 'Media server',
    version: '1.0.0',
    category: { id: 'media', name: 'Media', description: 'Media apps', icon: 'tv' as any, color: 'blue' },
    tags: ['media', 'streaming'],
    icon: 'plex.png',
    author: 'Plex Inc',
    license: 'Proprietary',
    requirements: {},
    status: 'available' as const,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  },
  {
    id: 'jellyfin',
    name: 'Jellyfin',
    description: 'Free media system',
    version: '10.8.0',
    category: { id: 'media', name: 'Media', description: 'Media apps', icon: 'tv' as any, color: 'blue' },
    tags: ['media', 'streaming'],
    icon: 'jellyfin.png',
    author: 'Jellyfin Team',
    license: 'GPL',
    requirements: {},
    status: 'installed' as const,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  },
  {
    id: 'nextcloud',
    name: 'Nextcloud',
    description: 'Cloud storage',
    version: '25.0.0',
    category: { id: 'productivity', name: 'Productivity', description: 'Productivity apps', icon: 'folder' as any, color: 'green' },
    tags: ['storage', 'cloud'],
    icon: 'nextcloud.png',
    author: 'Nextcloud GmbH',
    license: 'AGPL',
    requirements: {},
    status: 'available' as const,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  }
]

describe('useApplications', () => {
  let mockApplicationsService: {
    search: Mock
    install: Mock
    uninstall: Mock
  }

  beforeEach(() => {
    vi.clearAllMocks()

    mockApplicationsService = {
      search: vi.fn(),
      install: vi.fn(),
      uninstall: vi.fn()
    }

    mockUseApplicationsService.mockReturnValue({
      applicationsService: mockApplicationsService as any,
      isConnected: true
    })

    mockUseApplicationFilter.mockReturnValue({
      currentFilter: {},
      setFilter: vi.fn(),
      updateFilter: vi.fn(),
      sanitizeFilter: vi.fn((filter) => filter)
    })

    mockUseApplicationOperations.mockReturnValue({
      addApplication: vi.fn(),
      updateApplication: vi.fn(),
      deleteApplication: vi.fn(),
      installApplication: vi.fn(),
      removeApplications: vi.fn(),
      uninstallApplication: vi.fn(),
      uninstallApplications: vi.fn()
    })
  })

  describe('initialization', () => {
    it('should initialize with empty state', async () => {
      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: [], total: 0 }
      })

      const { result } = renderHook(() => useApplications())

      expect(result.current.apps).toEqual([])
      expect(result.current.categories).toEqual([])
      expect(result.current.error).toBeNull()
    })

    it('should fetch applications on mount when connected', async () => {
      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: mockApps, total: 3 }
      })

      const { result } = renderHook(() => useApplications())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(mockApplicationsService.search).toHaveBeenCalled()
      expect(result.current.apps).toEqual(mockApps)
    })

    it('should not fetch when not connected', async () => {
      mockUseApplicationsService.mockReturnValue({
        applicationsService: mockApplicationsService as any,
        isConnected: false
      })

      renderHook(() => useApplications())

      expect(mockApplicationsService.search).not.toHaveBeenCalled()
    })
  })

  describe('fetching applications', () => {
    it('should set loading state during fetch', async () => {
      let resolveSearch: (value: any) => void
      mockApplicationsService.search.mockReturnValue(
        new Promise((resolve) => {
          resolveSearch = resolve
        })
      )

      const { result } = renderHook(() => useApplications())

      // Should be loading initially
      expect(result.current.isLoading).toBe(true)

      // Resolve the search
      await act(async () => {
        resolveSearch!({ success: true, data: { apps: mockApps, total: 3 } })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('should derive categories from apps', async () => {
      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: mockApps, total: 3 }
      })

      const { result } = renderHook(() => useApplications())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.categories).toHaveLength(2)
      expect(result.current.categories.map((c) => c.id)).toContain('media')
      expect(result.current.categories.map((c) => c.id)).toContain('productivity')
    })

    it('should handle fetch error', async () => {
      mockApplicationsService.search.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useApplications())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Network error')
      expect(result.current.apps).toEqual([])
    })

    it('should handle unsuccessful response', async () => {
      mockApplicationsService.search.mockResolvedValue({
        success: false,
        error: 'Service unavailable'
      })

      const { result } = renderHook(() => useApplications())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Service unavailable')
      expect(result.current.apps).toEqual([])
    })
  })

  describe('refresh', () => {
    it('should refetch applications when refresh is called', async () => {
      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: mockApps, total: 3 }
      })

      const { result } = renderHook(() => useApplications())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const callCount = mockApplicationsService.search.mock.calls.length

      await act(async () => {
        result.current.refresh()
      })

      await waitFor(() => {
        expect(mockApplicationsService.search.mock.calls.length).toBeGreaterThan(callCount)
      })
    })
  })

  describe('filter integration', () => {
    it('should expose filter state from useApplicationFilter', async () => {
      const mockSetFilter = vi.fn()
      const mockUpdateFilter = vi.fn()

      mockUseApplicationFilter.mockReturnValue({
        currentFilter: { search: 'plex', category: 'media', status: 'installed' },
        setFilter: mockSetFilter,
        updateFilter: mockUpdateFilter,
        sanitizeFilter: vi.fn((filter) => filter)
      })

      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: [], total: 0 }
      })

      const { result } = renderHook(() => useApplications())

      expect(result.current.filter).toEqual({
        search: 'plex',
        category: 'media',
        status: 'installed'
      })
      expect(result.current.setFilter).toBe(mockSetFilter)
      expect(result.current.updateFilter).toBe(mockUpdateFilter)
    })
  })

  describe('operations integration', () => {
    it('should expose operations from useApplicationOperations', async () => {
      const mockAddApplication = vi.fn()
      const mockInstallApplication = vi.fn()
      const mockUninstallApplication = vi.fn()
      const mockRemoveApplications = vi.fn()

      mockUseApplicationOperations.mockReturnValue({
        addApplication: mockAddApplication,
        updateApplication: vi.fn(),
        deleteApplication: vi.fn(),
        installApplication: mockInstallApplication,
        removeApplications: mockRemoveApplications,
        uninstallApplication: mockUninstallApplication,
        uninstallApplications: vi.fn()
      })

      mockApplicationsService.search.mockResolvedValue({
        success: true,
        data: { apps: [], total: 0 }
      })

      const { result } = renderHook(() => useApplications())

      expect(result.current.addApplication).toBe(mockAddApplication)
      expect(result.current.installApplication).toBe(mockInstallApplication)
      expect(result.current.uninstallApplication).toBe(mockUninstallApplication)
      expect(result.current.removeApplications).toBe(mockRemoveApplications)
    })
  })
})
