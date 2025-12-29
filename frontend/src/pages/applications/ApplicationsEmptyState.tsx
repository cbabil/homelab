/**
 * Applications Empty State Component
 *
 * Empty state displayed when no applications match the current filters.
 */

import { Search } from 'lucide-react'
import { EmptyState } from 'ui-toolkit'

export function ApplicationsEmptyState() {
  return (
    <EmptyState
      icon={Search}
      title="No applications found"
      message="Try adjusting your search terms or filters."
    />
  )
}