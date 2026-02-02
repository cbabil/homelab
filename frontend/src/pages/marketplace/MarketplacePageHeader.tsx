/**
 * Marketplace Page Header Components
 *
 * Extracted header action components for the Marketplace page.
 */

import { Filter, Plus, RefreshCw } from 'lucide-react'
import { Box, Typography, Divider, Paper } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { SearchInput } from '@/components/ui/SearchInput'

interface FilterOption {
  label: string
  value: string
}

interface MarketplaceFiltersDropdownProps {
  showFilters: boolean
  showTrending: boolean
  selectedRepoId: string | undefined
  selectedCategory: string | undefined
  repoOptions: FilterOption[]
  categoryOptions: FilterOption[]
  onTrendingFilter: () => void
  onRepoChange: (repoId: string | undefined) => void
  onCategoryChange: (categoryId: string | undefined) => void
}

export function MarketplaceFiltersDropdown({
  showFilters,
  showTrending,
  selectedRepoId,
  selectedCategory,
  repoOptions,
  categoryOptions,
  onTrendingFilter,
  onRepoChange,
  onCategoryChange
}: MarketplaceFiltersDropdownProps) {
  const { t } = useTranslation()

  if (!showFilters) return null

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        right: 0,
        top: '100%',
        mt: 0.5,
        zIndex: 20,
        p: 1,
        minWidth: 200
      }}
    >
      <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1, px: 1, display: 'block' }}>
        {t('common.filter')}
      </Typography>
      <Button
        fullWidth
        onClick={onTrendingFilter}
        sx={{
          justifyContent: 'flex-start',
          px: 1,
          py: 0.75,
          fontSize: '0.875rem',
          textTransform: 'none',
          bgcolor: showTrending ? 'primary.light' : 'transparent',
          color: showTrending ? 'primary.main' : 'text.primary',
          '&:hover': {
            bgcolor: showTrending ? 'primary.light' : 'action.hover'
          }
        }}
      >
        {t('marketplace.trending')}
      </Button>
      <Divider sx={{ my: 1 }} />
      <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1, px: 1, display: 'block' }}>
        {t('marketplace.filters.source')}
      </Typography>
      {repoOptions.map((opt) => (
        <Button
          key={opt.value}
          fullWidth
          onClick={() => onRepoChange(opt.value || undefined)}
          sx={{
            justifyContent: 'flex-start',
            px: 1,
            py: 0.75,
            fontSize: '0.875rem',
            textTransform: 'none',
            bgcolor: !showTrending && (selectedRepoId === opt.value || (!selectedRepoId && !opt.value)) ? 'primary.light' : 'transparent',
            color: !showTrending && (selectedRepoId === opt.value || (!selectedRepoId && !opt.value)) ? 'primary.main' : 'text.primary',
            '&:hover': {
              bgcolor: !showTrending && (selectedRepoId === opt.value || (!selectedRepoId && !opt.value)) ? 'primary.light' : 'action.hover'
            }
          }}
        >
          {opt.label}
        </Button>
      ))}
      <Divider sx={{ my: 1 }} />
      <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1, px: 1, display: 'block' }}>
        {t('marketplace.category')}
      </Typography>
      {categoryOptions.map((opt) => (
        <Button
          key={opt.value}
          fullWidth
          onClick={() => onCategoryChange(opt.value || undefined)}
          sx={{
            justifyContent: 'flex-start',
            px: 1,
            py: 0.75,
            fontSize: '0.875rem',
            textTransform: 'none',
            bgcolor: !showTrending && (selectedCategory === opt.value || (!selectedCategory && !opt.value)) ? 'primary.light' : 'transparent',
            color: !showTrending && (selectedCategory === opt.value || (!selectedCategory && !opt.value)) ? 'primary.main' : 'text.primary',
            '&:hover': {
              bgcolor: !showTrending && (selectedCategory === opt.value || (!selectedCategory && !opt.value)) ? 'primary.light' : 'action.hover'
            }
          }}
        >
          {opt.label}
        </Button>
      ))}
    </Paper>
  )
}

interface BrowseTabActionsProps {
  searchQuery: string
  onSearchChange: (value: string) => void
  showFilters: boolean
  onToggleFilters: () => void
  showTrending: boolean
  selectedRepoId: string | undefined
  selectedCategory: string | undefined
  repoOptions: FilterOption[]
  categoryOptions: FilterOption[]
  onTrendingFilter: () => void
  onRepoChange: (repoId: string | undefined) => void
  onCategoryChange: (categoryId: string | undefined) => void
}

export function BrowseTabActions({
  searchQuery,
  onSearchChange,
  showFilters,
  onToggleFilters,
  showTrending,
  selectedRepoId,
  selectedCategory,
  repoOptions,
  categoryOptions,
  onTrendingFilter,
  onRepoChange,
  onCategoryChange
}: BrowseTabActionsProps) {
  const { t } = useTranslation()

  return (
    <>
      <SearchInput
        value={searchQuery}
        onChange={onSearchChange}
        placeholder={t('marketplace.searchApps')}
      />
      <Box sx={{ position: 'relative' }}>
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleFilters}
          leftIcon={<Filter style={{ width: 12, height: 12 }} />}
          sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
        >
          {t('common.filter')}
        </Button>
        <MarketplaceFiltersDropdown
          showFilters={showFilters}
          showTrending={showTrending}
          selectedRepoId={selectedRepoId}
          selectedCategory={selectedCategory}
          repoOptions={repoOptions}
          categoryOptions={categoryOptions}
          onTrendingFilter={onTrendingFilter}
          onRepoChange={onRepoChange}
          onCategoryChange={onCategoryChange}
        />
      </Box>
    </>
  )
}

interface ReposTabActionsProps {
  searchQuery: string
  onSearchChange: (value: string) => void
  isLoading: boolean
  onRefresh: () => void
  onAddRepo: () => void
}

export function ReposTabActions({
  searchQuery,
  onSearchChange,
  isLoading,
  onRefresh,
  onAddRepo
}: ReposTabActionsProps) {
  const { t } = useTranslation()

  return (
    <>
      <SearchInput
        value={searchQuery}
        onChange={onSearchChange}
        placeholder={t('marketplace.searchRepos')}
      />
      <Button
        variant="outline"
        size="sm"
        onClick={onRefresh}
        disabled={isLoading}
        leftIcon={<RefreshCw style={{ width: 12, height: 12 }} className={isLoading ? 'animate-spin' : ''} />}
        sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
      >
        {t('common.refresh')}
      </Button>
      <Button
        variant="primary"
        size="sm"
        onClick={onAddRepo}
        leftIcon={<Plus style={{ width: 12, height: 12 }} />}
        sx={{ fontSize: '0.7rem', py: 0.25, px: 1.5, minHeight: 26 }}
      >
        {t('common.add')}
      </Button>
    </>
  )
}
