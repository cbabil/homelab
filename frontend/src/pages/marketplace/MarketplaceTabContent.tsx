/**
 * Marketplace Tab Content Components
 *
 * Extracted tab content components for the Marketplace page.
 */

import { RefObject } from 'react'
import { Box, CircularProgress, Alert } from '@mui/material'
import { TablePagination } from '@/components/ui/TablePagination'
import { MarketplaceAppsTable } from './MarketplaceAppsTable'
import { RepoManager, RepoManagerRef } from './RepoManager'
import type { MarketplaceApp } from '@/types/marketplace'

interface BrowseTabContentProps {
  containerRef: RefObject<HTMLDivElement | null>
  isLoading: boolean
  error: string | null
  apps: MarketplaceApp[]
  onDeploy: (app: MarketplaceApp) => void
  repoMap: Map<string, string>
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function BrowseTabContent({
  containerRef,
  isLoading,
  error,
  apps,
  onDeploy,
  repoMap,
  currentPage,
  totalPages,
  onPageChange
}: BrowseTabContentProps) {
  return (
    <>
      <Box ref={containerRef} sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress size={24} />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <MarketplaceAppsTable
            apps={apps}
            onDeploy={onDeploy}
            repoMap={repoMap}
          />
        )}
      </Box>
      <TablePagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />
    </>
  )
}

interface ReposTabContentProps {
  repoManagerRef: RefObject<RepoManagerRef | null>
  searchQuery: string
  isAddModalOpen: boolean
  onAddModalClose: () => void
}

export function ReposTabContent({
  repoManagerRef,
  searchQuery,
  isAddModalOpen,
  onAddModalClose
}: ReposTabContentProps) {
  return (
    <Box sx={{ flex: 1, overflow: 'auto' }}>
      <RepoManager
        ref={repoManagerRef}
        searchQuery={searchQuery}
        isAddModalOpen={isAddModalOpen}
        onAddModalClose={onAddModalClose}
      />
    </Box>
  )
}
