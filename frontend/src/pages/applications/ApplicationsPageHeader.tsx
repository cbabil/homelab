/**
 * Applications Page Header Component
 *
 * Header section with title, description, and Add App button for the Applications page.
 */

import { Plus } from 'lucide-react'
import { Button, Typography } from 'ui-toolkit'

interface ApplicationsPageHeaderProps {
  onAddApp: () => void
}

export function ApplicationsPageHeader({ onAddApp }: ApplicationsPageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1 min-w-0">
        <Typography variant="h2">Applications</Typography>
        <Typography variant="small" muted className="truncate">
          Discover and deploy applications for your homelab infrastructure.
        </Typography>
      </div>

      <Button
        onClick={onAddApp}
        variant="primary"
        size="sm"
        leftIcon={<Plus size={14} />}
        className="shrink-0 ml-3"
      >
        Add App
      </Button>
    </div>
  )
}