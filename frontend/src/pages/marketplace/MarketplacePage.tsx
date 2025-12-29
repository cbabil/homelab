/**
 * Marketplace Page Component
 *
 * Browse and manage marketplace repositories and applications.
 * Features tab navigation, search, filtering, and showcases featured/trending apps.
 */

import { useEffect, useState, useMemo } from 'react'
import { TrendingUp, Package, Filter } from 'lucide-react'
import { Tabs, Search, Dropdown, EmptyState, Alert, Typography, Button, Carousel, Pagination, type DropdownOption } from 'ui-toolkit'
import { useToast } from '@/components/ui/Toast'
import type { MarketplaceApp, MarketplaceCategory, SearchFilters } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { RepoManager } from './RepoManager'
import { MarketplaceAppCard } from './MarketplaceAppCard'
import { marketplaceLogger } from '@/services/systemLogger'
import { useAuth } from '@/providers/AuthProvider'

type TabType = 'browse' | 'repos'

const tabItems = [
  { label: 'Browse Apps', value: 'browse' },
  { label: 'Manage Repos', value: 'repos' }
]

const ITEMS_PER_PAGE = 12

export function MarketplacePage() {
  const [activeTab, setActiveTab] = useState<TabType>('browse')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [showFilters, setShowFilters] = useState(false)
  const [categories, setCategories] = useState<MarketplaceCategory[]>([])
  const [featuredApps, setFeaturedApps] = useState<MarketplaceApp[]>([])
  const [trendingApps, setTrendingApps] = useState<MarketplaceApp[]>([])
  const [allApps, setAllApps] = useState<MarketplaceApp[]>([])
  const [searchResults, setSearchResults] = useState<MarketplaceApp[]>([])
  const [importedAppIds, setImportedAppIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const { addToast } = useToast()
  const { user } = useAuth()

  // Load initial data
  useEffect(() => {
    loadInitialData()
  }, [])

  // Show toast and log errors
  useEffect(() => {
    if (error) {
      addToast({ type: 'error', title: error })
      marketplaceLogger.error(error)
    }
  }, [error, addToast])

  // Search when filters change
  useEffect(() => {
    if (activeTab === 'browse') {
      performSearch()
    }
  }, [searchQuery, selectedCategory, activeTab])

  // Reset page when search/filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCategory])

  const loadInitialData = async () => {
    setIsLoading(true)
    setError(null)
    marketplaceLogger.info('Loading marketplace data')

    try {
      const [categoriesData, featuredData, trendingData, allAppsData, importedIds] = await Promise.all([
        marketplaceService.getCategories(),
        marketplaceService.getFeaturedApps(6),
        marketplaceService.getTrendingApps(6),
        marketplaceService.searchApps({ sortBy: 'name' }),
        marketplaceService.getImportedAppIds()
      ])

      setCategories(categoriesData)
      setFeaturedApps(featuredData)
      setTrendingApps(trendingData)
      setAllApps(allAppsData.apps)
      setImportedAppIds(new Set(importedIds))
      marketplaceLogger.info(`Loaded ${allAppsData.apps.length} apps from marketplace`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load marketplace data'
      setError(errorMsg)
      marketplaceLogger.error(errorMsg)
    } finally {
      setIsLoading(false)
    }
  }

  const performSearch = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const filters: SearchFilters = {
        search: searchQuery || undefined,
        category: selectedCategory,
        sortBy: 'name'
      }

      const result = await marketplaceService.searchApps(filters)
      setSearchResults(result.apps)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search apps')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
  }

  const handleCategoryChange = (categoryId: string | undefined) => {
    setSelectedCategory(categoryId)
    setShowFilters(false)
  }

  const handleImportApp = async (app: MarketplaceApp) => {
    if (!user) {
      addToast({ type: 'error', title: 'Please log in to import apps' })
      return
    }

    if (importedAppIds.has(app.id)) {
      addToast({ type: 'info', title: `${app.name} is already imported` })
      return
    }

    try {
      marketplaceLogger.info(`Importing app: ${app.name}`)
      await marketplaceService.importApp(app.id, user.id)
      setImportedAppIds(prev => new Set([...prev, app.id]))
      addToast({ type: 'success', title: `${app.name} imported successfully` })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to import app'
      addToast({ type: 'error', title: errorMsg })
    }
  }

  // Determine which apps to display
  const displayApps = (searchQuery || selectedCategory) ? searchResults : allApps
  const totalApps = displayApps.length
  const totalPages = Math.ceil(totalApps / ITEMS_PER_PAGE)

  // Paginated apps
  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return displayApps.slice(start, start + ITEMS_PER_PAGE)
  }, [displayApps, currentPage])

  // Build dropdown options from categories
  const categoryOptions: DropdownOption[] = [
    { label: 'All Categories', value: '' },
    ...categories.map((cat) => ({
      label: `${cat.name} (${cat.count})`,
      value: cat.id
    }))
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header Row: Title + Tabs + Search */}
      <div className="flex flex-col lg:flex-row lg:items-center gap-3 mb-4">
        <div className="shrink-0 mr-4">
          <Typography variant="h2">Marketplace</Typography>
        </div>

        <Tabs
          items={tabItems}
          active={activeTab}
          onChange={(value) => setActiveTab(value as TabType)}
          variant="underline"
        />

        {activeTab === 'browse' && (
          <div className="flex gap-2 lg:ml-auto items-center">
            <Search
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search apps..."
            />
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                className="p-2"
              >
                <Filter className="h-4 w-4" />
              </Button>
              {showFilters && (
                <div className="absolute right-0 top-full mt-1 z-20 bg-popover border border-border rounded-lg shadow-lg p-2 min-w-[200px]">
                  <p className="text-xs text-muted-foreground mb-2 px-2">Category</p>
                  {categoryOptions.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleCategoryChange(opt.value || undefined)}
                      className={`w-full text-left px-2 py-1.5 text-sm rounded hover:bg-muted ${selectedCategory === opt.value || (!selectedCategory && !opt.value) ? 'bg-primary/10 text-primary' : ''}`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Browse Apps Tab */}
      {activeTab === 'browse' && (
        <div className="flex-1 overflow-auto space-y-4">
          {/* Trending Apps Carousel */}
          {!searchQuery && !selectedCategory && (trendingApps.length > 0 || allApps.length > 0) && (
            <section className="px-4">
              <Typography variant="small" muted className="flex items-center gap-1.5 mb-2 font-semibold">
                <TrendingUp className="h-4 w-4 text-green-500" />
                Trending
              </Typography>
              <Carousel gap={8}>
                {(trendingApps.length > 0 ? trendingApps : allApps.slice(0, 10)).map((app) => (
                  <div key={app.id} className="w-[100px]">
                    <MarketplaceAppCard app={app} onImport={handleImportApp} isImported={importedAppIds.has(app.id)} />
                  </div>
                ))}
              </Carousel>
            </section>
          )}

          {/* All Apps */}
          {totalApps > 0 && (
            <section>
              <Typography variant="small" muted className="mb-6 font-semibold">
                {searchQuery || selectedCategory ? `${totalApps} ${totalApps === 1 ? 'App' : 'Apps'} Found` : `All Apps (${totalApps})`}
              </Typography>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 2xl:grid-cols-12 gap-2 pt-2">
                {paginatedApps.map((app) => (
                  <MarketplaceAppCard key={app.id} app={app} onImport={handleImportApp} isImported={importedAppIds.has(app.id)} />
                ))}
              </div>
            </section>
          )}

          {/* Empty State */}
          {!isLoading && totalApps === 0 && !searchQuery && !selectedCategory && (
            <EmptyState
              icon={Package}
              title="No apps available"
              message="Sync a repository to get started"
            />
          )}

          {!isLoading && totalApps === 0 && (searchQuery || selectedCategory) && (
            <div className="text-center py-8 bg-muted rounded-lg border border-border">
              <Typography variant="small" muted>No apps found matching your criteria</Typography>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          )}

          {/* Error */}
          {error && (
            <Alert variant="danger" title="Error">
              {error}
            </Alert>
          )}
        </div>
      )}

      {/* Manage Repos Tab */}
      {activeTab === 'repos' && (
        <div className="flex-1 overflow-auto">
          <RepoManager />
        </div>
      )}

      {/* Pagination - Fixed at bottom */}
      {activeTab === 'browse' && totalPages > 0 && (
        <div className="shrink-0 mt-auto">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}
    </div>
  )
}
