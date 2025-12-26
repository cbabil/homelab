/**
 * Applications Page Component
 * 
 * Modern app marketplace with search, filters, and installation management.
 */

import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { App } from '@/types/app'
import { AppCard } from '@/components/applications/AppCard'
import { ApplicationFormDialog } from '@/components/applications/ApplicationFormDialog'
import { useApplications } from '@/hooks/useApplications'
import { ApplicationsPageHeader } from './ApplicationsPageHeader'
import { ApplicationsSearchAndFilter } from './ApplicationsSearchAndFilter'
import { ApplicationsEmptyState } from './ApplicationsEmptyState'

export function ApplicationsPage() {
  const [searchParams] = useSearchParams()
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const {
    apps,
    categories,
    filter,
    setFilter,
    updateFilter,
    addApplication,
    isLoading,
    error
  } = useApplications()

  // Read URL parameters and update filter
  useEffect(() => {
    const categoryParam = searchParams.get('category') || undefined
    updateFilter({ category: categoryParam })
  }, [searchParams, updateFilter])

  const handleSearch = (value: string) => {
    updateFilter({ search: value })
  }

  const handleAddApp = () => {
    setIsAddDialogOpen(true)
  }

  const handleSaveApp = async (appData: Partial<App>) => {
    try {
      await addApplication(appData)
      setIsAddDialogOpen(false)
    } catch (error) {
      console.error('Failed to add application:', error)
    }
  }

  return (
    <div className="space-y-4">
      {/* Ultra-compact header with inline Add App button */}
      <div className="space-y-2">
        <ApplicationsPageHeader onAddApp={handleAddApp} />

        {/* Ultra-compact search and filters in single line */}
        <ApplicationsSearchAndFilter 
          filter={filter}
          onFilterChange={setFilter}
          onSearch={handleSearch}
          categories={categories}
        />
      </div>

      {/* Ultra-compact grid with minimal gaps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
        {apps.map((app) => (
          <AppCard key={app.id} app={app} />
        ))}
      </div>

      {!isLoading && apps.length === 0 && <ApplicationsEmptyState />}

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      <ApplicationFormDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        onSave={handleSaveApp}
        categories={categories}
        title="Add Custom Application"
      />
    </div>
  )
}
