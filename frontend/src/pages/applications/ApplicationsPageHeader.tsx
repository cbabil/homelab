/**
 * Applications Page Header Component
 *
 * Header section with title, description, and Add App button for the Applications page.
 */

import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface ApplicationsPageHeaderProps {
  onAddApp: () => void
}

export function ApplicationsPageHeader({ onAddApp }: ApplicationsPageHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex-1 min-w-0">
        <h1 className="text-xl font-bold tracking-tight">Application Marketplace</h1>
        <p className="text-muted-foreground text-xs truncate">
          Discover and install applications for your homelab infrastructure.
        </p>
      </div>

      <Button
        onClick={onAddApp}
        variant="primary"
        size="sm"
        leftIcon={<Plus className="h-3.5 w-3.5" />}
        className="shrink-0 ml-3"
      >
        Add App
      </Button>
    </div>
  )
}