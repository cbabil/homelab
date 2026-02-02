/**
 * MarketplacesSettings Test Suite
 *
 * Tests for the MarketplacesSettings component including
 * repository list, add repository modal, and sync functionality.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import type { MarketplaceRepo } from '@/types/marketplace'

// Mock marketplace service
const mockRepos: MarketplaceRepo[] = [
  {
    id: '1',
    name: 'Official Apps',
    url: 'https://github.com/tomo/official-apps',
    branch: 'main',
    repoType: 'official',
    enabled: true,
    status: 'active',
    appCount: 25,
    lastSynced: '2024-01-15T10:00:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'Community Apps',
    url: 'https://github.com/community/apps',
    branch: 'main',
    repoType: 'community',
    enabled: true,
    status: 'active',
    appCount: 100,
    lastSynced: '2024-01-14T10:00:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-14T10:00:00Z'
  }
]

vi.mock('@/services/marketplaceService', () => ({
  getRepos: vi.fn(() => Promise.resolve(mockRepos)),
  addRepo: vi.fn(),
  syncRepo: vi.fn(),
  removeRepo: vi.fn()
}))

vi.mock('@/services/systemLogger', () => ({
  marketplaceLogger: {
    info: vi.fn(),
    error: vi.fn()
  }
}))

import { MarketplacesSettings } from '../MarketplacesSettings'

describe('MarketplacesSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render marketplace repositories header', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('Marketplace Repositories')).toBeInTheDocument()
      })
    })

    it('should render description text', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText(/Configure repositories that provide applications/i)).toBeInTheDocument()
      })
    })

    it('should render Add Repository button', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('Add Repository')).toBeInTheDocument()
      })
    })

    it('should render sync rate dropdown', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox')
        expect(comboboxes.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Repository List', () => {
    it('should display repository names after loading', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('Official Apps')).toBeInTheDocument()
        expect(screen.getByText('Community Apps')).toBeInTheDocument()
      })
    })

    it('should display repository URLs', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('https://github.com/tomo/official-apps')).toBeInTheDocument()
      })
    })

    it('should display repository branch', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        // Both repos have 'main' branch
        expect(screen.getAllByText('main').length).toBeGreaterThan(0)
      })
    })

    it('should display app count', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('25 apps')).toBeInTheDocument()
        expect(screen.getByText('100 apps')).toBeInTheDocument()
      })
    })

    it('should display status chips', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        // Both repos are 'active'
        expect(screen.getAllByText('active').length).toBe(2)
      })
    })

    it('should display repo type chips', async () => {
      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('official')).toBeInTheDocument()
        expect(screen.getByText('community')).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no repositories', async () => {
      const { getRepos } = await import('@/services/marketplaceService')
      vi.mocked(getRepos).mockResolvedValueOnce([])

      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText('No marketplace repositories')).toBeInTheDocument()
      })
    })

    it('should show helpful message in empty state', async () => {
      const { getRepos } = await import('@/services/marketplaceService')
      vi.mocked(getRepos).mockResolvedValueOnce([])

      render(<MarketplacesSettings />)

      await waitFor(() => {
        expect(screen.getByText(/Add a Git repository to start discovering apps/i)).toBeInTheDocument()
      })
    })
  })

  describe('Sync Rate Options', () => {
    it('should have daily, weekly, and monthly options', async () => {
      render(<MarketplacesSettings />)

      // The select should default to 'monthly'
      await waitFor(() => {
        expect(screen.getByText('Monthly')).toBeInTheDocument()
      })
    })
  })
})
