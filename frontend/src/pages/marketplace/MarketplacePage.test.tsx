/**
 * MarketplacePage Test Suite
 *
 * Tests for MarketplacePage component including rendering,
 * search functionality, tab navigation, and i18n translations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { MarketplacePage } from './MarketplacePage'

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Setup hoisted mocks
const { mockApps, mockCategories, mockRepos, mockAddToast, mockUser, mockServers } =
  vi.hoisted(() => {
    const mockApps = [
      {
        id: 'app-1',
        name: 'Test App 1',
        version: '1.0.0',
        description: 'Test application description',
        category: 'Development',
        icon: 'https://example.com/icon.png',
        author: 'Test Author',
        license: 'MIT',
        maintainers: ['Maintainer 1'],
        repoId: 'repo-1'
      },
      {
        id: 'app-2',
        name: 'Test App 2',
        version: '2.0.0',
        description: 'Another test application',
        category: 'Productivity',
        icon: null,
        author: 'Another Author',
        license: 'Apache-2.0',
        maintainers: [],
        repoId: 'repo-1'
      }
    ]

    const mockCategories = [
      { id: 'development', name: 'Development', count: 5 },
      { id: 'productivity', name: 'Productivity', count: 3 }
    ]

    const mockRepos = [
      {
        id: 'repo-1',
        name: 'Official Repo',
        url: 'https://github.com/official/repo',
        branch: 'main',
        repoType: 'official',
        enabled: true,
        appCount: 2,
        status: 'active'
      }
    ]

    const mockAddToast = vi.fn()
    const mockUser = { id: 1, username: 'testuser', role: 'admin' }
    const mockServers = [{ id: 'server-1', name: 'Test Server', host: 'localhost' }]

    return {
      mockApps,
      mockCategories,
      mockRepos,
      mockAddToast,
      mockUser,
      mockServers
    }
  })

// Mock marketplace service
vi.mock('@/services/marketplaceService', () => ({
  getCategories: vi.fn().mockResolvedValue(mockCategories),
  getTrendingApps: vi.fn().mockResolvedValue(mockApps),
  searchApps: vi.fn().mockResolvedValue({ apps: mockApps }),
  getRepos: vi.fn().mockResolvedValue(mockRepos),
  addRepo: vi.fn(),
  syncRepo: vi.fn(),
  removeRepo: vi.fn()
}))

// Mock providers
vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({ addToast: mockAddToast })
}))

vi.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ user: mockUser })
}))

vi.mock('@/hooks/useServers', () => ({
  useServers: () => ({ servers: mockServers })
}))

vi.mock('@/hooks/useDeploymentModal', () => ({
  useDeploymentModal: () => ({
    isOpen: false,
    selectedApp: null,
    step: 'select-servers',
    selectedServerIds: [],
    isDeploying: false,
    error: null,
    deploymentResult: null,
    installationStatus: {},
    targetServerStatuses: {},
    openModalForMarketplace: vi.fn(),
    closeModal: vi.fn(),
    setStep: vi.fn(),
    setSelectedServerIds: vi.fn(),
    deploy: vi.fn(),
    retryDeployment: vi.fn(),
    cleanup: vi.fn()
  })
}))

// Mock DeploymentModal
vi.mock('@/components/deployment/DeploymentModal', () => ({
  DeploymentModal: () => null
}))

// Mock RepoManager
vi.mock('./RepoManager', () => ({
  RepoManager: vi.fn().mockImplementation(() => <div data-testid="repo-manager" />)
}))

function renderMarketplacePage() {
  return render(
    <BrowserRouter>
      <MarketplacePage />
    </BrowserRouter>
  )
}

describe('MarketplacePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering and UI', () => {
    it('should render marketplace page with title', async () => {
      renderMarketplacePage()

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Marketplace' })).toBeInTheDocument()
      })
    })

    it('should render browse and repos tabs', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /browse apps/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /manage repos/i })).toBeInTheDocument()
      })
    })

    it('should render search input', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search apps/i)).toBeInTheDocument()
      })
    })

    it('should display app count when apps are loaded', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        // Uses translation "allApps"
        expect(screen.getByText(/All Apps \(2\)/i)).toBeInTheDocument()
      })
    })
  })

  describe('Tab Navigation', () => {
    it('should switch to repos tab when clicked', async () => {
      const user = userEvent.setup()
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /manage repos/i })).toBeInTheDocument()
      })

      const reposTab = screen.getByRole('tab', { name: /manage repos/i })
      await user.click(reposTab)

      await waitFor(() => {
        expect(screen.getByTestId('repo-manager')).toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('should update search query when typing', async () => {
      const user = userEvent.setup()
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search apps/i)).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/search apps/i)
      await user.type(searchInput, 'Test')

      expect(searchInput).toHaveValue('Test')
    })
  })

  describe('App Cards', () => {
    it('should render app cards with names', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByText('Test App 1')).toBeInTheDocument()
        expect(screen.getByText('Test App 2')).toBeInTheDocument()
      })
    })

    it('should render app versions', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByText('v1.0.0')).toBeInTheDocument()
        expect(screen.getByText('v2.0.0')).toBeInTheDocument()
      })
    })

    it('should render app categories', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        expect(screen.getByText('Development')).toBeInTheDocument()
        expect(screen.getByText('Productivity')).toBeInTheDocument()
      })
    })
  })

  describe('i18n Translations', () => {
    it('should use translated page title', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        // "Marketplace" comes from translations
        expect(screen.getByRole('heading', { name: 'Marketplace' })).toBeInTheDocument()
      })
    })

    it('should use translated tab labels', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        // Tab labels from translations
        expect(screen.getByRole('tab', { name: 'Browse Apps' })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: 'Manage Repos' })).toBeInTheDocument()
      })
    })

    it('should use translated search placeholder', async () => {
      renderMarketplacePage()

      await waitFor(() => {
        // Placeholder from translations
        expect(screen.getByPlaceholderText('Search apps...')).toBeInTheDocument()
      })
    })
  })
})
