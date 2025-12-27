/**
 * Marketplace Page Component
 *
 * Browse and manage marketplace repositories and applications.
 * Features tab navigation, search, filtering, and showcases featured/trending apps.
 */

import { useEffect, useState } from 'react'
import { Search } from 'lucide-react'
import type { MarketplaceApp, MarketplaceCategory, SearchFilters } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { RepoManager } from './RepoManager'
import { MarketplaceAppCard } from './MarketplaceAppCard'

type TabType = 'browse' | 'repos'

export function MarketplacePage() {
  const [activeTab, setActiveTab] = useState<TabType>('browse')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [categories, setCategories] = useState<MarketplaceCategory[]>([])
  const [featuredApps, setFeaturedApps] = useState<MarketplaceApp[]>([])
  const [trendingApps, setTrendingApps] = useState<MarketplaceApp[]>([])
  const [searchResults, setSearchResults] = useState<MarketplaceApp[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load initial data
  useEffect(() => {
    loadInitialData()
  }, [])

  // Search when filters change
  useEffect(() => {
    if (activeTab === 'browse') {
      performSearch()
    }
  }, [searchQuery, selectedCategory, activeTab])

  const loadInitialData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Load categories, featured, and trending apps in parallel
      const [categoriesData, featuredData, trendingData] = await Promise.all([
        marketplaceService.getCategories(),
        marketplaceService.getFeaturedApps(6),
        marketplaceService.getTrendingApps(6)
      ])

      setCategories(categoriesData)
      setFeaturedApps(featuredData)
      setTrendingApps(trendingData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load marketplace data')
      console.error('Failed to load marketplace data:', err)
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
      console.error('Failed to search apps:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
  }

  const handleCategoryChange = (categoryId: string | undefined) => {
    setSelectedCategory(categoryId)
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Marketplace</h1>
          <p className="text-sm text-gray-600">Discover and install applications</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('browse')}
            className={`
              py-2 px-1 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'browse'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            Browse Apps
          </button>
          <button
            onClick={() => setActiveTab('repos')}
            className={`
              py-2 px-1 border-b-2 font-medium text-sm transition-colors
              ${activeTab === 'repos'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            Manage Repos
          </button>
        </nav>
      </div>

      {/* Browse Apps Tab */}
      {activeTab === 'browse' && (
        <div className="space-y-6">
          {/* Search and Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search Input */}
            <div className="flex-1 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search apps..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory || ''}
              onChange={(e) => handleCategoryChange(e.target.value || undefined)}
              className="block px-3 py-2 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name} ({category.count})
                </option>
              ))}
            </select>
          </div>

          {/* Featured Apps Section */}
          {featuredApps.length > 0 && !searchQuery && !selectedCategory && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-900">Featured Apps</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
                {featuredApps.map((app) => (
                  <MarketplaceAppCard key={app.id} app={app} />
                ))}
              </div>
            </div>
          )}

          {/* Trending Apps Section */}
          {trendingApps.length > 0 && !searchQuery && !selectedCategory && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-900">Trending Apps</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
                {trendingApps.map((app) => (
                  <MarketplaceAppCard key={app.id} app={app} />
                ))}
              </div>
            </div>
          )}

          {/* Search Results */}
          {(searchQuery || selectedCategory) && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-900">
                {searchResults.length} {searchResults.length === 1 ? 'App' : 'Apps'} Found
              </h2>
              {searchResults.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
                  {searchResults.map((app) => (
                    <MarketplaceAppCard key={app.id} app={app} />
                  ))}
                </div>
              ) : (
                !isLoading && (
                  <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-600">No apps found matching your criteria</p>
                  </div>
                )
              )}
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Manage Repos Tab */}
      {activeTab === 'repos' && (
        <RepoManager />
      )}
    </div>
  )
}
