/**
 * Marketplace Page Component
 *
 * Browse and manage marketplace repositories and applications.
 * Features tab navigation, search, filtering, and showcases featured/trending apps.
 */

import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { Tabs, Tab, Box } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { PageHeader } from '@/components/layout/PageHeader'
import { useToast } from '@/components/ui/Toast'
import type { MarketplaceApp, MarketplaceCategory, MarketplaceRepo, SearchFilters } from '@/types/marketplace'
import * as marketplaceService from '@/services/marketplaceService'
import { RepoManagerRef } from './RepoManager'
import { BrowseTabActions, ReposTabActions } from './MarketplacePageHeader'
import { BrowseTabContent, ReposTabContent } from './MarketplaceTabContent'
import { marketplaceLogger } from '@/services/systemLogger'
import { useAuth } from '@/providers/AuthProvider'
import { useServers } from '@/hooks/useServers'
import { useDeploymentModal } from '@/hooks/useDeploymentModal'
import { DeploymentModal } from '@/components/deployment/DeploymentModal'
import { useDynamicRowCount } from '@/hooks/useDynamicRowCount'

type TabType = 'browse' | 'repos'

export function MarketplacePage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('browse')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()
  const [selectedRepoId, setSelectedRepoId] = useState<string | undefined>()
  const [showTrending, setShowTrending] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [categories, setCategories] = useState<MarketplaceCategory[]>([])
  const [repos, setRepos] = useState<MarketplaceRepo[]>([])
  const [trendingApps, setTrendingApps] = useState<MarketplaceApp[]>([])
  const [allApps, setAllApps] = useState<MarketplaceApp[]>([])
  const [searchResults, setSearchResults] = useState<MarketplaceApp[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const { addToast } = useToast()
  const { user } = useAuth()

  // Repo manager state
  const repoManagerRef = useRef<RepoManagerRef>(null)
  const [repoSearchQuery, setRepoSearchQuery] = useState('')
  const [isRepoLoading, setIsRepoLoading] = useState(false)

  // Table container ref for dynamic row calculation (same settings as AuditLogsPage)
  const containerRef = useRef<HTMLDivElement>(null)
  const itemsPerPage = useDynamicRowCount(containerRef, {
    rowHeight: 32,
    headerHeight: 40,
    paginationHeight: 0
  })

  const [isAddRepoModalOpen, setIsAddRepoModalOpen] = useState(false)

  const tabItems = [
    { label: t('marketplace.tabs.browseApps'), value: 'browse' },
    { label: t('marketplace.tabs.manageRepos'), value: 'repos' }
  ]

  // Server and deployment state
  const { servers } = useServers()
  const deploymentModal = useDeploymentModal()

  // Handle deploy from marketplace
  const handleDeployApp = useCallback((app: MarketplaceApp) => {
    if (!user) {
      addToast({ type: 'error', title: t('marketplace.errors.loginRequired') })
      return
    }
    marketplaceLogger.info(`Opening deployment modal for: ${app.name}`)
    deploymentModal.openModalForMarketplace(app)
  }, [user, addToast, deploymentModal, t])

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
  }, [searchQuery, selectedCategory, selectedRepoId, activeTab])

  // Reset page when search/filter/items per page changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, selectedCategory, selectedRepoId, showTrending, itemsPerPage])

  const loadInitialData = async () => {
    setIsLoading(true)
    setError(null)
    marketplaceLogger.info('Loading marketplace data')

    try {
      const [categoriesData, trendingData, allAppsData, reposData] = await Promise.all([
        marketplaceService.getCategories(),
        marketplaceService.getTrendingApps(50),
        marketplaceService.searchApps({ sortBy: 'name' }),
        marketplaceService.getRepos()
      ])

      setCategories(categoriesData)
      setTrendingApps(trendingData)
      setAllApps(allAppsData.apps)
      setRepos(reposData)
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
        repoId: selectedRepoId,
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
    if (value) {
      setShowTrending(false)
    }
  }

  const handleCategoryChange = (categoryId: string | undefined) => {
    setSelectedCategory(categoryId)
    setShowTrending(false)
    setShowFilters(false)
  }

  const handleRepoChange = (repoId: string | undefined) => {
    setSelectedRepoId(repoId)
    setShowTrending(false)
    setShowFilters(false)
  }

  const handleTrendingFilter = () => {
    setShowTrending(!showTrending)
    setSelectedCategory(undefined)
    setShowFilters(false)
  }

  // Create a map of repoId -> repoName for display
  const repoMap = useMemo(() => {
    const map = new Map<string, string>()
    repos.forEach(repo => map.set(repo.id, repo.name))
    return map
  }, [repos])

  // Determine which apps to display
  const displayApps = showTrending ? trendingApps : (searchQuery || selectedCategory || selectedRepoId) ? searchResults : allApps
  const totalApps = displayApps.length
  const totalPages = Math.ceil(totalApps / itemsPerPage)

  // Paginated apps
  const paginatedApps = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage
    return displayApps.slice(start, start + itemsPerPage)
  }, [displayApps, currentPage])

  // Build dropdown options from categories
  const categoryOptions = useMemo(() => [
    { label: t('marketplace.allCategories'), value: '' },
    ...categories.map((cat) => ({
      label: `${cat.name} (${cat.count})`,
      value: cat.id
    }))
  ], [categories, t])

  // Build dropdown options from repos
  const repoOptions = useMemo(() => [
    { label: t('marketplace.filters.allSources'), value: '' },
    ...repos.filter(r => r.enabled).map((repo) => ({
      label: `${repo.name} (${repo.appCount})`,
      value: repo.id
    }))
  ], [repos, t])

  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* Header - same structure as AuditLogsHeader */}
      <PageHeader
        title={t('marketplace.title')}
        subtitle={t('marketplace.subtitle')}
        actions={activeTab === 'browse' ? (
          <BrowseTabActions
            searchQuery={searchQuery}
            onSearchChange={handleSearchChange}
            showFilters={showFilters}
            onToggleFilters={() => setShowFilters(!showFilters)}
            showTrending={showTrending}
            selectedRepoId={selectedRepoId}
            selectedCategory={selectedCategory}
            repoOptions={repoOptions}
            categoryOptions={categoryOptions}
            onTrendingFilter={handleTrendingFilter}
            onRepoChange={handleRepoChange}
            onCategoryChange={handleCategoryChange}
          />
        ) : activeTab === 'repos' ? (
          <ReposTabActions
            searchQuery={repoSearchQuery}
            onSearchChange={setRepoSearchQuery}
            isLoading={isRepoLoading}
            onRefresh={() => {
              setIsRepoLoading(true)
              repoManagerRef.current?.refresh().finally(() => setIsRepoLoading(false))
            }}
            onAddRepo={() => setIsAddRepoModalOpen(true)}
          />
        ) : undefined}
      />

      {/* Tab Navigation - same structure as AuditLogsPage */}
      <Box sx={{ mt: 3, mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_e, value) => setActiveTab(value as TabType)}
          sx={{ minHeight: 36 }}
        >
          {tabItems.map((item) => (
            <Tab key={item.value} label={item.label} value={item.value} sx={{ minHeight: 36, py: 1 }} />
          ))}
        </Tabs>
      </Box>

      {/* Browse Apps Tab - Main Content Area */}
      {activeTab === 'browse' && (
        <BrowseTabContent
          containerRef={containerRef}
          isLoading={isLoading}
          error={error}
          apps={paginatedApps}
          onDeploy={handleDeployApp}
          repoMap={repoMap}
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}

      {/* Manage Repos Tab */}
      {activeTab === 'repos' && (
        <ReposTabContent
          repoManagerRef={repoManagerRef}
          searchQuery={repoSearchQuery}
          isAddModalOpen={isAddRepoModalOpen}
          onAddModalClose={() => setIsAddRepoModalOpen(false)}
        />
      )}

      {/* Deployment Modal */}
      <DeploymentModal
        isOpen={deploymentModal.isOpen}
        onClose={deploymentModal.closeModal}
        app={deploymentModal.selectedApp}
        servers={servers}
        step={deploymentModal.step}
        setStep={deploymentModal.setStep}
        selectedServerIds={deploymentModal.selectedServerIds}
        setSelectedServerIds={deploymentModal.setSelectedServerIds}
        isDeploying={deploymentModal.isDeploying}
        error={deploymentModal.error}
        deploymentResult={deploymentModal.deploymentResult}
        onDeploy={() => deploymentModal.deploy(servers)}
        onRetry={() => deploymentModal.retryDeployment(servers)}
        onCleanup={deploymentModal.cleanup}
        installationStatus={deploymentModal.installationStatus}
        targetServerStatuses={deploymentModal.targetServerStatuses}
      />
    </Box>
  )
}
