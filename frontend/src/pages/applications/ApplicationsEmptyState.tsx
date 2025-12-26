/**
 * Applications Empty State Component
 * 
 * Empty state displayed when no applications match the current filters.
 */

import { Search } from 'lucide-react'

export function ApplicationsEmptyState() {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 mx-auto rounded-full bg-muted flex items-center justify-center mb-4">
        <Search className="w-8 h-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">No applications found</h3>
      <p className="text-muted-foreground">
        Try adjusting your search terms or filters.
      </p>
    </div>
  )
}